# -*- coding: utf-8 -*-
import scrapy

from scrapy.http import Request
from scrapy_splash import SplashRequest
from scrapy_splash import SlotPolicy

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
        request = Request(url='http://hotel.meituan.com', cookies=cookies, callback=self.parse_city_redirect, dont_filter=True)
        request.meta['city'] = response.meta['city']
        yield request

    def parse_city_redirect(self, response):
        request = Request(url=response.url, callback=self.parse_city_page)
        request.meta['city'] = response.meta['city']
        yield request

    def parse_city_page(self, response):
        for hotel in response.css('.poi-title')[:10]:
            url = hotel.css('a::attr(href)').extract_first()
            request = SplashRequest(url=url, callback=self.parse_hotel_rooms,
                                args={
                                    'wait': 3,
                                    'timeout': 20,
                                    'headers': {
                                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36'
                                    }
                                },
                                slot_policy=SlotPolicy.SINGLE_SLOT
                                )
            request.meta['city'] = response.meta['city']
            request.meta['raw_name'] = hotel.css('a::text').extract_first().strip()
            request.meta['hotel_url'] = url
            yield request

    def parse_hotel_rooms(self, response):
        source = 'meituan'
        country = 'cn'
        city = response.meta['city']
        raw_name = response.meta['raw_name']
        hotel_url = response.meta['hotel_url']

        for room in response.css('.deal-item'):
            room_name = room.css('.mb15.deal-cellname::text').extract_first().strip()
            for product in room.css('tr.goods'):
                product_name = product.css('span.deal-cellname::text').extract_first().strip()
                product_price = product.css('em.price-number::text').extract_first().strip()

                product_item = ProductItem()
                product_item['source'] = source
                product_item['country'] = country
                product_item['city'] = city
                product_item['raw_name'] = raw_name
                product_item['hotel_url'] = hotel_url
                product_item['room_name'] = room_name
                product_item['product_name'] = product_name
                product_item['product_price'] = product_price
                yield product_item
