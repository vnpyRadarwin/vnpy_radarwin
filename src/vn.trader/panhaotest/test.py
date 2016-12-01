# encoding: UTF-8
import time
import urllib
import hashlib
import requests


def Order():
    """发送撤單"""
    timestamp = long(time.time())

    paramsDict = {"access_key": "c51a66be-45e7bdcd-10bdef43-6b7d8", "secret_key": "223c0ee1-7a6dff29-5b4824d8-b07d1",
                  "coin_type": 1, "created": timestamp, "method": 'get_orders'}
    sign = signature(paramsDict)
    del paramsDict["secret_key"]
    paramsDict['sign'] = sign
    payload = urllib.urlencode(paramsDict)
    r = requests.post('https://api.huobi.com/apiv3', params=payload)
    print r



def cancelOrder():
    """发送撤單"""
    timestamp = long(time.time())

    paramsDict = {"access_key": "c51a66be-45e7bdcd-10bdef43-6b7d8", "secret_key": "223c0ee1-7a6dff29-5b4824d8-b07d1",
                  "coin_type": 1, "id":2857553295, "created": timestamp, "method": 'cancel_order'}
    sign = signature(paramsDict)
    del paramsDict["secret_key"]
    paramsDict['sign'] = sign
    payload = urllib.urlencode(paramsDict)
    r = requests.post('https://api.huobi.com/apiv3', params=payload)
    print r

def signature(params):
    params = sorted(params.iteritems(), key=lambda d: d[0], reverse=False)
    message = urllib.urlencode(params)
    m = hashlib.md5()
    m.update(message)
    m.digest()
    sig = m.hexdigest()
    return sig


def processRequest(self, req):
    """发送请求并通过回调函数推送数据结果"""
    r = None
    error = None
    params = req['params']
    payload = urllib.urlencode(params)
    try:
        r = requests.post(self.host, params=payload)
    except Exception, e:
        error = e

    return r, error

if __name__ == '__main__':
    cancelOrder()


