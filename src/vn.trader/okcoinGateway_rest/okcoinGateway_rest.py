# encoding: UTF-8

'''
vn.huobi的gateway接入

注意：
1. 该接口尚处于测试阶段，用于实盘请谨慎
2. 目前仅支持USD和CNY的现货交易，USD的期货合约交易暂不支持
'''
import hashlib
import httplib
import json
import os
import urllib
from copy import copy
from datetime import datetime, time
from threading import Condition

import vnokcoin_rest
from vtGateway import *
from rwConstant import *
from rwDbConnection import *
from time import localtime

#priceTypeMapReverse = {v: k for k, v in priceTypeMap.items()}


############################################
## 交易合约代码
############################################


# CNY
BTC_CNY_SPOT = 'BTC_CNY_SPOT'
#LTC_CNY_SPOT = 'LTC_CNY_SPOT'

EXCHANGE_NAME = 'OKCOIN'

############################################
## Channel和Symbol的印射
############################################
channelSymbolMap = {}



# CNY
channelSymbolMap['btccny'] = BTC_CNY_SPOT
#channelSymbolMap['ltccny'] = LTC_CNY_SPOT


############################################
## 交易所返回Response结构体
############################################
RESPONSE_CHANNEL = 'channel'
RESPONSE_DATE = 'date'
RESPONSE_NO = 'no'
RESPONSE_TICKER = 'ticker'
RESPONSE_ASKS='asks'

#持仓信息


############################################
## 持仓类型（BTC,LTC,CNY）
############################################
#SYMBOL_STYLE=['BTC','LTC','CNY']

# 电子货币代码
SYMBOL_BTC = 'btc'
#SYMBOL_LTC = 'ltc'

# 价格类型映射
priceTypeMap = {}
priceTypeMap['buy'] = (DIRECTION_LONG, PRICETYPE_LIMITPRICE)
priceTypeMap['sell'] = (DIRECTION_SHORT, PRICETYPE_LIMITPRICE)
# priceTypeMap['buy_market'] = (DIRECTION_LONG, PRICETYPE_MARKETPRICE)
# priceTypeMap['sell_market'] = (DIRECTION_SHORT, PRICETYPE_MARKETPRICE)

############################################
## 成交单类型
############################################
tradeTypeMap = {}

tradeTypeMap['buy'] = TRADE_TYPE_LIMIT_BUY
tradeTypeMap['sell'] = TRADE_TYPE_LIMIT_SELL
# tradeTypeMap['buy_market'] = TRADE_TYPE_MARKET_BUY
# tradeTypeMap['sell_market'] = TRADE_TYPE_MARKET_SELL

############################################
## 成交状态
############################################
tradeStatusMap = {}

tradeStatusMap['0'] = TRADER_STATUS_NO_DEAL
tradeStatusMap['1'] = TRADER_STATUS_PART_DEAL
tradeStatusMap['2'] = TRADER_STATUS_DEAL
tradeStatusMap['4'] = TRADER_STATUS_CANEL


############################################
## 委托单类型
############################################
orderTypeMap = {}

orderTypeMap['1'] = ORDER_TYPE_BUY
orderTypeMap['2'] = ORDER_TYPE_SELL

traderTypeMap = {}

traderTypeMap['1'] = ORDER_TYPE_BUY
traderTypeMap['2'] = ORDER_TYPE_SELL
traderTypeMap['3'] = ORDER_TYPE_BUY
traderTypeMap['4'] = ORDER_TYPE_SELL

