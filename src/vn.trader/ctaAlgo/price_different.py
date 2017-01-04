# encoding: UTF-8

"""

注意事项：
1. 作者不对交易盈利做任何保证，策略代码仅供参考    author = u'Vista'
    #mysql参数
    host = 'localhost'
2. 本策略需要用到talib，没有安装的用户请先参考www.vnpy.org上的教程安装
3. 将IF0000_1min.csv用ctaHistoryData.py导入MongoDB后，直接运行本文件即可回测策略

"""

from ctaBase import *
from ctaTemplate_2 import CtaTemplate_2
from datetime import datetime
import talib
import numpy as np
from radarwinFunction.rwDbConnection import *
from radarwinFunction.rwConstant import *
from radarwinFunction.rwLoggerFunction import *
from radarwinFunction.rwFunction import *
from weixinWarning import *

########################################################################
class Price_Different(CtaTemplate_2):
    """布林带突破系统"""
    className = 'Price_Different'
    author = u'vista'
    tablename = 'bolling_okcoin_test'
    # 策略参数
    bollingLength = 30
    atrFactor = 6
    atsfactor = 6
    atrLength = 15  # 计算ATR指标的窗口数
    maLength = 20  # 计算A均线的窗口数
    trailingPercent = 0.2  # 百分比移动止损
    initDays = 50  # 初始化数据所用的天数

    #账户资金变量
    btcnum = 0
    cnynum = 0
    # 策略变量
    bar_okcoin = None  # K线对象
    bar_huobi = None  # K线对象
    barMinute_okcoin = EMPTY_STRING  # K线当前的分钟
    barMinute_huobi = EMPTY_STRING  # K线当前的分钟
    datacount = 0
    bufferSize = 30  # 需要缓存的数据的大小
    bufferCount = 0  # 目前已经缓存了的数据的计数
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
    lots = 0.01             #交易手数
    entryPrice = 0
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

    priceDifferent=5

    # 参数列表，保存了参数的名称
    paramList = ['name',
                 'className',
                 'author',
                 'vtSymbol',
                 'bollingLength',
                 'atrLength'
                 ]

    # 变量列表，保存了变量的名称
    varList = ['inited',
               'trading',
               'signal',
               'direction',
               'pos',
               'entryPrice',
               'upLine',
               'lowLine',
               'longStop',
               'shortStop',
               'realtimeprice',
               'intraTradeHigh',
               'intraTradeLow'
               ]

    # ----------------------------------------------------------------------
    def __init__(self, ctaEngine, setting):
        """Constructor"""
        super(Price_Different, self).__init__(ctaEngine, setting)
        self.logger = rwLoggerFunction()
        self.dbCon = rwDbConnection()
        self.positionDict = {}
        self.tickDict={}
        self.messageFlag = False
        self.buySellFlag=0
        self.positionDict_huobi = {}
        self.positionDict_okcoin = {}
        # 注意策略类中的可变对象属性（通常是list和dict等），在策略初始化时需要重新创建，
        # 否则会出现多个策略实例之间数据共享的情况，有可能导致潜在的策略逻辑错误风险，
        # 策略类中的这些可变对象属性可以选择不写，全都放在__init__下面，写主要是为了阅读
        # 策略时方便（更多是个编程习惯的选择）


    # ----------------------------------------------------------------------
    def onInit(self):
        """初始化策略（必须由用户继承实现）"""
        self.writeCtaLog(u'%s策略初始化' % self.name)
        self.putEvent()

    # ----------------------------------------------------------------------
    def onStart(self):
        """启动策略（必须由用户继承实现）"""
        self.writeCtaLog(u'%s策略启动' % self.name)
        print "start"
        self.messageFlag = True
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
            print 'OKCOIN_K线已更新，最近K线时间：', self.barMinute_okcoin, bar.datetime, tickMinute
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
            print 'HUOBI_K线已更新，最近K线时间：',self.barMinute_huobi,bar.datetime,tickMinute
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
        #print 'orderinfo:'+ order.direction, order.price, order.tradedVolume
        pass

    def onTrade(self, trade):
        """收到成交变化推送（必须由用户继承实现）"""
        # if self.direction == 0 :
        #     tradedirection = trade.direction.encode('utf-8') + '平'
        # else :
        #     tradedirection = trade.direction.encode('utf-8') + '开'
        #
        # value = [tradedirection, trade.price, trade.volume, self.intraTradeHigh, self.intraTradeLow, datetime.now(), self.lasttradetype, self.direction]
        # sqlcontent = 'insert into ' + self.tablename + '(trade_type,price,volume,intrahigh,intralow,trade_time,lasttradetype,pos) values(%s,%s,%s,%s,%s,%s,%s,%s)'
        # #print  '价格：',trade.price
        # self.dbCon.insUpdMySqlData(sqlcontent, value,dbFlag=DATABASE_VNPY)
        pass

    def onPosition(self,position):
        if "HUOBI" in position:
            self.positionDict_huobi = position
        elif "OKCOIN" in position:
            self.positionDict_okcoin = position
        pass

    def __processQueue(self,gatewayName,tick):
        self.tickDict[gatewayName]=tick

        if 'HUOBI' in self.tickDict and 'OKCOIN' in self.tickDict:
            huobi_lastprice = self.tickDict['HUOBI'].lastPrice
            okcoin_lastprice = self.tickDict['OKCOIN'].lastPrice
            #self.buyresult = getPosition("buy", self.positionDict, huobi_lastprice + 1, self.lots)
            #self.sellresult = getPosition("sell", self.positionDict, okcoin_lastprice - 1, self.lots)
            #价差大于设定值的时候
            if abs(huobi_lastprice-okcoin_lastprice) > self.priceDifferent:

                print "yes:",huobi_lastprice-okcoin_lastprice
                #print "self.messageFlag:",self.messageFlag
                if self.messageFlag:
                    self.messageFlag = False
                    if huobi_lastprice > okcoin_lastprice:
                        sellResult = getPosition("sell", self.positionDict_huobi, self.tickDict['HUOBI'], self.lots)
                        buyResult = getPosition("buy", self.positionDict_okcoin, self.tickDict['OKCOIN'], self.lots)
                        if sellResult and buyResult:
                            #huobi:sell , okcoin:buy
                            #self.vtSymbol=self.exSymbol['HUOBI']
                            self.sell(self.tickDict['HUOBI'].lastPrice-10, self.lots,'HUOBI')
                            #self.vtSymbol = self.exSymbol['OKCOIN']
                            self.buy(self.tickDict['OKCOIN'].lastPrice+10, self.lots,'OKCOIN')



                            sendMessage = "套利执行：" + str(abs(huobi_lastprice - okcoin_lastprice)) + " 火币：" + str(huobi_lastprice) + " OKCOIN：" + str(okcoin_lastprice)
                            print sendMessage
                        else:
                            print "钱币不足"
                    else:
                        buyResult = getPosition("buy", self.positionDict_huobi, self.tickDict['HUOBI'], self.lots)
                        sellResult = getPosition("sell", self.positionDict_okcoin, self.tickDict['OKCOIN'], self.lots)
                        if buyResult and sellResult:
                            # huobi:buy , okcoin:sell

                            #self.vtSymbol = self.exSymbol['HUOBI']
                            self.buy(self.tickDict['HUOBI'].lastPrice+10, self.lots,'HUOBI')
                            # self.vtSymbol = self.exSymbol['OKCOIN']
                            self.sell(self.tickDict['OKCOIN'].lastPrice-10, self.lots,'OKCOIN')

                            sendMessage = "套利执行：" + str(abs(huobi_lastprice - okcoin_lastprice)) + " 火币：" + str(huobi_lastprice) + " OKCOIN：" + str(okcoin_lastprice)
                            print sendMessage
                        else:
                            print "钱币不足"
            else:
                self.messageFlag = True
                print 'no:',abs(huobi_lastprice-okcoin_lastprice)
                    #print 'self.exSymbol:', self.exSymbol



