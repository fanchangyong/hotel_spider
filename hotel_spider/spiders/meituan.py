# -*- coding: utf-8 -*-
import scrapy

from scrapy.http import Request
from scrapy_splash import SplashRequest

from hotel_spider.items import ProductItem
from hotel_spider.utils import cookie_to_dict

class MeituancitiesSpider(scrapy.Spider):
    name = 'meituan'
    start_urls = ['http://www.meituan.com/changecity/']

    def parse(self, response):
        for city in response.css('.cities .city')[:1]:
            url = city.css('a::attr(href)').extract_first()
            city_name = city.css('::text').extract_first()
            request = Request(url='http:' + url, callback=self.parse_after_change_city)
            request.meta['city'] = city_name
            yield request

    def parse_after_change_city(self, response):
        cookies = cookie_to_dict(response.headers.getlist('Set-Cookie')[0].decode('utf-8'))
        request = Request(url='http://hotel.meituan.com', cookies=cookies, callback=self.parse_before_max_page, dont_filter=True)
        request.meta['city'] = response.meta['city']
        yield request

    def parse_before_max_page(self, response):
        script = """
        function wait_for_element(splash, ele_selector)
            while true do
                local ele = splash:select(ele_selector)
                if ele then
                    break
                end
                splash:wait(0.05)
            end
        end

        function main(splash, args)
            local url = args.url
            assert(splash:go(url))
            wait_for_element(splash, 'li.page-link')
            local page_links = splash:select_all('li.page-link')
            local max_page = 0
            for _, link in ipairs(page_links) do
                local page = tonumber(link:text())
                if page > max_page then
                    max_page = page
                end
            end
            return { max_page=max_page }
        end
        """
        url = response.url
        request = SplashRequest(callback=self.parse_after_max_page, endpoint='/execute',
                                args={
                                    'lua_source': script,
                                    'url': url,
                                    'images': 0,
                                    'headers': {
                                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36'
                                    }
                                })
        request.meta['city'] = response.meta['city']
        yield request

    def parse_after_max_page(self, response):
        max_page = response.data['max_page']
        base_url = response.url
        for page in range(1, max_page + 1):
            script = """
            function main(splash, args)
                local url = args.url
                assert(splash:go(url))

                function wait_for_element(ele_selector)
                    while true do
                        local ele = splash:select(ele_selector)
                        if ele then
                            break
                        end
                        splash:wait(0.05)
                    end
                end
                wait_for_element('article.poi-item')
                return splash:html()
            end
            """
            paged_url = base_url + 'pn' + str(page)
            request = SplashRequest(endpoint='/execute', callback=self.parse_hotel_list_page,
                                    args={
                                        'url': paged_url,
                                        'lua_source': script,
                                        'images': 0,
                                        'headers': {
                                            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36'
                                        }
                                    })
            request.meta['city'] = response.meta['city']
            yield request

    def parse_hotel_list_page(self, response):
        script = """
        function main(splash, args)
            local url = args.url
            assert(splash:go(url))

            function wait_for_element(ele_selector)
                while true do
                    local ele = splash:select(ele_selector)
                    if ele then
                        break
                    end
                    splash:wait(0.05)
                end
            end
            wait_for_element('.deal-item')
            return splash:html()
        end
        """
        print('酒店数量: ', len(response.css('article.poi-item')), ', url: ', response.url)
        for hotel in response.css('article.poi-item'):
            hotel_url = hotel.css('a.poi-title::attr(href)').extract_first()
            request = SplashRequest(endpoint='/execute', callback=self.parse_hotel_rooms,
                                args={
                                    'url': hotel_url,
                                    'lua_source': script,
                                    'timeout': 20,
                                    'images': 0,
                                    'headers': {
                                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36'
                                    }
                                })
            request.meta['city'] = response.meta['city']
            request.meta['hotel_name'] = hotel.css('a.poi-title::text').extract_first().strip()
            request.meta['address'] = hotel.css('div.poi-address::text').extract_first().strip()
            request.meta['hotel_url'] = hotel_url
            yield request

    def parse_hotel_rooms(self, response):
        source = 'meituan'
        country = 'cn'
        city = response.meta['city']
        address = response.meta['address']
        hotel_name = response.meta['hotel_name']
        hotel_url = response.meta['hotel_url']
        print('房间数量: ', len(response.css('.deal-item')), ', url: ', hotel_url)

        for room in response.css('.deal-item'):
            room_name = room.css('.mb15.deal-cellname::text').extract_first().strip()
            for product in room.css('tr.goods'):
                product_name = product.css('span.deal-cellname::text').extract_first().strip()
                product_price = product.css('em.price-number::text').extract_first().strip()

                product_item = ProductItem()
                product_item['source'] = source
                product_item['country'] = country
                product_item['city'] = city
                product_item['address'] = address
                product_item['hotel_name'] = hotel_name
                product_item['hotel_url'] = hotel_url
                product_item['room_name'] = room_name
                product_item['product_name'] = product_name
                product_item['product_price'] = product_price
                yield product_item
