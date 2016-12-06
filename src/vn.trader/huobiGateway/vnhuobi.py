# encoding: UTF-8
from time import sleep

from vtGateway import *

from Queue import Queue,Empty
import urllib
import requests
from threading import Thread

# 账户货币代码

# 电子货币代码

# 行情深度


# K线时间区间
INTERVAL_1M = '1min'
INTERVAL_3M = '3min'
INTERVAL_5M = '5min'
INTERVAL_15M = '15min'
INTERVAL_30M = '30min'
INTERVAL_1H = '1hour'
INTERVAL_2H = '2hour'
INTERVAL_4H = '4hour'
INTERVAL_6H = '6hour'
INTERVAL_1D = 'day'
INTERVAL_3D = '3day'
INTERVAL_1W = 'week'

# 交易代码，需要后缀货币名才能完整
TRADING_SYMBOL_BTC = 'btc_'
TRADING_SYMBOL_LTC = 'ltc_'

# 委托类型
TYPE_BUY = 'buy'
TYPE_SELL = 'sell'
TYPE_BUY_MARKET = 'buy_market'
TYPE_SELL_MARKET = 'sell_market'

# 期货合约到期类型
FUTURE_EXPIRY_THIS_WEEK = 'this_week'
FUTURE_EXPIRY_NEXT_WEEK = 'next_week'
FUTURE_EXPIRY_QUARTER = 'quarter'

# 期货委托类型
FUTURE_TYPE_LONG = 1
FUTURE_TYPE_SHORT = 2
FUTURE_TYPE_SELL = 3
FUTURE_TYPE_COVER = 4

# 期货是否用现价
FUTURE_ORDER_MARKET = 1
FUTURE_ORDER_LIMIT = 0

# 期货杠杆
FUTURE_LEVERAGE_10 = 10
FUTURE_LEVERAGE_20 = 20

# 委托状态
ORDER_STATUS_NOTTRADED = 0
ORDER_STATUS_PARTTRADED = 1
ORDER_STATUS_ALLTRADED = 2
ORDER_STATUS_CANCELLED = -1
ORDER_STATUS_CANCELLING = 4

HOST_URL='http://api.huobi.com'
HOST_MARKET_CNY='staticmarket'
HOST_MARKET_USD='usdmarket'
JSON_NAME='%s_%s_json.js'