if __name__ == '__main__':
    # ----------------------------------------------------------------------
    # 提供直接双击回测的功能
    # 导入PyQt4的包是为了保证matplotlib使用PyQt4而不是PySide，防止初始化出错
    from ctaBacktesting import *
    from PyQt4 import QtCore, QtGui

    # 创建回测引擎
    engine = BacktestingEngine()

    # 设置引擎的回测模式为K线
    engine.setBacktestingMode(engine.BAR_MODE)

    # 设置回测用的数据起始日期
    engine.setStartDate('20120101')

    # 设置产品相关参数
    engine.setSlippage(0.2)  # 股指1跳
    engine.setRate(0.3 / 10000)  # 万0.3
    engine.setSize(300)  # 股指合约大小

    # 设置使用的历史数据库
    engine.setDatabase(MINUTE_DB_NAME, 'IF0000')

    # 在引擎中创建策略对象
    d = {'atrLength': 11}
    engine.initStrategy(Bolling, d)

    # 开始跑回测
    engine.runBacktesting()

    # 显示回测结果
    engine.showBacktestingResult()

    ## 跑优化
    # setting = OptimizationSetting()                 # 新建一个优化任务设置对象
    # setting.setOptimizeTarget('capital')            # 设置优化排序的目标是策略净盈利
    # setting.addParameter('atrLength', 11, 12, 1)    # 增加第一个优化参数atrLength，起始11，结束12，步进1
    # setting.addParameter('atrMa', 20, 30, 5)        # 增加第二个优化参数atrMa，起始20，结束30，步进1
    # engine.runOptimization(AtrRsiStrategy, setting) # 运行优化函数，自动输出结果

