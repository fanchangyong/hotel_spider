# -*- coding: utf-8 -*-
import scrapy

from scrapy.http import Request
from hotel_spider.items import CityItem

class CitiesSpider(scrapy.Spider):
    name = 'cities'
    allowed_domains = ['ctrip.com']

    def start_requests(self):
        domestic_url = 'http://hotels.ctrip.com/domestic-city-hotel.html'
        intl_url = 'http://hotels.ctrip.com/international/landmarks/'
        return [
            Request(url=domestic_url, callback=self.parse_domestic),
            Request(url=intl_url, callback=self.parse_intl)
        ]

    def parse_domestic(self, response):
        country = '中国'
        for city in response.css('.pinyin_filter_detail dd a'):
            city_name = city.css('a::text').extract_first()
            item = CityItem()
            item['country'] = country
            item['city'] = city_name
            yield item

    def parse_intl(self, response):
        for country in response.css('ul.nation_list li'):
            country_name = country.css('strong.nation a::text').extract_first()
            country_url = country.css('strong.nation a::attr(href)').extract_first()
            country_url = country_url + '/city'
            request = Request(url=country_url, callback=self.parse_intl_cities_page)
            request.meta['country'] = country_name
            yield request

    def parse_intl_cities_page(self, response):
        country = response.meta['country']
        for city in response.css('ul.other_city li a'):
            city_name = city.css('::text').extract_first()
            city_name = city_name.replace('酒店', '')
            item = CityItem()
            item['country'] = country
            item['city'] = city_name
            yield item

