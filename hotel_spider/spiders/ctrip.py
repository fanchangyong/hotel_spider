# -*- coding: utf-8 -*-
import scrapy

from scrapy.http import Request
from scrapy_splash import SplashRequest

from hotel_spider.items import ProductItem

class CtripSpider(scrapy.Spider):
    name = 'ctrip'
    allowed_domains = ['ctrip.com']
    start_urls = ['http://hotels.ctrip.com/domestic-city-hotel.html']

    def parse(self, response):
        for city in response.css('.pinyin_filter_detail dd a'):
            city_name = city.css('a::text').extract_first()
            url = city.css('a::attr(href)').extract_first()
            request = Request(url='http://hotels.ctrip.com' + url, callback=self.parse_city_hotels)
            request.meta['city'] = city_name
            yield request

    def parse_city_hotels(self, response):
        for hotel in response.css('.hotel_item'):
            hotel_name = hotel.css('.hotel_name a::text').extract_first()
            hotel_url = hotel.css('.hotel_name a::attr(href)').extract_first()
            hotel_url = 'http://hotels.ctrip.com' + hotel_url
            request = Request(url=hotel_url, callback=self.parse_hotel_page)
            request = SplashRequest(url=hotel_url, callback=self.parse_hotel_page,
                                    args={
                                        'wait': 5,
                                        'timeout': 20,
                                        'headers': {
                                            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36'
                                        }
                                    })
            request.meta['city'] = response.meta['city']
            request.meta['hotel_name'] = hotel_name
            request.meta['hotel_url'] = hotel_url
            yield request

    def parse_hotel_page(self, response):
        rooms = response.css('table#J_RoomListTbl tr[expand]')
        source = 'ctrip'
        country = 'cn'
        meta = response.meta
        city = meta['city']
        hotel_name = meta['hotel_name']
        hotel_url = meta['hotel_url']

        room_name = None
        for room in rooms:
            _room_name = room.css('a.room_unfold::text').extract_first()
            if _room_name:
                room_name = _room_name.strip()

            product_name = room.css('.room_type_name::text').extract_first()
            product_price = room.css('.base_txtdiv::text').extract_first()

            item = ProductItem()
            item['source'] = source
            item['country'] = country
            item['city'] = city
            item['hotel_name'] = hotel_name
            item['hotel_url'] = hotel_url
            item['room_name'] = room_name
            item['product_name'] = product_name
            item['product_price'] = product_price
            yield item
