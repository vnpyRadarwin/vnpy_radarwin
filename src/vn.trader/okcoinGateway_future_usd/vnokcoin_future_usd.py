# encoding: UTF-8
import httplib
import json
from time import sleep

from vtGateway import *

from Queue import Queue,Empty
import urllib
import requests
from threading import Thread
from rwFunction import *
from rwConstant import *
from weixinWarning import *


HOST_URL='www.okcoin.com'


RECONNECTION_TIMES=3
RECONNECTION_SLEEPTIMES=0.5

#断线后重连间隔时间
RECONNECTION_INTERVAL=600

#进程间间隔
THREAD_INTERVAL=0.5

CONTRACT_TYPE='this_week'

########################################################################
class OkcoinApi(object):
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
        #self.streamDepthThread = Thread(target=self.processStreamDepth)  # 实时深度线程
        self.DEBUG = False
        self.spotTicker=['btc_usd']
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
        #self.streamDepthThread.start()
    # ----------------------------------------------------------------------

    def processQueue(self):
        """处理请求队列中的请求"""
        while self.active:
            try:
                error=False
                req = self.reqQueue.get(block=True, timeout=1)  # 获取请求的阻塞为一秒
                callback = req['callback']
                data, error = self.processRequest(req)
                if error:
                    #1分钟后在连接
                    sleep(RECONNECTION_INTERVAL)
                    continue

                try:
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
        reqResource=req['resource']
        payload = urllib.urlencode(reqParamas)
        headers = {
            "Content-type": "application/x-www-form-urlencoded",
        }
        try:


            conn = httplib.HTTPSConnection(HOST_URL, timeout=10)

            conn.request("POST", reqResource, payload, headers)

            response = conn.getresponse()
            data = response.read().decode('utf-8')
            result = json.loads(data)
            reqParamas.clear()
            conn.close()


        except Exception, e:
             sleep(THREAD_INTERVAL)
             try:
                 conn = httplib.HTTPSConnection(HOST_URL, timeout=10)

                 conn.request("POST", reqResource, payload, headers)

                 response = conn.getresponse()
                 data = response.read().decode('utf-8')
                 result = json.loads(data)
                 reqParamas.clear()
                 conn.close()
             except Exception, e:
                 print "Info Data Connect Fail"
                 infoError = True

        return result,infoError

    # ----------------------------------------------------------------------

    def processRequestTicker(self, symbol):
        """实时数据请求"""
        # result,tickError = reConnection_tick(times=RECONNECTION_TIMES,host=tickerURL,sleepTime=RECONNECTION_SLEEPTIMES)
        tickError=False
        result=None
        TICKER_RESOURCE = "/api/v1/future_ticker.do"
        try:
            params = ''
            if symbol:
                params = 'symbol=%(symbol)s&contract_type=%(contract_type)s' % {'symbol': symbol,'contract_type':CONTRACT_TYPE}
            result = self.httpGet(HOST_URL,TICKER_RESOURCE,params)
        except Exception, e:
             sleep(THREAD_INTERVAL)
             try:
                 result = self.httpGet(HOST_URL,TICKER_RESOURCE,params)
             except Exception, e:
                 print "Tick Data Connect Fail"
                 sendMessage=u'OKCOIN的行情数据连接中断,10分钟后重新连接'
                 #send_msg(WEIXIN_MESSAGE_ERROR,sendMessage)
                 tickError = True

        return result, tickError

    # ----------------------------------------------------------------------

    def processRequestDepth(self,symbol):
        """实时数据请求"""
        # result,tickError = reConnection_tick(times=RECONNECTION_TIMES,host=tickerURL,sleepTime=RECONNECTION_SLEEPTIMES)
        tickError=False
        result=None
        TICKER_RESOURCE = "/api/v1/future_depth.do"
        try:
            params = ''
            if symbol:
                params = 'symbol=%(symbol)s&contract_type=%(contract_type)s' % {'symbol': symbol,'contract_type':CONTRACT_TYPE}
            result = self.httpGet(HOST_URL,TICKER_RESOURCE,params)
        except Exception, e:
             sleep(THREAD_INTERVAL)
             try:
                 result = self.httpGet(HOST_URL,TICKER_RESOURCE,params)
             except Exception, e:
                 print "Depth Data Connect Fail"
                 sendMessage=u'OKCOIN美国站的期货深度数据连接中断,10分钟后重新连接'
                 #send_msg(WEIXIN_MESSAGE_ERROR,sendMessage)
                 tickError = True

        return result, tickError

    # ----------------------------------------------------------------------

    def sendRequest(self, params, callback,resource):
        """发送请求"""

        self.reqID += 1

        req = {'params': params,
               'callback': callback,
               'resource': resource
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
                sleep(THREAD_INTERVAL)
                tickData, tickError = self.processRequestTicker(symbol)
                depthData, depthError = self.processRequestDepth(symbol)
                if tickError or depthError:
                    # 1分钟后在连接
                    sleep(RECONNECTION_INTERVAL)
                    break

                try:
                    self.onTicker(tickData,depthData)
                except Exception,e:
                    print "tick error:",tickData,depthData

    # ----------------------------------------------------------------------

    def processStreamDepth(self):
        """获取深度推送"""
        # 首先获取所有合约的代码
        while self.active:
            for symbol in self.spotTicker:
                sleep(THREAD_INTERVAL)
                data, error = self.processRequestDepth(symbol)
                if error:
                    # 10分钟后在连接
                    sleep(RECONNECTION_INTERVAL)
                    print "depth data reconnection"
                    break

                try:
                    self.onDepth(data)
                except Exception, e:
                    print "tick error:", data

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
    def httpGet(self,url, resource, params=''):
            conn = httplib.HTTPSConnection(url, timeout=10)
            conn.request("GET", resource + '?' + params)
            response = conn.getresponse()
            data = response.read().decode('utf-8')
            return json.loads(data)
    # ----------------------------------------------------------------------

        


