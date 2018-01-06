# -*- coding: utf-8 -*-
import scrapy

from scrapy.http import Request
from scrapy_splash import SplashRequest

from hotel_spider.items import ProductItem

class CtripSpider(scrapy.Spider):
    name = 'ctrip'
    start_urls = ['http://hotels.ctrip.com/domestic-city-hotel.html']

    def parse(self, response):
        for city in response.css('.pinyin_filter_detail dd a'):
            city_name = city.css('a::text').extract_first()
            city_url = city.css('a::attr(href)').extract_first()

            # Get max_page number
            script = """
            function wait_for_element(splash, ele_selector)
                while true do
                    local ele = splash:select(ele_selector)
                    if ele then
                        break
                    end
                    splash:wait(0.5)
                end
            end
            function main(splash, args)
                local url = args.url
                assert(splash:go(url))
                splash:wait(5)
                wait_for_element(splash, 'div.c_page_list')
                local page_links = splash:select_all('.c_page_list a')
                local max_page = 0
                for _, page_link in ipairs(page_links) do
                    local page = tonumber(page_link:text())
                    if page > max_page then
                        max_page = page
                    end
                end
                return { max_page=max_page }
            end
            """
            url = 'http://hotels.ctrip.com' + city_url
            request = SplashRequest(callback=self.parse_after_max_page, endpoint='/execute',
                                    args={
                                        'lua_source': script,
                                        'url': url,
                                        'images': 0,
                                        'headers': {
                                            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36'
                                        }
                                    })
            request.meta['city'] = city_name
            yield request

    def parse_after_max_page(self, response):
        max_page = response.data['max_page']
        base_url = response.url
        for page in range(1, max_page + 1):
            script = """
            function wait_for_element(splash, ele_selector)
                while true do
                    local ele = splash:select(ele_selector)
                    if ele then
                        break
                    end
                    splash:wait(0.5)
                end
            end
            function main(splash, args)
                local url = args.url
                assert(splash:go(url))
                wait_for_element(splash, '.hotel_item')
                return splash:html()
            end
            """
            paged_url = base_url + '/p' + str(page)
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
        for hotel in response.css('.hotel_item'):
            hotel_name = hotel.css('.hotel_name a::text').extract_first()
            hotel_url = hotel.css('.hotel_name a::attr(href)').extract_first()
            hotel_url = 'http://hotels.ctrip.com' + hotel_url
            address = hotel.css('.hotel_item_htladdress::text').extract_first()

            script = """
            function wait_for_element(splash, ele_selector)
                while true do
                    local ele = splash:select(ele_selector)
                    if ele then
                        break
                    end
                    splash:wait(0.5)
                end
            end
            function main(splash, args)
                local url = args.url
                assert(splash:go(url))
                wait_for_element(splash, 'table#J_RoomListTbl tr[expand]')
                return splash:html()
            end
            """

            request = SplashRequest(endpoint='/execute', callback=self.parse_hotel_page,
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
            request.meta['address'] = address
            request.meta['hotel_name'] = hotel_name
            request.meta['hotel_url'] = hotel_url
            yield request

    def parse_hotel_page(self, response):
        source = 'ctrip'
        country = 'cn'
        meta = response.meta
        city = meta['city']
        address = meta['address']
        hotel_name = meta['hotel_name']
        hotel_url = meta['hotel_url']

        latitude = response.css('meta[itemprop="latitude"]::attr(content)').extract_first()
        longitude = response.css('meta[itemprop="longitude"]::attr(content)').extract_first()

        rooms = response.css('table#J_RoomListTbl tr[expand]')
        room_name = None
        for room in rooms:
            _room_name = room.css('a.room_unfold::text').extract_first()
            if _room_name:
                room_name = _room_name.strip()

            product_name = room.css('.room_type_name::text').extract_first()
            product_price = room.css('.base_price::text').extract_first()

            item = ProductItem()
            item['source'] = source
            item['country'] = country
            item['city'] = city
            item['address'] = address
            item['latitude'] = latitude
            item['longitude'] = longitude
            item['hotel_name'] = hotel_name
            item['hotel_url'] = hotel_url
            item['room_name'] = room_name
            item['product_name'] = product_name
            item['product_price'] = product_price
            yield item
