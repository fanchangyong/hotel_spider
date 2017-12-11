# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import logging

import pymysql
from scrapy.exceptions import DropItem
from hotel_spider import settings
from hotel_spider.items import ProductItem


class HotelSpiderPipeline(object):
    def __init__(self):
        self.connect = pymysql.connect(
            host=settings.MYSQL_HOST,
            db=settings.MYSQL_DB,
            user=settings.MYSQL_USER,
            passwd=settings.MYSQL_PASSWD,
            charset='utf8',
            use_unicode=True
        )
        self.cursor = self.connect.cursor()

    def process_item(self, item, spider):
        if item.__class__ == ProductItem:
            self.process_product_item(item, spider)
        else:
            raise DropItem('Unknown item type: ' % item)
        return item

    def process_product_item(self, item, spider):
        try:
            source = item['source']
            country = item['country']
            city = item['city']
            raw_name = item['hotel_name']
            hotel_url = item['hotel_url']
            room_name = item['room_name']
            product_name = item['product_name']
            product_price = item['product_price']

            if not source:
                raise DropItem('no source')
            if not country:
                raise DropItem('no country')
            if not city:
                raise DropItem('no city')
            if not raw_name:
                raise DropItem('no raw_name')
            if not room_name:
                raise DropItem('no room_name')
            if not product_name:
                raise DropItem('no product_name')
            if not product_price:
                raise DropItem('no product_price')

            # Insert or update hotels
            self.cursor.execute(
                """
                select id from hotels where source=%s and country=%s and city=%s and raw_name=%s
                """,
                (source, country, city, raw_name)
            )
            ret = self.cursor.fetchone()
            if ret:
                hotel_id = ret[0]
                self.cursor.execute(
                    """
                    update hotels set url = %s where id = %s
                    """,
                    (hotel_url, hotel_id)
                )
                self.connect.commit()
            else:
                self.cursor.execute(
                    """
                    INSERT INTO hotels(source, country, city, raw_name, url)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (source, country, city, raw_name, hotel_url)
                )
                ret = self.connect.commit()
                hotel_id = self.cursor.lastrowid

            # insert or update rooms
            self.cursor.execute(
                """
                select id from rooms where hotel_id = %s and name = %s
                """,
                (hotel_id, room_name)
            )
            ret = self.cursor.fetchone()
            if ret:
                room_id = ret[0]
            else:
                self.cursor.execute(
                    """
                    insert into rooms(hotel_id, name) values (%s, %s)
                    """,
                    (hotel_id, room_name)
                )
                self.connect.commit()
                room_id = self.cursor.lastrowid

            # insert or update products
            self.cursor.execute(
                """
                select id from products where hotel_id = %s and room_id = %s and name = %s
                """,
                (hotel_id, room_id, product_name)
            )
            ret = self.cursor.fetchone()
            if ret:
                pass
            else:
                self.cursor.execute(
                    """
                    insert into products (hotel_id, room_id, name, price) values (%s, %s, %s, %s)
                    """,
                    (hotel_id, room_id, product_name, product_price)
                )

        except Exception as error:
            raise error
