
API_KEY = 'H34BZ-3VEWX-ISD4E-7ZJK4-SZQT2-O6FQR'
import requests

def latlon_to_addr(latitude, longitude):
    url = 'http://apis.map.qq.com/ws/geocoder/v1/?location=%s,%s&key=%s' % (latitude, longitude, API_KEY)
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