OKCOIN_HOST="'www.okcoin.cn"
########################################################################
class OkcoinGateway(VtGateway):
    """OKCOIN接口"""

    #----------------------------------------------------------------------
    def __init__(self, eventEngine, gatewayName='OKCOIN'):
        """Constructor"""
        super(OkcoinGateway, self).__init__(eventEngine, gatewayName)

        self.api = Api(self)
        self.leverage = 0
        self.connected = False
        self.dbCon = rwDbConnection()

    #----------------------------------------------------------------------
    def connect(self):
        """连接"""
        #非画面启动接口方式
        # if strategyName:
        #     SQL = 'SELECT ai.api_key as apiKey,ai.secret_key as secretKey,ai.password as password FROM account_info ai,strategy_master sm WHERE ai.account_id = sm.account_id and sm.strategy_name = %s'
        # # 画面启动接口
        # else:
        #SQL = 'SELECT ai.api_key as apiKey,ai.secret_key as secretKey,ai.password as password FROM account_info ai,strategy_master sm WHERE ai.account_id = sm.account_id and sm.flag = 1'
        data = self.dbCon.getMySqlData(GET_ACCOUNT_INFO,params='OKCOIN',dbFlag=DATABASE_VNPY)

        try:
            data=data[0]
            host = OKCOIN_HOST
            apiKey = str(data['apiKey'])
            secretKey = str(data['secretKey'])
            password=data['password']
        except KeyError:
            log = VtLogData()
            log.gatewayName = self.gatewayName
            log.logContent = u'连接配置缺少字段，请检查'
            self.onLog(log)
            return


        # 初始化接口
        #self.leverage = leverage

        self.api.init(host, apiKey, secretKey,password)

        log = VtLogData()
        log.gatewayName = self.gatewayName
        log.logContent = u'接口初始化成功'
        self.onLog(log)
        self.api.qryGenerateCnyContract()

        #self.api.getOrders()

        # self.api.getTickerInfo(SYMBOL_BTC)
        # self.api.getTickerInfo(SYMBOL_LTC)
        # self.api.getDepthInfo(SYMBOL_BTC)
        # self.api.getDepthInfo(SYMBOL_LTC)
        #self.api.qryOrders()
        #self.api.qryTrades()

        # 启动查询
        self.initQuery()
        #self.startQuery()

    #----------------------------------------------------------------------
    def subscribe(self, subscribeReq):
        """订阅行情"""
        pass

    #----------------------------------------------------------------------
    def cancelOrder(self, cancelOrderReq):
        """撤单"""
        self.api.cancelOrder(cancelOrderReq)

    #----------------------------------------------------------------------
    def qryAccount(self):
        """查询账户资金"""
        self.api.spotUserInfo()

    #----------------------------------------------------------------------
    def qryPosition(self):
        """查询持仓"""
        pass
    # ----------------------------------------------------------------------
    def qryOrders(self):
        #下单后调用
        if self.api.tradeFlag:
            """查询委托"""
            self.api.getOrders()

    #----------------------------------------------------------------------
    def qryTrades(self):
        # 下单后调用
        if self.api.tradeFlag:
            """查询委托"""
            #self.api.getOrders()
            self.api.getTrades()


    # ----------------------------------------------------------------------
    def close(self):
        """关闭"""
        pass

    #----------------------------------------------------------------------
    def initQuery(self):
        """初始化连续查询"""
        if self.qryEnabled:
            # 需要循环的查询函数列表

            self.qryFunctionList = [self.qryAccount,self.qryTrades]#self.qryOrders,

            self.qryCount = 0           # 查询触发倒计时
            self.qryTrigger = 2         # 查询触发点
            self.qryNextFunction = 0    # 上次运行的查询函数索引

            self.startQuery()

    #----------------------------------------------------------------------
    def query(self, event):
        """注册到事件处理引擎上的查询函数"""
        self.qryCount += 1

        if self.qryCount > self.qryTrigger:
            # 清空倒计时
            self.qryCount = 0

            # 执行查询函数
            function = self.qryFunctionList[self.qryNextFunction]
            function()

            # 计算下次查询函数的索引，如果超过了列表长度，则重新设为0
            self.qryNextFunction += 1
            if self.qryNextFunction == len(self.qryFunctionList):
                self.qryNextFunction = 0

    #----------------------------------------------------------------------
    def startQuery(self):
        """启动连续查询"""
        self.eventEngine.register(EVENT_TIMER, self.query)

    #----------------------------------------------------------------------
    def setQryEnabled(self, qryEnabled):
        """设置是否要启动循环查询"""
        self.qryEnabled = qryEnabled

    # ----------------------------------------------------------------------
    def sendOrder(self, orderReq):
        """发单"""
        return self.api.sendOrder(orderReq)


