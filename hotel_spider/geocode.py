
import random
import requests

API_KEYS = [
    'H34BZ-3VEWX-ISD4E-7ZJK4-SZQT2-O6FQR',
    'CXFBZ-MSOLF-FYNJO-N7547-KKEQ2-VHFJ5',
    'HNPBZ-NXHEO-MTYWP-SCPCY-2TVBE-YFFDN'
]

def latlon_to_addr(latitude, longitude):
    api_key = random.choice(API_KEYS)
    url = 'http://apis.map.qq.com/ws/geocoder/v1/?location=%s,%s&key=%s' % (latitude, longitude, api_key)
    r = requests.get(url)
    body = r.json()
    status = body['status']
    if status != 0:
        raise '请求腾讯API失败: ' + body['message']

    result = body['result']
    component = result['address_component']

    return {
        'district': component['district']
    }
