#coding=utf-8
import hashlib
import httplib
import json
import time
import urllib

import requests
from rwDbConnection import *


#初始化apikey，secretkey,url
apikey = '933a76b1-a15e-4bc8-97c4-247b4ee123fe'
secretkey = 'F1DE03EC7723C6748E23FD3C2DFF5CA7'
#okcoinRESTURL = 'www.okcoin.com'   #请求注意：国内账号需要 修改为 www.okcoin.cn
okcoinRESTURL = 'www.okcoin.cn'





class okcoinService(object):

    def __init__(self):
        self.dbCon = rwDbConnection()
        data = self.dbCon.getMySqlData(GET_ACCOUNT_INFO, params='OKCOIN', dbFlag=DATABASE_VNPY)
        data = data[0]
        self.apiKey = str(data['apiKey'])
        self.secretKey = str(data['secretKey'])

    '''
    获取账号详情
    '''


    def userinfo(self):
        USERINFO_RESOURCE = "/api/v1/userinfo.do"
        params = {}
        params['api_key'] = self.apiKey
        params['sign'] = self.buildMySign(params, self.secretKey)
        return self.httpPost(okcoinRESTURL, USERINFO_RESOURCE, params)
        # 现货订单信息查询


    def orderinfo(self,orderId):
        ORDER_INFO_RESOURCE = "/api/v1/order_info.do"
        params = {
            'api_key': self.apiKey,
            'symbol': 'btc_cny',
            'order_id': orderId
        }
        params['sign'] = self.buildMySign(params, self.secretKey)
        result=self.httpPost(okcoinRESTURL, ORDER_INFO_RESOURCE, params)
        ordersData = result['orders']
        return ordersData[0]

    def buildMySign(self,params,secretKey):
        sign = ''
        for key in sorted(params.keys()):
            sign += key + '=' + str(params[key]) +'&'
        data = sign+'secret_key='+secretKey
        return  hashlib.md5(data.encode("utf8")).hexdigest().upper()


    def httpPost(self,url, resource, params):
        headers = {
            "Content-type": "application/x-www-form-urlencoded",
        }

        conn = httplib.HTTPSConnection(url, timeout=10)
        temp_params = urllib.urlencode(params)

        conn.request("POST", resource, temp_params, headers)

        response = conn.getresponse()
        data = response.read().decode('utf-8')
        data=json.loads(data)
        params.clear()
        conn.close()
        return data

if __name__=='__main__':
    print (u' 用户现货账户信息 ')
    method=okcoinService()
    data=method.orderinfo(111111)
    print data

