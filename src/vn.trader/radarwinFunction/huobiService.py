#coding=utf-8
import hashlib
import time
import urllib

import requests
from rwDbConnection import *




HUOBI_SERVICE_API="https://api.huobi.com/apiv3"

BUY = "buy"
BUY_MARKET = "buy_market"
CANCEL_ORDER = "cancel_order"
ACCOUNT_INFO = "get_account_info"
NEW_DEAL_ORDERS = "get_new_deal_orders"
ORDER_ID_BY_TRADE_ID = "get_order_id_by_trade_id"
GET_ORDERS = "get_orders"
ORDER_INFO = "order_info"
SELL = "sell"
SELL_MARKET = "sell_market"


class huobiService(object):

    def __init__(self):
        self.dbCon = rwDbConnection()
        data = self.dbCon.getMySqlData(GET_ACCOUNT_INFO, params='HUOBI', dbFlag=DATABASE_VNPY)
        data = data[0]
        self.apiKey = str(data['apiKey'])
        self.secretKey = str(data['secretKey'])

    '''
    获取账号详情
    '''
    def getAccountInfo(self):
        timestamp = long(time.time())
        params = {"access_key": self.apiKey,"secret_key": self.secretKey, "created": timestamp,"method":"get_account_info"}
        sign=self.signature(params)
        params['sign']=sign

        del params['secret_key']

        payload = urllib.urlencode(params)
        r = requests.post(HUOBI_SERVICE_API, params=payload)
        if r.status_code == 200:
            data = r.json()
            return data
        else:
            return None

    '''
    获取订单详情
    @param coinType
    @param id
    '''
    def getOrderInfo(self,id):
        timestamp = long(time.time())
        params = {"access_key": self.apiKey,"secret_key": self.secretKey, "created": timestamp,"coin_type":1,"method":"order_info","id":id}
        sign=self.signature(params)
        params['sign']=sign
        del params['secret_key']

        payload = urllib.urlencode(params)
        r = requests.post(HUOBI_SERVICE_API, params=payload)
        if r.status_code == 200:
            data = r.json()
            return data
        else:
            return None

    def signature(self,params):
        params = sorted(params.iteritems(), key=lambda d:d[0], reverse=False)
        message = urllib.urlencode(params)
        m = hashlib.md5()
        m.update(message)
        m.digest()
        sig=m.hexdigest()
        return sig

if __name__=='__main__':
    print "获取账号详情"
    method=huobiService()
    print method.getOrderInfo(123455)