########################################################################
class HuobiApi(object):
    """基于Websocket的API对象"""

    # ----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        self.apiKey = ''  # 用户名
        self.secretKey = ''  # 密码
        self.host = ''  # 服务器地址

        self.active = False  # API的工作状态

        self.reqID = 0  # 请求编号
        self.reqQueue = Queue()  # 请求队列
        self.reqThread = Thread(target=self.processQueue)  # 请求处理线程
        self.streamPricesThread = Thread(target=self.processStreamPrices)  # 实时行情线程
        self.DEBUG = False
        self.spotTicker=['btc']
        #######################
        ## 通用函数
        #######################

    # ----------------------------------------------------------------------
    def init(self, host, apiKey, secretKey, password,trace=False):
        """连接服务器"""
        self.host = host
        self.apiKey = apiKey
        self.secretKey = secretKey
        self.password=password
        self.active = True
        self.reqThread.start()
        self.streamPricesThread.start()
    # ----------------------------------------------------------------------

    def processQueue(self):
        """处理请求队列中的请求"""
        while self.active:
            try:
                req = self.reqQueue.get(block=True, timeout=1)  # 获取请求的阻塞为一秒
                callback = req['callback']
                #reqID = req['reqID']
                r, error = self.processRequest(req)
                try:
                    if r.status_code == 200:
                        data = r.json()
                        if self.DEBUG:
                            print callback.__name__
                        callback(data)
                except Exception, e:
                    self.onError(str(e))

            except Empty:
                pass

    # ----------------------------------------------------------------------

    def processRequest(self, req):
        """发送请求并通过回调函数推送数据结果"""
        r = None
        error = None
        params = req['params']
        payload = urllib.urlencode(params)
        try:
            r = requests.post(self.host, params=payload)
        except Exception, e:
            error=e

        return r,error

    # ----------------------------------------------------------------------

    # def processRequestTicker(self,req):
    #     """实时数据请求"""
    #     result = None
    #     error = None
    #     try:
    #         params=req['params']
    #         tickerDepth=params['ticker_depth']
    #         symbol=params['symbol']
    #         # 实时行情数据文件名
    #         fileName = JSON_NAME % (tickerDepth,symbol)
    #         # 实时行情数据地址
    #         tickerURL = HOST_URL + '/' + HOST_MARKET_CNY + '/' + fileName
    #
    #         result = requests.post(tickerURL)
    #
    #     except Exception, e:
    #         print "TickerRequestError("+str(symbol)+"):" + str(e.message)
    #         error = e
    #
    #     return result,error

    def processRequestTicker(self, symbol,ticker):
        """实时数据请求"""
        result = None
        error = None
        try:
            # 实时行情数据文件名
            fileName = JSON_NAME % (ticker, symbol)
            # 实时行情数据地址
            tickerURL = HOST_URL + '/' + HOST_MARKET_CNY + '/' + fileName

            result = requests.post(tickerURL)

        except Exception, e:
            print "TickerRequestError(" + str(symbol) + "):" + str(e.message)
            sleep(0.5)
            try:
                result = requests.post(tickerURL)
            except Exception, e:
                print "TickerRequestError_again(" + symbol + "):" + str(e.message)
                error = e

        return result, error

    # ----------------------------------------------------------------------

    def processRequestDepth(self,symbol,depth):
        """发送请求并通过回调函数推送数据结果"""
        result = None
        error = None

        try:
            fileName=JSON_NAME % (depth, symbol)
            deptURL=HOST_URL+'/'+HOST_MARKET_CNY+'/'+fileName
            result = requests.post(deptURL)
        except Exception, e:
            print "DepthRequestError("+symbol+"):" + str(e.message)
            sleep(0.5)
            try:
                result = requests.post(deptURL)
            except Exception, e:
                print "DepthRequestError_again(" + symbol + "):" + str(e.message)
                error = e

        return result, error

    # ----------------------------------------------------------------------

    def sendRequest(self, params, callback):
        """发送请求"""

        self.reqID += 1

        req = {'params': params,
               'callback': callback
               #'reqID': self.reqID
               }
               # 交易数据，行情数据区分（DEFUALT：交易API）
               #'apiFlag':apiFlag}
        self.reqQueue.put(req)

        #return self.reqID

    # ----------------------------------------------------------------------

    def onGetAccountInfo(self, data, reqID):
        """回调函数"""
        pass

    # ----------------------------------------------------------------------
    def onGetInstruments(self, data, reqID):
        """回调函数"""
        pass

    # ----------------------------------------------------------------------
    def onTicker(self, data):
        pass

    # ----------------------------------------------------------------------
    def onDepth(self, data):
        pass

    # ----------------------------------------------------------------------
    def getInstruments(self, params):
        """查询可交易的合约列表"""
        return self.processRequestMarket(self.onGetInstruments)

    # ----------------------------------------------------------------------

    def processStreamPrices(self):
        """获取价格推送"""
        # 首先获取所有合约的代码
        while self.active:
            for symbol in self.spotTicker:
                sleep(0.5)
                r, error = self.processRequestTicker(symbol,'ticker')
                print "processStreamPrices is start"
                try:
                    if r.status_code == 200:
                        data = r.json()
                        self.onTicker(data)
                except Exception,e:
                    self.onError(str(e))
                    return

                r, error = self.processRequestDepth(symbol,'depth')
                try:
                    if r.status_code == 200:
                        data = r.json()
                        self.onDepth(data)
                except Exception,e:
                    self.onError(str(e))
                    return


    #----------------------------------------------------------------------
    def onMessage(self, ws, evt):
        """信息推送""" 
        print 'onMessage'
        data = self.readData(evt)
        print data
        
    #----------------------------------------------------------------------
    def onError(self,evt):
        """错误推送"""
        pass
        
    #----------------------------------------------------------------------
    def onClose(self, ws):
        """接口断开"""
        print 'onClose'
        
    #----------------------------------------------------------------------
    def onOpen(self, ws):
        """接口打开"""
        print 'onOpen'


        
    #----------------------------------------------------------------------
    def spotUserInfo(self):
        """查询现货账户"""
        pass

    #----------------------------------------------------------------------

    # ----------------------------------------------------------------------

        


