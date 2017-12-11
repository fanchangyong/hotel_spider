def cookie_to_dict(cookie):
    '''
    将从浏览器上Copy来的cookie字符串转化为Scrapy能使用的Dict
    :return:
    '''
    itemDict = {}
    items = cookie.split(';')
    for item in items:
        key = item.split('=')[0].replace(' ', '')
        value = item.split('=')[1]
        itemDict[key] = value
        return itemDict
