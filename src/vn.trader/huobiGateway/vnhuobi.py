# encoding: UTF-8
from time import sleep

from vtGateway import *

from Queue import Queue,Empty
import urllib
import requests
from threading import Thread
from rwFunction import *


HOST_URL='http://api.huobi.com'
HOST_MARKET_CNY='staticmarket'
HOST_MARKET_USD='usdmarket'
JSON_NAME='%s_%s_json.js'

RECONNECTION_TIMES=3
RECONNECTION_SLEEPTIMES=0.5

#断线后重连间隔时间
RECONNECTION_INTERVAL=3600

#进程间间隔
THREAD_INTERVAL=0.5

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
    def init(self, host, apiKey, secretKey, password):
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
                error=False
                req = self.reqQueue.get(block=True, timeout=1)  # 获取请求的阻塞为一秒
                callback = req['callback']
                r, error = self.processRequest(req)
                if error:
                    #1小时后在连接
                    sleep(RECONNECTION_INTERVAL)
                    continue

                try:
                    if r.status_code == 200:
                        data = r.json()
                        callback(data)
                except Exception, e:
                    print "callback error:",callback
                    if 'message' in data:
                        print "error message:",data['message']

                    #self.onError(str(e))


            except Empty:
                pass

    # ----------------------------------------------------------------------

    def processRequest(self, req):
        """发送请求并通过回调函数推送数据结果"""

        #result, infoError = reConnection_info(times=RECONNECTION_TIMES, host=self.host, paramas=reqParamas,sleepTime=RECONNECTION_SLEEPTIMES)
        infoError = False
        result=None
        reqParamas = req['params']

        payload = urllib.urlencode(reqParamas)

        try:
            result= requests.post(self.host, params=payload)

        except Exception, e:
             sleep(THREAD_INTERVAL)
             try:
                 result = requests.post(self.host, params=payload)
             except Exception, e:
                 print "Info Data Connect Fail"
                 infoError = True

        return result,infoError

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
        # result,tickError = reConnection_tick(times=RECONNECTION_TIMES,host=tickerURL,sleepTime=RECONNECTION_SLEEPTIMES)
        tickError=False
        result=None
        try:
            # 实时行情数据文件名
            fileName = JSON_NAME % (ticker, symbol)
            # 实时行情数据地址
            tickerURL = HOST_URL + '/' + HOST_MARKET_CNY + '/' + fileName
            result = requests.post(tickerURL)
        except Exception, e:
             sleep(THREAD_INTERVAL)
             try:
                 result = requests.post(tickerURL)
             except Exception, e:
                 print "Tick Data Connect Fail"
                 tickError = True

        return result, tickError

    # ----------------------------------------------------------------------

    # def processRequestDepth(self,symbol,depth):
    #     """发送请求并通过回调函数推送数据结果"""
    #     result = None
    #     error = None
    #
    #     try:
    #         fileName=JSON_NAME % (depth, symbol)
    #         deptURL=HOST_URL+'/'+HOST_MARKET_CNY+'/'+fileName
    #         result = requests.post(deptURL)
    #     except Exception, e:
    #         sleep(0.5)
    #         try:
    #             result = requests.post(deptURL)
    #         except Exception, e:
    #             print "Depty Data Connect Fail"
    #             error = e
    #
    #     return result, error

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
                error =False
                sleep(THREAD_INTERVAL)
                r, error = self.processRequestTicker(symbol,'ticker')
                if error:
                    # 1小时后在连接
                    sleep(RECONNECTION_INTERVAL)
                    print "tick data reconnection"
                    break

                try:
                    if r.status_code == 200:
                        data = r.json()
                        self.onTicker(data)
                except Exception,e:
                    print "tick error:",data
                    #self.onError(str(data))

                # r, error = self.processRequestDepth(symbol,'depth')
                # try:
                #     if r.status_code == 200:
                #         data = r.json()
                #         self.onDepth(data)
                # except Exception,e:
                #     self.onError(str(e))
                #     return


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

        