########################################################################
class Api(vnokcoin_rest.OkcoinApi):
    """OKCOIN的API实现"""

    #----------------------------------------------------------------------
    def __init__(self, gateway):
        """Constructor"""
        super(Api, self).__init__()

        self.gateway = gateway                  # gateway对象
        self.gatewayName = gateway.gatewayName  # gateway对象名称

        self.cbDict = {}
        self.tickDict = {}
        self.orderDict = {}

        self.lastOrderID = ''
        self.orderCondition = Condition()
        self.trade_password = False

        #self.initCallback()
        self.tradeFlag=False

        #self.strategyName=''


    #----------------------------------------------------------------------
    def qryInstruments(self):
            """查询合约"""
            params = {'accountId': self.accountId}
            self.getInstruments(params)

    # ----------------------------------------------------------------------
    def qryGenerateCnyContract(self):
        l = self.generateCnyContract()
        for contract in l:
            contract.gatewayName = self.gatewayName
            self.gateway.onContract(contract)

    # ----------------------------------------------------------------------
    def onMessage(self, ws, evt):
        """信息推送"""
        data=json.loads(evt)
        channel = data[RESPONSE_CHANNEL]
        callback = self.cbDict[channel]
        callback(data)

    #----------------------------------------------------------------------
    def onError(self, evt):
        """错误推送"""
        error = VtErrorData()
        error.gatewayName = self.gatewayName
        error.errorMsg = str(evt)
        self.gateway.onError(error)

    #----------------------------------------------------------------------
    def onClose(self, ws):
        """接口断开"""
        self.gateway.connected = True
        self.writeLog(u'服务器连接断开')

    #----------------------------------------------------------------------
    def onOpen(self, ws):
        pass

    #----------------------------------------------------------------------
    def writeLog(self, content):
        """快速记录日志"""
        log = VtLogData()
        log.gatewayName = self.gatewayName
        log.logContent = content
        self.gateway.onLog(log)

    #----------------------------------------------------------------------
    def initCallback(self):
        """初始化回调函数"""
        pass


    #----------------------------------------------------------------------
    def generateSpecificContract(self, contract, symbol):
        """生成合约"""
        new = copy(contract)
        new.symbol = symbol
        new.vtSymbol = symbol
        #new.vtSymbol = EXCHANGE_NAME + CONNECTION_MARK + symbol
        new.name = symbol
        return new

    #----------------------------------------------------------------------
    def generateCnyContract(self):
        """生成CNY合约信息"""
        contractList = []

        contract = VtContractData()
        contract.exchange = EXCHANGE_NAME
        contract.productClass = PRODUCT_SPOT
        contract.size = 1
        contract.priceTick = 0.01
        #contract.strategyName = self.strategyName
        contractList.append(self.generateSpecificContract(contract, BTC_CNY_SPOT))

        return contractList

    # ----------------------------------------------------------------------
    # def getTickerInfo(self,symbol):
    #     """查询行情数据"""
    #     paramsDict = {"ticker_depth": 'ticker', "symbol": symbol}
    #     self.sendRequest(paramsDict, self.onTicker, API_FLAG_TICKER)

    # ----------------------------------------------------------------------
    def onTicker(self, data):
        """"""
        if 'ticker' not in data:
            return
        ticker = data['ticker']
        symbol = BTC_CNY_SPOT
        #vtSymbol= EXCHANGE_NAME+'_'+symbol
        vtSymbol =symbol
        if vtSymbol not in self.tickDict:
            tick = VtTickData()
            tick.symbol = symbol
            tick.vtSymbol = vtSymbol
            tick.gatewayName = self.gatewayName
            tick.exchange=EXCHANGE_NAME
            self.tickDict[vtSymbol] = tick
        else:
            tick = self.tickDict[vtSymbol]

        tick.highPrice = float(ticker['high'])
        tick.lowPrice = float(ticker['low'])
        tick.lastPrice = float(ticker['last'])
        tick.volume = float(ticker['vol'])
        tick.date, tick.time = generateDateTime(data['date'])

        newtick = copy(tick)
        self.gateway.onTick(newtick)

    # ----------------------------------------------------------------------
    # def getDepthInfo(self,symbol):
    #     """查询行情数据"""
    #     paramsDict = {"ticker_depth": 'depth', "symbol": symbol}
    #     self.sendRequest(paramsDict, self.onDepth, API_FLAG_TICKER)
    # ----------------------------------------------------------------------

    def onDepth(self, data):
        """"""
        # if 'asks' not in data:
        #     return
        #
        # symbol = channelSymbolMap[data['symbol']]
        #
        # if symbol not in self.tickDict:
        #     tick = VtTickData()
        #     tick.symbol = symbol
        #     tick.vtSymbol = symbol
        #     tick.gatewayName = self.gatewayName
        #     self.tickDict[symbol] = tick
        # else:
        #     tick = self.tickDict[symbol]
        #
        # tick.bidPrice1, tick.bidVolume1 = data['bids'][0]
        # tick.bidPrice2, tick.bidVolume2 = data['bids'][1]
        # tick.bidPrice3, tick.bidVolume3 = data['bids'][2]
        # tick.bidPrice4, tick.bidVolume4 = data['bids'][3]
        # tick.bidPrice5, tick.bidVolume5 = data['bids'][4]
        #
        # tick.askPrice1, tick.askVolume1 = data['asks'][0]
        # tick.askPrice2, tick.askVolume2 = data['asks'][1]
        # tick.askPrice3, tick.askVolume3 = data['asks'][2]
        # tick.askPrice4, tick.askVolume4 = data['asks'][3]
        # tick.askPrice5, tick.askVolume5 = data['asks'][4]
        pass
        #newtick = copy(tick)
        #self.gateway.onTick(newtick)

    # ----------------------------------------------------------------------
    def getOrders(self):
        """查询正在进行的委托订单"""
        # timestamp = long(time.time())
        # paramsDict = {"access_key": self.apiKey, "secret_key": self.secretKey,
        #               "created": timestamp, "coin_type": 1, "method": 'get_orders'}
        # sign = signature(paramsDict)
        # del paramsDict["secret_key"]
        # paramsDict['sign'] = sign
        # self.sendRequest(paramsDict, self.onGetOrders)
        pass

    # ----------------------------------------------------------------------
    def onGetOrders(self, data):
        """回调函数"""
        # if len(data) == 0:
        #     return
        # for d in data:
        #     order = VtOrderData()
        #     order.gatewayName = self.gatewayName
        #
        #     order.symbol = BTC_CNY_SPOT
        #     order.exchange = EXCHANGE_OKCOIN
        #     order.vtSymbol = '.'.join([order.symbol, order.exchange])
        #     order.orderID = str(d['id'])
        #     order.direction, priceType = priceTypeMap[str(d['type'])]
        #     order.offset = orderTypeMap[str(d['type'])]
        #     #order.status = orderStatusMap[str(d['status'])]
        #
        #     order.price = d['order_price']
        #     order.totalVolume = d['order_amount']
        #     order.tradeVolume = d['processed_amount']
        #     order.orderTime = generateDateTimeStamp(d['order_time'])
        #
        #     order.vtOrderID = '.'.join([self.gatewayName, order.orderID])
        #
        #     self.gateway.onOrder(order)
        #
        #     self.orderDict[order.orderID] = order
        pass
        #self.writeLog(u'委托信息查询完成')
    # ----------------------------------------------------------------------
    def getTrades(self):
        self.tradeFlag = False

        ORDER_INFO_RESOURCE = "/api/v1/order_info.do"
        params = {
            'api_key': self.apiKey,
            'symbol': 'btc_cny',
            'order_id': self.lastOrderID
        }
        params['sign'] = buildMySign(params, self.secretKey)
        self.sendRequest(params, self.onGetTrade, ORDER_INFO_RESOURCE)

    #----------------------------------------------------------------------
    def onGetTrade(self, result):
        """回调函数"""
        if 'orders' not in result:
            print 'Trade Data Error'
            return

        ordersData=result['orders']
        if len(ordersData)==0:
            print 'no Trade Data '
            return
        for data in ordersData:

            order = VtOrderData()
            order.gatewayName = self.gatewayName

            order.symbol = BTC_CNY_SPOT
            order.exchange = EXCHANGE_OKCOIN
            order.vtSymbol = '.'.join([order.symbol, order.exchange])

            order.orderID = str(data['order_id'])
            order.direction, priceType = priceTypeMap[str(data['type'])]
            order.offset = tradeTypeMap[str(data['type'])]
            # order.status = orderStatusMap[str(d['status'])]

            order.price = data['price']
            order.totalVolume = data['amount']
            order.tradeVolume = data['deal_amount']
            order.status=tradeStatusMap[str(data['status'])]
            #order.orderTime = generateDateTimeStamp(d['order_time'])

            order.vtOrderID = '.'.join([self.gatewayName, order.orderID])

            self.gateway.onOrder(order)

            #self.orderDict[order.orderID] = order
            if 'status' in data and tradeStatusMap[str(data['status'])]==TRADER_STATUS_DEAL:
                trade = VtTradeData()
                trade.gatewayName = self.gatewayName

                trade.symbol = BTC_CNY_SPOT
                trade.exchange = EXCHANGE_OKCOIN
                trade.vtSymbol = '.'.join([trade.symbol, trade.exchange])
                trade.orderID = str(data['order_id'])
                trade.tradeID=  str(data['order_id'])
                trade.direction, priceType = priceTypeMap[str(data['type'])]
                trade.offset = tradeTypeMap[str(data['type'])]


                trade.price=data['avg_price']
                trade.volume=float(data['deal_amount'])
                trade.status=tradeStatusMap[str(data['status'])]


                trade.vtOrderID = '.'.join([self.gatewayName, trade.orderID])
                trade.vtTradeID = '.'.join([self.gatewayName, trade.tradeID])

                self.gateway.onTrade(trade)

                #self.orderDict[trade.orderID] = trade

        self.writeLog(u'成交信息查询完成')

    # ----------------------------------------------------------------------
    def spotUserInfo(self):
        """查询现货账户"""
        USERINFO_RESOURCE = "/api/v1/userinfo.do"
        params ={}
        params['api_key'] = self.apiKey
        params['sign'] = buildMySign(params,self.secretKey)
        self.sendRequest(params, self.onSpotUserInfo,USERINFO_RESOURCE)

    # ----------------------------------------------------------------------
    def onSpotUserInfo(self, data):
        """回调函数"""
        # 持仓信息
        for symbol in ['btc', 'cny']:
                pos = VtPositionData()
                pos.gatewayName = self.gatewayName

                pos.symbol = symbol
                pos.vtSymbol = symbol
                pos.vtPositionName = symbol
                pos.direction = DIRECTION_NET

                funds=data['info']['funds']
                pos.frozen = float(funds['freezed']['%s' %symbol])
                pos.position = float(funds['free']['%s' %symbol])

                self.gateway.onPosition(pos)

        account = VtAccountData()

        account.gatewayName = self.gatewayName
        account.accountID = self.gatewayName
        account.vtAccountID = account.accountID
        account.balance = float(funds['asset']['total'])
        self.gateway.onAccount(account)

    # ----------------------------------------------------------------------

    def sendOrder(self, params):
        self.lastOrderID = ''
        """发送委托"""

        if params.direction == DIRECTION_LONG:
            direction='buy'
        else:
            direction = 'sell'

        TRADE_RESOURCE = "/api/v1/trade.do"
        paramsDict = {
            'api_key': self.apiKey,
            'symbol': 'btc_cny',
            'type': direction
        }
        if params.price:
            paramsDict['price'] = params.price
        if params.volume:
            paramsDict['amount'] = params.volume
        paramsDict['sign'] = buildMySign(paramsDict, self.secretKey)
        self.sendRequest(paramsDict, self.onSendOrder, TRADE_RESOURCE)

        # 等待发单回调推送委托号信息
        self.orderCondition.acquire()
        self.orderCondition.wait()
        self.orderCondition.release()
        vtOrderID = '.'.join([self.gatewayName, self.lastOrderID])
        return vtOrderID

    # ----------------------------------------------------------------------
    def onSendOrder(self,data):
        test=data['result']
        if 'result' in data and data['result']:
                self.lastOrderID= str(data['order_id'])
                self.tradeFlag = True
        else:
            print (u'火币下单失败，请查询账户资金额度')
        # 收到委托号后，通知发送委托的线程返回委托号
        self.orderCondition.acquire()
        self.orderCondition.notify()
        self.orderCondition.release()

    # ----------------------------------------------------------------------
    def cancelOrder(self, params):
        """发送撤單"""

        CANCEL_ORDER_RESOURCE = "/api/v1/cancel_order.do"
        params = {
             'api_key':self.apiKey,
             'symbol':'btc_cny',
             'order_id':params.orderID
        }
        params['sign'] = buildMySign(params,self.__secretkey)
        return self.sendRequest(params, self.onCancelOrder, CANCEL_ORDER_RESOURCE)


    # ----------------------------------------------------------------------

    def onCancelOrder(self,data):
        # if data['result'] == 'success':
        #     print "撤单完成"
        pass
    # ----------------------------------------------------------------------

    def generateUsdContract(self):
        """生成USD合约信息"""
        pass

    # ----------------------------------------------------------------------

    def onSpotTrade(self, data):
        """委托回报"""
        pass

    # ----------------------------------------------------------------------

    def onSpotCancelOrder(self, data):
        """撤单回报"""
        pass

    # ----------------------------------------------------------------------

    def spotSendOrder(self, req):
        """发单"""
        pass

    # ----------------------------------------------------------------------

    def spotCancel(self, req):
        """撤单"""
        pass
    # ----------------------------------------------------------------------


    def onSpotSubTrades(self, data):
        pass

    # ----------------------------------------------------------------------


    def onSpotOrderInfo(self, data):
        pass


def generateDateTime(s):
    """生成时间"""
    dt = datetime.fromtimestamp(float(s))
    #dt = datetime.now()
    time = dt.strftime("%H:%M:%S.%f")
    date = dt.strftime("%Y%m%d")
    return date, time

def generateDateTimeStamp(s):
    """生成时间"""
    dt = localtime(s)
    orderTime = time.strftime("%Y-%m-%d %H:%M:%S",dt)
    return orderTime



def buildMySign(params,secretKey):
    sign = ''
    for key in sorted(params.keys()):
        sign += key + '=' + str(params[key]) +'&'
    data = sign+'secret_key='+secretKey
    return  hashlib.md5(data.encode("utf8")).hexdigest().upper()

def httpPost(url, resource, params):
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



