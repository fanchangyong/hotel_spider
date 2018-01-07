# -*- coding: utf-8 -*-
import scrapy
import pymysql
import json
import re
import math

from scrapy.http import Request
from scrapy_splash import SplashRequest

from hotel_spider import settings
from hotel_spider.items import ProductItem

class ExpediaSpider(scrapy.Spider):
    name = 'expedia'

    def start_requests(self):
        ### 中国的地址从json读取
        locations = json.load(open('locations.json'))
        country_name = '中国'
        for i in range(len(locations)):
            province = locations[i]
            province_name = province['name']
            cities = province['child']
            for j in range(len(cities)):
                city = cities[j]
                city_name = city['name']
                if city_name != '深圳市':
                    continue
                districts = city['child']
                for k in range(len(districts)):
                    district = districts[k]
                    district_name = district['name']

                    request = self.request_pages_of_location(country_name, province_name, city_name, district_name)
                    yield request

        ### 国外的地址从mysql读取
        connect = pymysql.connect(
            host=settings.MYSQL_HOST,
            db=settings.MYSQL_DB,
            user=settings.MYSQL_USER,
            passwd=settings.MYSQL_PASSWD,
            charset='utf8',
            use_unicode=True
        )
        cursor = connect.cursor()
        cursor.execute('select country, city from cities')
        ret = cursor.fetchall()
        for r in ret:
            country_name = r[0]
            city_name = r[1]

            request = self.request_pages_of_location(country_name, '', city_name, '')
            yield request

    def request_pages_of_location(self, country_name, province_name, city_name, district_name):
        url = 'https://www.expedia.cn/Hotel-Search?destination=' + country_name + province_name + city_name + district_name
        script = """
        function wait_for_element(splash, ele_selector)
            local count = 0
            while true do
                if count > 20 then
                    break
                end
                local ele = splash:select(ele_selector)
                if ele then
                    break
                end
                count = count + 1
                splash:wait(1)
            end
        end

        function main(splash, args)
            local url = args.url
            splash:go(url)
            wait_for_element(splash, '.showing-results')
            return splash:html()
        end
        """
        request = SplashRequest(callback=self.parse_max_page, endpoint='/execute',
                                args={
                                    'lua_source': script,
                                    'url': url,
                                    'images': 0,
                                    'headers': {
                                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36'
                                    }
                                })
        request.meta['country'] = country_name
        request.meta['city'] = city_name
        request.meta['district'] = district_name
        return request

    def parse_max_page(self, response):
        result_str = response.css('.showing-results::text').extract_first()
        pattern = re.compile(r'共(.*)个')
        m = re.search(pattern, result_str)
        total = int(m.group(1).strip())
        pages = math.ceil(total / 20)
        for page in range(1, pages + 1):
            script = """
            function wait_for_element(splash, ele_selector)
                local count = 0
                while true do
                    if count > 20 then
                        break
                    end
                    local ele = splash:select(ele_selector)
                    if ele then
                        break
                    end
                    count = count + 1
                    splash:wait(1)
                end
            end

            function main(splash, args)
                local url = args.url
                splash:go(url)

                wait_for_element(splash, 'article.hotel.listing')
                return splash:html()
            end
            """
            paged_url = response.url + '&page=' + str(page)
            request = SplashRequest(endpoint='/execute', callback=self.parse_hotel_list_page,
                                    args={
                                        'url': paged_url,
                                        'lua_source': script,
                                        'images': 0,
                                        'headers': {
                                            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36'
                                        }
                                    })
            request.meta['country'] = response.meta['country']
            request.meta['city'] = response.meta['city']
            request.meta['district'] = response.meta['district']
            yield request

    def parse_hotel_list_page(self, response):
        for hotel in response.css('article.hotel.listing'):
            hotel_name = hotel.css('.hotelName::text').extract_first()
            hotel_url = hotel.css('a.flex-link::attr(href)').extract_first()
            script = """
            function wait_for_element(splash, ele_selector)
                local count = 0
                while true do
                    if count > 20 then
                        break
                    end
                    local ele = splash:select(ele_selector)
                    if ele then
                        break
                    end
                    count = count + 1
                    splash:wait(1)
                end
            end

            function main(splash, args)
                local url = args.url
                splash:go(url)

                -- wait_for_element(splash, 'tbody.room')
                return splash:html()
            end

            """

            request = SplashRequest(url=hotel_url, callback=self.parse_hotel_detail_page,
                                    args={
                                        'images': 0,
                                        'headers': {
                                            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36'
                                        }
                                    })
            meta = request.meta
            meta['country'] = response.meta['country']
            meta['city'] = response.meta['city']
            meta['district'] = response.meta['district']
            meta['hotel_name'] = hotel_name
            meta['hotel_url'] = hotel_url
            yield request

    def parse_hotel_detail_page(self, response):
        meta = response.meta
        source = 'expedia'
        country = meta['country']
        city = meta['city']
        district = meta['district']
        hotel_name = meta['hotel_name']
        hotel_url = meta['hotel_url']

        for room in response.css('tbody.room'):
            room_name = room.css('td.room-info .room-basic-info .room-name::text').extract_first()
            for product in room.css('td.avg-rate'):
                product_price = product.css('.room-price .room-price-value::text').extract_first()
                if product_price:
                    product_price = product_price.replace('￥', '')
                    product_price = product_price.strip()

                item = ProductItem()
                item['source'] = source
                item['country'] = country
                item['city'] = city
                item['district'] = district
                item['hotel_name'] = hotel_name
                item['hotel_url'] = hotel_url
                item['room_name'] = room_name
                item['product_name'] = 'expedia product'
                item['product_price'] = product_price
                yield item
