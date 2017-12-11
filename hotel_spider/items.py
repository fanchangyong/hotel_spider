# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class HotelSpiderItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass

class ProductItem(scrapy.Item):
    source = scrapy.Field()
    country = scrapy.Field()
    city = scrapy.Field()
    hotel_name = scrapy.Field()
    brand = scrapy.Field()
    branch = scrapy.Field()
    hotel_url = scrapy.Field()
    room_name = scrapy.Field()
    product_name = scrapy.Field()
    product_price = scrapy.Field()
