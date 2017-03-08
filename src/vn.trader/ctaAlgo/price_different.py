# encoding: UTF-8

"""

注意事项：
1. 作者不对交易盈利做任何保证，策略代码仅供参考    author = u'Vista'
    #mysql参数
    host = 'localhost'
2. 本策略需要用到talib，没有安装的用户请先参考www.vnpy.org上的教程安装
3. 将IF0000_1min.csv用ctaHistoryData.py导入MongoDB后，直接运行本文件即可回测策略

"""

from threading import Condition
from time import sleep

from ctaBase import *
from ctaTemplate_2 import CtaTemplate_2
from datetime import datetime
import talib
import numpy as np
from radarwinFunction.rwDbConnection import *
from radarwinFunction.rwConstant import *
from radarwinFunction.rwLoggerFunction import *
from radarwinFunction.rwFunction import *
from radarwinFunction.weixinWarning import *
from radarwinFunction.okcoinService import *
from radarwinFunction.huobiService import *
from vtGateway import *

########################################################################
class Price_Different(CtaTemplate_2):
    """价差测试"""
    className = 'Price_Different'
    author = u'vista'
    tablename = 'arbitrage_1_test'
    # 策略参数
    bollingLength = 30
    atrFactor = 6
    atsfactor = 6
    atrLength = 15  # 计算ATR指标的窗口数
    maLength = 20  # 计算A均线的窗口数
    trailingPercent = 0.2  # 百分比移动止损
    initDays = 50  # 初始化数据所用的天数
    messagetunnel = 4
    #账户资金变量
    btcnum = 0
    cnynum = 0
    # 策略变量
    bar_okcoin = None  # K线对象
    bar_huobi = None  # K线对象
    bar = None  # K线对象
    barMinute_okcoin = EMPTY_STRING  # K线当前的分钟
    barMinute_huobi = EMPTY_STRING  # K线当前的分钟
    datacount = 0
    bufferSize = 30  # 需要缓存的数据的大小
    bufferCount = 0  # 目前已经缓存了的数据的计数
    spreadCount = 0  # 已缓存价差计数
    atrCount = 0
    highArray = np.zeros(bufferSize)  # K线最高价的数组
    lowArray = np.zeros(bufferSize)  # K线最低价的数组
    closeArray = np.zeros(bufferSize)  # K线收盘价的数组
    typpArray = np.zeros(bufferSize)  # K线均价数组
    typp = 0
    upLineArray = np.zeros(bufferSize)
    upLine = 0
    lowLineArray = np.zeros(bufferSize)
    lowLine = 0
    midLineArray = np.zeros(bufferSize)
    midLine = 0
    atrArray = np.zeros(bufferSize)
    atsvalue = 0
    atrValue = 0
    trendMa = 0
    lasttrendMa = 0
    trendMaArray = np.zeros(bufferSize)
    lots = 1          #交易手数
    signal = 0
    intraTradeHigh = 0.1  # 移动止损用的持仓期内最高价
    intraTradeLow = 9999.99999  # 移动止损用的持仓期内最低价
    longStop = 0  # 多单止损价
    shortStop = 10000  # 空单止损价
    orderList = []  # 保存委托代码的列表
    lasttradetype = 0
    lastpos = 0
    realtimeprice = 0
    direction = 0
    buyresult = False
    sellresult = False

    priceDifferent=2
    factor = 2
    huobi_date = []
    huobi_price = []
    okcoin_date = []
    okcoin_price = []
    spreadArray = np.zeros(bufferSize)
    spread = 0
    upbandArray = np.zeros(bufferSize)
    lowbandArray = np.zeros(bufferSize)
    midbandArray = np.zeros(bufferSize)
    spreadtickcount = 0
    spreadtickbuffer = 10
    entryPrice = 0
    exitPrice = 0
    profit = 0
    cumProfit = 0
    sellstatus = 0
    buystatus = 0
    slip = 10
    lasthuobiorder = 0
    lastokcoinorder = 0
    testcondotion = 0
    order_status_okcoin = 0
    order_status_huobi = 0
    entryPrice_okcoin = 0
    entryPrice_huobi = 0
    exitPrice_okcoin = 0
    exitPrice_huobi = 0
    lastentryorder_okcoin = ''
    lastentryorder_huobi = ''
    lastexitorder_okcoin = ''
    lastexitorder_huobi = ''
    trade_status_okcoin = 0
    trade_status_huobi = 0
    # 参数列表，保存了参数的名称
    paramList = ['name',
                 'className',
                 'author',
                 'vtSymbol',
                 ]

    # 变量列表，保存了变量的名称
    varList = ['inited',
               'trading',
               'signal',
               'direction',
               'pos'
               ]

    # ----------------------------------------------------------------------
    def __init__(self, ctaEngine, setting):
        """Constructor"""
        super(Price_Different, self).__init__(ctaEngine, setting)
        self.logger = rwLoggerFunction()
        self.dbCon = rwDbConnection()
        self.okinfo = okcoinService()
        self.hbinfo = huobiService()
        self.positionDict = {}
        self.tickDict={}
        self.orderDict={}
        self.tradeDict = {}
        self.messageFlag = False
        self.buySellFlag=0
        self.positionDict_huobi = {}
        self.positionDict_okcoin = {}

        # 注意策略类中的可变对象属性（通常是list和dict等），在策略初始化时需要重新创建，
        # 否则会出现多个策略实例之间数据共享的情况，有可能导致潜在的策略逻辑错误风险，
        # 策略类中的这些可变对象属性可以选择不写，全都放在__init__下面，写主要是为了阅读
        # 策略时方便（更多是个编程习惯的选择）
        self.flag=False
        #self.orderCondition = Condition()

        self.orderStatus=False


    # ----------------------------------------------------------------------
    def onInit(self):
        """初始化策略（必须由用户继承实现）"""

        # SQL = 'SELECT closing_price,sequence FROM huobi_spot_btc_cny_aggregation_minute1 ORDER BY sequence DESC LIMIT 1,%s'
        #
        # data = self.dbCon.getMySqlData(SQL, self.initDays, DATABASE_RW_TRADING)
        # for d in data[::-1]:
        #     self.huobi_date.append(d['sequence'])
        #     self.huobi_price.append(d['closing_price'])
        #
        # SQL = 'SELECT closing_price,sequence FROM okcoincn_spot_btc_cny_aggregation_minute1 ORDER BY sequence DESC LIMIT 1,%s'
        #
        # data = self.dbCon.getMySqlData(SQL, self.initDays, DATABASE_RW_TRADING)
        # for d in data[::-1]:
        #     self.okcoin_date.append(d['sequence'])
        #     self.okcoin_price.append(d['closing_price'])
        #
        # #temp = list(set(self.huobi_date).intersection(set(self.okcoin_date)))
        # #temp.sort()
        # temp = np.array(self.okcoin_price) - np.array(self.huobi_price)
        #
        # for t in temp:
        #     self.calboundry(t)
        # self.calboundry(self.spread)
        self.writeCtaLog(u'%s策略初始化' % self.name)
        self.putEvent()

    # ----------------------------------------------------------------------
    def onStart(self):
        """启动策略（必须由用户继承实现）"""
        self.writeCtaLog(u'%s策略启动' % self.name)
        print "start"
        self.messageFlag = True
        self.flag = True
        self.putEvent()
        self.logger.setInfoLog("策略启动")

    # ----------------------------------------------------------------------
    def onStop(self):
        """停止策略（必须由用户继承实现）"""
        self.writeCtaLog(u'%s策略停止' % self.name)
        self.putEvent()
        self.logger.setInfoLog("策略停止")

    # ----------------------------------------------------------------------
    def onTick(self, tick):
        if self.flag:
            if tick.gatewayName=="HUOBI":
                self.__onTick_huobi(tick)
            elif tick.gatewayName == "OKCOIN":
                self.__onTick_okcoin(tick)
    # ----------------------------------------------------------------------
    def __onTick_okcoin(self, tick):
        """收到行情TICK推送（必须由用户继承实现）"""
        """收到行情TICK推送（必须由用户继承实现）"""

        self.__processQueue('OKCOIN',tick)
        # 计算K线
        tickMinute = tick.datetime.minute
        #print tickMinute , self.barMinute_okcoin

        # 当推送来的tick数据分钟数不等于指定周期时，生成新的K线
        if tickMinute != self.barMinute_okcoin:  # 一分钟
            # if ((tickMinute != self.barMinute and (tickMinute+1) % 5 == 0) or not self.bar):  #五分钟
            if self.bar_okcoin:
                self.__onBar_okcoin(self.bar_okcoin)

            bar = CtaBarData()
            bar.vtSymbol = tick.vtSymbol
            bar.symbol = tick.symbol
            bar.exchange = tick.exchange

            bar.open = tick.lastPrice
            bar.high = tick.lastPrice
            bar.low = tick.lastPrice
            bar.close = tick.lastPrice

            bar.date = tick.date
            bar.time = tick.time
            bar.datetime = tick.datetime  # K线的时间设为第一个Tick的时间

            self.bar_okcoin = bar  # 这种写法为了减少一层访问，加快速度
            self.barMinute_okcoin = tickMinute  # 更新当前的分钟
            #print 'OKCOIN_K线已更新，最近K线时间：', self.barMinute_okcoin, bar.datetime, tickMinute
            # print 'btc:',self.btcnum,'cny:',self.cnynum
        else:  # 否则继续累加新的K线
            bar = self.bar_okcoin  # 写法同样为了加快速度
            bar.high = max(bar.high, tick.lastPrice)
            bar.low = min(bar.low, tick.lastPrice)
            bar.close = tick.lastPrice
            self.realtimeprice = bar.close  # 更新策略界面实时价格



    # ----------------------------------------------------------------------
    def __onTick_huobi(self, tick):
        """收到行情TICK推送（必须由用户继承实现）"""
        self.__processQueue('HUOBI',tick)
        # 计算K线
        tickMinute = tick.datetime.minute
        #print tickMinute , self.barMinute

        # 当推送来的tick数据分钟数不等于指定周期时，生成新的K线
        if tickMinute != self.barMinute_huobi:    #一分钟
        #if ((tickMinute != self.barMinute and (tickMinute+1) % 5 == 0) or not self.bar):  #五分钟
            if self.bar_huobi:
                self.__onBar_huobi(self.bar_huobi)

            bar = CtaBarData()
            bar.vtSymbol = tick.vtSymbol
            bar.symbol = tick.symbol
            bar.exchange = tick.exchange

            bar.open = tick.lastPrice
            bar.high = tick.lastPrice
            bar.low = tick.lastPrice
            bar.close = tick.lastPrice

            bar.date = tick.date
            bar.time = tick.time
            bar.datetime = tick.datetime  # K线的时间设为第一个Tick的时间

            self.bar_huobi = bar  # 这种写法为了减少一层访问，加快速度
            self.barMinute_huobi = tickMinute  # 更新当前的分钟
            #print 'HUOBI_K线已更新，最近K线时间：',self.barMinute_huobi,bar.datetime,tickMinute
            #print 'btc:',self.btcnum,'cny:',self.cnynum
        else:  # 否则继续累加新的K线
            bar = self.bar_huobi  # 写法同样为了加快速度
            bar.high = max(bar.high, tick.lastPrice)
            bar.low = min(bar.low, tick.lastPrice)
            bar.close = tick.lastPrice
            self.realtimeprice = bar.close  # 更新策略界面实时价格


    # ----------------------------------------------------------------------
    def __onBar_okcoin(self, bar):

        pass

    # ----------------------------------------------------------------------
    def __onBar_huobi(self, bar):
        pass
    # ----------------------------------------------------------------------
    def onBar(self, bar):
        pass
    # ----------------------------------------------------------------------
    def onOrder(self, order):
        """收到委托变化推送（必须由用户继承实现）"""
        pass
        # print "onOrder"
        # if order.gatewayName == "HUOBI":
        #     self.orderDict[order.gatewayName] = order
        #     # self.orderCondition.acquire()
        #     # self.orderCondition.notify()
        #     # self.orderCondition.release()
        # elif order.gatewayName == "OKCOIN":
        #     self.orderDict[order.gatewayName] = order
        #print 'orderinfo:'+ order.direction, order.price, order.tradedVolume

    # ----------------------------------------------------------------------
    def onOrder_huobi(self, order):
        self.orderDict[order.gatewayName]=order
        if order.status == "未成交":
            sendMessage =  "HUOBI订单未成交，挂单价：" + str(order.price) +  " 挂单量：" + str(order.totalVolume) + " 时间：" + str(datetime.now()) +  "  请尽快处理。"
            send_msg(self.messagetunnel, sendMessage)
            print sendMessage
        print 'onOrder_huobi:', 'ID:', order.orderID, '成交量:', order.totalVolume, '总量:', order.tradedVolume, 'Status:', order.status
    # ----------------------------------------------------------------------
    def onOrder_okcoin(self, order):
        self.orderDict[order.gatewayName]=order
        if order.status == "未成交":
            sendMessage =  "OKCOIN订单未成交，挂单价：" + str(order.price) +  " 挂单量：" + str(order.totalVolume) + " 时间：" + str(datetime.now()) +  "  请尽快处理。"
            send_msg(self.messagetunnel, sendMessage)
            print sendMessage
        print 'onOrder_okcoin:', 'ID:', order.orderID, '成交量:', order.totalVolume, '总量:', order.tradedVolume, 'Status:', order.status


    # ----------------------------------------------------------------------
    def onTrade(self, trade):
        pass
    # ----------------------------------------------------------------------
    def onTrade_huobi(self, trade):
        self.tradeDict[trade.gatewayName]=trade
        # self.huobiexittime = datetime.now()
        # print 'onTrade_huobi:', 'ID:',trade.orderID, 'Time:',self.huobiexittime ,'Price:', trade.price,'Direction:',trade.direction,'Status:',trade.status
        # 根据订单ID更新订单状态
        print "onTrade:huobi"
        #print trade.orderID,self.lastentryorder_huobi,self.lastexitorder_huobi,type(trade.orderID),type(self.lastentryorder_huobi),type(self.lastexitorder_huobi)
        #print trade.orderID == self.lastentryorder_huobi  ,trade.orderID == self.lastexitorder_huobi
        #print trade.direction == "多",trade.direction == "空"
        if trade.orderID == self.lastentryorder_huobi:
            self.entryPrice_huobi = trade.price
            self.trade_status_huobi = 1
        elif trade.orderID == self.lastexitorder_huobi:
            self.exitPrice_huobi = trade.price
            self.trade_status_huobi = 2

        #根据订单状态计算盈利以及插入交易记录
        if self.trade_status_okcoin == 1 and self.trade_status_huobi == 1:
            self.entryPrice = self.entryPrice_okcoin - self.entryPrice_huobi
            sendMessage = "双边开仓成功，开仓价：" + str(self.entryPrice)+ ' ' + str(self.okcoinentrytime)
            print sendMessage
            send_msg(self.messagetunnel,sendMessage)
        elif self.trade_status_okcoin == 2 and self.trade_status_huobi == 2:
            self.exitPrice = self.exitPrice_okcoin - self.exitPrice_huobi
            if trade.direction == "多":
                self.profit = (self.exitPrice - self.entryPrice) * trade.volume
                tradetype = "多"
            elif trade.direction == "空":
                self.profit = (self.entryPrice - self.exitPrice) * trade.volume
                tradetype = "空"

            sendMessage = "套利平" + tradetype + ",开仓价：" + str(self.entryPrice) + " 平仓价：" + str(self.exitPrice) + "量：" + str(
                trade.volume) + "利润:" + str(self.profit)
            print sendMessage
            send_msg(self.messagetunnel, sendMessage)
            self.trade_status_huobi = 0
            self.trade_status_okcoin = 0
            value = [tradetype,self.entryPrice,self.exitPrice,trade.volume,self.profit/trade.volume,self.profit,self.okcoinentrytime,self.okcoinexittime]
            sqlcontent = 'insert into ' + self.tablename + '(trade_type,entry_price,exit_price,volume,point,profit,entry_time,exit_time) values(%s,%s,%s,%s,%s,%s,%s,%s)'
            self.dbCon.insUpdMySqlData(sqlcontent, value, dbFlag=DATABASE_VNPY)
        print self.trade_status_okcoin,self.trade_status_huobi




        # print 'huobi_ontrade_time:',self.huobiexittime - self.huobientrytime
    # ----------------------------------------------------------------------
    def onTrade_okcoin(self, trade):
        self.tradeDict[trade.gatewayName]=trade
        # self.okcoinexittime = datetime.now()
        # 根据订单ID更新订单状态
        print "onTrade:okcoin"
        #print trade.orderID, self.lastentryorder_okcoin, self.lastexitorder_okcoin ,type(trade.orderID),type(self.lastentryorder_okcoin),type(self.lastexitorder_okcoin)
        #print trade.orderID == self.lastentryorder_okcoin,trade.orderID == self.lastexitorder_okcoin
        #print trade.direction == "多", trade.direction == "空"
        if trade.orderID == self.lastentryorder_okcoin:
            self.entryPrice_okcoin = trade.price
            self.trade_status_okcoin = 1
        elif trade.orderID == self.lastexitorder_okcoin:
            self.exitPrice_okcoin = trade.price
            self.trade_status_okcoin = 2

        # 根据订单状态计算盈利以及插入交易记录
        if self.trade_status_okcoin == 1 and self.trade_status_huobi == 1:
            self.entryPrice = self.entryPrice_okcoin - self.entryPrice_huobi
            sendMessage = "双边开仓成功，开仓价：" + str(self.entryPrice)+ ' ' +  str(self.okcoinentrytime)
            print sendMessage
            send_msg(self.messagetunnel, sendMessage)
        elif self.trade_status_okcoin == 2 and self.trade_status_huobi == 2:
            self.exitPrice = self.exitPrice_okcoin - self.exitPrice_huobi
            if trade.direction == "空":
                tradetype = "多"
                self.profit = (self.exitPrice - self.entryPrice) * trade.volume
            elif trade.direction == "多":
                tradetype = "空"
                self.profit = (self.entryPrice - self.exitPrice) * trade.volume

            sendMessage = "套利平" + tradetype + ",开仓价：" + str(self.entryPrice) + " 平仓价：" + str(self.exitPrice) + "量：" + str(
                trade.volume) + "利润:" + str(self.profit)
            print sendMessage
            send_msg(self.messagetunnel, sendMessage)
            self.trade_status_huobi = 0
            self.trade_status_okcoin = 0
            value = [tradetype, self.entryPrice, self.exitPrice, trade.volume, self.profit/trade.volume,
                     self.profit, self.okcoinentrytime, self.okcoinexittime]
            sqlcontent = 'insert into ' + self.tablename + '(trade_type,entry_price,exit_price,volume,point,profit,entry_time,exit_time) values(%s,%s,%s,%s,%s,%s,%s,%s)'
            self.dbCon.insUpdMySqlData(sqlcontent, value, dbFlag=DATABASE_VNPY)
        print self.trade_status_okcoin, self.trade_status_huobi
        #print 'onTrade_okcoin:','ID:',trade.orderID,trade.tradeID ,'Price:', trade.price,'Direction:',trade.direction,'Status:',trade.status
        # print 'okcoin_ontrade_time:', self.okcoinexittime - self.okcoinentrytime
    # ----------------------------------------------------------------------
    def onTrade(self, trade):
        pass

    # ----------------------------------------------------------------------
    def onPosition(self,position):

        if "HUOBI" in position:
            self.positionDict_huobi = position
            #print "HUOBI:",datetime.now()
        elif "OKCOIN" in position:
            self.positionDict_okcoin = position
            #print "OKCOIN:", datetime.now()

    def __processQueue(self,gatewayName,tick):
        self.tickDict[gatewayName]=tick
        #print self.tickDict,self.tickDict['HUOBI'].time
        if 'HUOBI' in self.tickDict and 'OKCOIN' in self.tickDict:

            huobi_lastprice = self.tickDict['HUOBI'].lastPrice
            okcoin_lastprice = self.tickDict['OKCOIN'].lastPrice
            #print huobi_lastprice,okcoin_lastprice
            self.spread = okcoin_lastprice - huobi_lastprice
            # 测试下单模块
            # if self.testcondotion == 0:
            #     self.lastokcoinorder = self.buy(self.tickDict['OKCOIN'].lastPrice - self.slip, 0.01, 'OKCOIN')
            #     self.testcondotion = 1



            #每N个tick截取一次价差
            self.spreadtickcount += 1
            if self.spreadtickcount == self.spreadtickbuffer :
                self.calboundry(self.spread)
                self.spreadtickcount = 0

            # 读取账户信息
            # 做空账户状态：买火币，卖ok
            if getPosition("buy", self.positionDict_huobi, huobi_lastprice + self.slip, self.lots) and \
                    getPosition("sell", self.positionDict_okcoin, okcoin_lastprice - self.slip, self.lots):
                self.sellstatus = 1
            else:
                self.sellstatus = 0
            # 做多账户状态：卖火币，买ok
            if getPosition("buy", self.positionDict_okcoin, okcoin_lastprice + self.slip, self.lots) and\
                    getPosition("sell", self.positionDict_huobi, huobi_lastprice - self.slip, self.lots):
                self.buystatus = 1
            else:
                self.buystatus = 0

            #print self.sellstatus,self.buystatus






            # 开仓模块

            if self.trading == True and self.direction == 0 and abs(
                                    self.upbandArray[-1] - self.lowbandArray[-1] ) > 10 and abs(self.spread) < 200 and self.trade_status_okcoin == 0 and self.trade_status_huobi == 0 \
                    and self.order_status_huobi == 0 and self.order_status_okcoin == 0:
                # 价差大于上边界开空  ，卖ok，买火币
                if self.spread > self.upbandArray[-1] and self.sellstatus :
                    self.direction = -1
                    #self.entryPrice = self.spread
                    self.lastentryorder_okcoin = self.sell(self.tickDict['OKCOIN'].lastPrice - self.slip, self.lots, 'OKCOIN')
                    self.lastentryorder_okcoin = self.lastentryorder_okcoin.split('.')[1]
                    #Panhao
                    if self.lastentryorder_okcoin <> EMPTY_STRING:
                        self.orderStatus=self.getTrades(self.lastentryorder_okcoin,gatewayName)


                    print self.lastentryorder_okcoin
                    self.order_status_okcoin = 1 # 更改ok开仓状态
                    self.okcoinentrytime = datetime.now()
                    #print 'okcoinentrytime:',self.okcoinentrytime
                    self.lastentryorder_huobi = self.buy(self.tickDict['HUOBI'].lastPrice + self.slip , self.lots, 'HUOBI')
                    self.lastentryorder_huobi = self.lastentryorder_huobi.split('.')[1]
                    print self.lastentryorder_huobi
                    self.order_status_huobi = 1   # 更改huobi开仓状态

                    self.huobientrytime = datetime.now()

                # 价差小于下边界开多, 卖火币，买OK
                elif self.spread < self.lowbandArray[-1] and self.buystatus:
                    self.direction = 1
                    self.entryPrice = self.spread
                    self.lastentryorder_huobi = self.sell(self.tickDict['HUOBI'].lastPrice - self.slip, self.lots, 'HUOBI')
                    self.lastentryorder_huobi = self.lastentryorder_huobi.split('.')[1]
                    print self.lastentryorder_huobi
                    self.order_status_huobi = 1  # 更改huobi开仓状态
                    self.huobientrytime = datetime.now()
                    #print 'huobientrytime:', self.huobientrytime
                    self.lastentryorder_okcoin = self.buy(self.tickDict['OKCOIN'].lastPrice + self.slip , self.lots, 'OKCOIN')
                    self.lastentryorder_okcoin = self.lastentryorder_okcoin.split('.')[1]
                    self.okcoinentrytime = datetime.now()
                    print self.lastentryorder_okcoin
                    self.order_status_okcoin = 1  # 更改ok开仓状态
                    self.okcoinentrytime = datetime.now()

            # 平仓模块
            # 多单平仓
            if self.trade_status_okcoin == 1 and self.trade_status_huobi == 1:
                if self.direction == 1 and self.spread > self.midbandArray[-1]:
                    self.direction = 0
                    self.exitPrice = self.midbandArray[-1]
                    self.lastexitorder_okcoin = self.sell(self.tickDict['OKCOIN'].lastPrice - self.slip, self.lots, 'OKCOIN')
                    self.lastexitorder_okcoin = self.lastexitorder_okcoin.split('.')[1]
                    print self.lastexitorder_okcoin
                    self.order_status_okcoin = 0  # 更改ok开仓状态
                    self.okcoinexittime = datetime.now()
                    #print 'okcoinentrytime:', self.okcoinentrytime
                    self.lastexitorder_huobi = self.buy(self.tickDict['HUOBI'].lastPrice + self.slip, self.lots, 'HUOBI')
                    self.lastexitorder_huobi = self.lastexitorder_huobi.split('.')[1]
                    print self.lastexitorder_huobi
                    self.order_status_huobi = 0  # 更改huobi开仓状态
                    self.testcondotion = 1
                # 空单平仓
                if self.direction == -1 and self.spread < self.midbandArray[-1]:
                    self.direction = 0
                    self.exitPrice = self.midbandArray[-1]
                    self.lastexitorder_huobi  = self.sell(self.tickDict['HUOBI'].lastPrice - self.slip, self.lots, 'HUOBI')
                    self.lastexitorder_huobi = self.lastexitorder_huobi.split('.')[1]
                    print self.lastexitorder_huobi
                    self.order_status_huobi = 0  # 更改huobi开仓状态
                    #self.huobientrytime = datetime.now()
                    #print 'huobientrytime:', self.huobientrytime
                    self.lastexitorder_okcoin = self.buy(self.tickDict['OKCOIN'].lastPrice + self.slip, self.lots, 'OKCOIN')
                    self.lastexitorder_okcoin = self.lastexitorder_okcoin.split('.')[1]
                    self.okcoinexittime = datetime.now()
                    print self.lastexitorder_okcoin
                    self.order_status_okcoin = 0  # 更改ok开仓状态
                    self.testcondotion = 1


            self.tickDict={}

    # def __getHuobiAccount(self):
    #         data = getAccountInfo()
    #         for symbol in ['btc', 'cny']:
    #             self.positionDict_huobi[symbol] = float(data['available_%s_display' % symbol])
    #         return self.positionDict_huobi
    #
    # def __getOkcoinAccount(self):
    #         data = userinfo()
    #         funds = data['info']['funds']
    #         for symbol in ['btc', 'cny']:
    #             self.positionDict_okcoin[symbol] = float(funds['free'][symbol])
    #         return self.positionDict_okcoin
    #
    #
    # def __getHuobiOrder(self):
    #     data = getAccountInfo()
    #     for symbol in ['btc', 'cny']:
    #         self.positionDict_huobi[symbol] = float(data['available_%s_display' % symbol])
    #     return self.positionDict_huobi
    #
    #
    # def __getOkcoinOrder(self):
    #     data = userinfo()
    #     funds = data['info']['funds']
    #     for symbol in ['btc', 'cny']:
    #         self.positionDict_okcoin[symbol] = float(funds['free'][symbol])
    #     return self.positionDict_okcoin

    def calboundry(self,spread):

        self.spreadArray[0:self.bufferSize-1] = self.spreadArray[1:self.bufferSize]
        self.spreadArray[-1] = spread
        self.spreadCount += 1

        if self.spreadCount < self.bufferSize:
            self.trading = False
            return
        self.trading = True
        spread_mean = np.mean(self.spreadArray)
        spread_std = np.std(self.spreadArray)
        upband = spread_mean + self.factor * spread_std
        lowband = spread_mean- self.factor * spread_std

        self.upbandArray[0:self.bufferSize-1] = self.upbandArray[1:self.bufferSize]
        self.upbandArray[-1] = upband
        self.lowbandArray[0:self.bufferSize-1] = self.lowbandArray[1:self.bufferSize]
        self.lowbandArray[-1] = lowband
        self.midbandArray[0:self.bufferSize-1] = self.midbandArray[1:self.bufferSize]
        self.midbandArray[-1] = spread_mean
        print self.upbandArray[-1],self.lowbandArray[-1],'   ',self.spread,self.sellstatus,self.buystatus


if __name__ == '__main__':
    ACCOUNT_INFO = "get_account_info"
    data=getAccountInfo(ACCOUNT_INFO)
    positionDict_huobi={}
    for symbol in ['btc', 'cny']:
        positionDict_huobi[symbol]=float(data['available_%s_display' % symbol])
    print positionDict_huobi