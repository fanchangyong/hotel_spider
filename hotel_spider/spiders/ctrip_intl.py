# -*- coding: utf-8 -*-
import scrapy

from scrapy.http import Request
from scrapy_splash import SplashRequest

from hotel_spider.items import ProductItem

class CtripIntlSpider(scrapy.Spider):
    name = 'ctrip_intl'
    allowed_domains = ['ctrip.com']
    start_urls = ['http://hotels.ctrip.com/international/landmarks/']

    def parse(self, response):
        for country in response.css('ul.nation_list li'):
            country_name = country.css('strong.nation a::text').extract_first()
            country_url = country.css('strong.nation a::attr(href)').extract_first()
            country_url = country_url + '/city'
            request = Request(url=country_url, callback=self.parse_country_page)
            request.meta['country'] = country_name
            yield request

    def parse_country_page(self, response):
        for city in response.css('ul.other_city li a'):
            city_name = city.css('::text').extract_first()
            city_name = city_name.replace('酒店', '')
            city_url = city.css('::attr(href)').extract_first()
            city_url = 'http://hotels.ctrip.com' + city_url
            request = Request(url=city_url, callback=self.parse_hotel_list_page)
            request.meta['country'] = response.meta['country']
            request.meta['city'] = city_name
            yield request

    def parse_hotel_list_page(self, response):
        for hotel in response.css('.hlist .hlist_item'):
            hotel_name = hotel.css('.hlist_item_name a::text').extract_first()
            hotel_url = hotel.css('.hlist_item_name a::attr(href)').extract_first()
            hotel_url = 'http://hotels.ctrip.com' + hotel_url
            request = SplashRequest(url=hotel_url, callback=self.parse_hotel_detail_page,
                                    args={
                                        'wait': 5,
                                        'timeout': 20,
                                        'headers': {
                                            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36'
                                        }
                                    })
            request.meta['country'] = response.meta['country']
            request.meta['city'] = response.meta['city']
            request.meta['hotel_name'] = hotel_name
            request.meta['hotel_url'] = hotel_url
            yield request

    def parse_hotel_detail_page(self, response):
        rooms = response.css('table#J_RoomListTbl tr[expand]')
        source = 'ctrip-intl'
        meta = response.meta
        country = meta['country']
        city = meta['city']
        hotel_name = meta['hotel_name']
        hotel_url = meta['hotel_url']

        for room in response.css('.hroom_list .hroom_tr'):
            room_name = room.css('.hroom_base .hroom_base_tit::text').extract_first()
            for product in room.css('.hroom_tr_cols .hroom_tr_col.J_subRoomlist'):
                product_name = product.css('.hroom_roomname.J_rooms_name::text').extract_first()
                product_price = product.css('.hroom_col.hroom_col_price .base_pricediv::text').extract_first()

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

