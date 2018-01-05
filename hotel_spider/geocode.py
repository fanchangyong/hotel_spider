
import random
import requests
import pymysql
from hotel_spider import settings

API_KEYS = [
    'H34BZ-3VEWX-ISD4E-7ZJK4-SZQT2-O6FQR',
    'CXFBZ-MSOLF-FYNJO-N7547-KKEQ2-VHFJ5',
    'HNPBZ-NXHEO-MTYWP-SCPCY-2TVBE-YFFDN',
    '5HTBZ-FQCEX-OCC4M-7CEUS-5MB72-FCB2F',
    'NRXBZ-HUZYU-GRZVJ-4SNCN-5LMUK-WDFVN'
]

def latlon_to_addr(latitude, longitude):
    connect = pymysql.connect(
        host=settings.MYSQL_HOST,
        db=settings.MYSQL_DB,
        user=settings.MYSQL_USER,
        passwd=settings.MYSQL_PASSWD,
        charset='utf8',
        use_unicode=True
    )
    cursor = connect.cursor()
    cursor.execute('select district from geocode where lat=%s and lon=%s',
                   (latitude, longitude)
                   )
    district = None
    ret = cursor.fetchone()
    if ret:
        district = ret[0]
    else:
        api_key = random.choice(API_KEYS)
        url = 'http://apis.map.qq.com/ws/geocoder/v1/?location=%s,%s&key=%s' % (latitude, longitude, api_key)
        r = requests.get(url)
        body = r.json()
        status = body['status']
        if status != 0:
            print('请求腾讯API失败: ' + body['message'])
            raise

        result = body['result']
        component = result['address_component']
        district = component['district']
        cursor.execute('insert into geocode(lat, lon, district) values(%s, %s, %s)',
                       (latitude, longitude, district))
        connect.commit()

    return {
        'district': district
    }
