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
from ctaTemplate import CtaTemplate
from datetime import datetime
import talib
import numpy as np
from radarwinFunction.rwDbConnection import *
from radarwinFunction.rwConstant import *
from radarwinFunction.rwLoggerFunction import *
from radarwinFunction.rwFunction import *

########################################################################
class Bolling(CtaTemplate):
    """布林带突破系统"""
    className = 'Bolling'
    author = u'vista'
    tablename = 'bolling_okcoin_test'
    # 策略参数
    bollingLength = 30
    atrFactor = 6
    atsfactor = 9
    atrLength = 7  # 计算ATR指标的窗口数
    maLength = 20  # 计算A均线的窗口数
    trailingPercent = 0.2  # 百分比移动止损
    initDays = 100  # 初始化数据所用的天数
    slip = 3       # 滑点
    #账户资金变量
    btcnum = 0
    cnynum = 0
    # 策略变量
    bar = None  # K线对象
    barMinute = EMPTY_STRING  # K线当前的分钟
    barHour = EMPTY_STRING  # K线当前的小时
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

    # 参数列表，保存了参数的名称
    paramList = ['name',
                 'className',
                 'author',
                 'vtSymbol',
                 'bollingLength',
                 'atrLength',
                 'atrFactor',
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
               'atsvalue',
               'realtimeprice',
               'intraTradeHigh',
               'intraTradeLow'
               ]

    # ----------------------------------------------------------------------
    def __init__(self, ctaEngine, setting):
        """Constructor"""
        super(Bolling, self).__init__(ctaEngine, setting)
        self.logger = rwLoggerFunction()
        #self.dbCon = rwDbConnection()
        self.positionDict = {}
        # 注意策略类中的可变对象属性（通常是list和dict等），在策略初始化时需要重新创建，
        # 否则会出现多个策略实例之间数据共享的情况，有可能导致潜在的策略逻辑错误风险，
        # 策略类中的这些可变对象属性可以选择不写，全都放在__init__下面，写主要是为了阅读
        # 策略时方便（更多是个编程习惯的选择）

    # ----------------------------------------------------------------------
    def onInit(self):
        """初始化策略（必须由用户继承实现）"""
        self.writeCtaLog(u'%s策略初始化' % self.name)



        # 载入历史数据，并采用回放计算的方式初始化策略数值
        initData = []
        #SQL = 'SELECT open,high,low,close,volumn,date FROM okcn_btc_cny_5 ORDER BY date DESC LIMIT 1,%s'
        #SQL = 'SELECT opening_price,max_price,min_price,closing_price,volume_price,time_stamp FROM okcoincn_spot_btc_cny_aggregation_hour1 ORDER BY sequence DESC LIMIT 1,%s'

        #data = self.dbCon.getMySqlData(SQL, self.initDays, DATABASE_RW_TRADING)
        #K线历史数据取得
        data=kline_okcoin()

        for d in data[::-1]:
            bar = CtaBarData()
            bar.open = d[1]
            bar.high = d[2]
            bar.low = d[3]
            bar.close = d[4]
            bar.volume = d[5]
            bar.datetime = d[0]
            bar.date = d[0]
            bar.time = d[0]
            bar.symbol = 'BTC_CNY_SPOT'
            bar.vtSymbol = 'BTC_CNY_SPOT'
            initData.append(bar)


        #   bitrees 数据库
        # for d in data[::-1]:
        #     bar = CtaBarData()
        #     bar.open = d['open']
        #     bar.high = d['high']
        #     bar.low = d['low']
        #     bar.close = d['close']
        #     bar.volume = d['volumn']
        #     bar.datetime=d['date']
        #     bar.date=d['date']
        #     bar.time = d['date']
        #     bar.symbol = 'BTC_CNY_SPOT'
        #     bar.vtSymbol = 'BTC_CNY_SPOT'
        #     initData.append(bar)

        #   radarwin 数据库
        # for d in data[::-1]:
        #     bar = CtaBarData()
        #     bar.open = d['opening_price']
        #     bar.high = d['max_price']
        #     bar.low = d['min_price']
        #     bar.close = d['closing_price']
        #     bar.volume = d['volume_price']
        #     bar.datetime=d['time_stamp']
        #     bar.date=d['time_stamp']
        #     bar.time = d['time_stamp']
        #     bar.symbol = 'BTC_CNY_SPOT'
        #     bar.vtSymbol = 'BTC_CNY_SPOT'
        #     initData.append(bar)

        #lasttradedata = self.readtradelog2mysql()
        #lasttradedata = False
        # if lasttradedata:
        #     self.lasttradetype = lasttradedata[0][7]
        #     self.lastpos = lasttradedata[0][8]
        #     #print 'lasttradetype is :',self.lasttradetype
        #     if self.lasttradetype == None:
        #         print 'this no trade before'
        #         self.lasttradetype = 0
        #         self.intraTradeHigh = 0
        #         self.intraTradeLow = 9999999.9999
        #     elif self.lasttradetype == 1:
        #         if self.lastpos == 0:
        #             self.intraTradeHigh = lasttradedata[0][4]
        #             print 'last trade is long,and intratradehigh = ',self.intraTradeHigh
        #         elif self.lastpos == 1:
        #             self.intraTradeHigh = float(self.getperioddata(lasttradedata[0][6],'high'))
        #             self.direction = 1
        #             self.entryPrice = lasttradedata[0][2]
        #             print 'last trade is long and not closed yet'
        #
        #     elif self.lasttradetype == -1:
        #         if self.lastpos == 0:
        #             self.intraTradeLow = lasttradedata[0][5]
        #             print 'last trade is short,and intratradelow = ', self.intraTradeLow
        #         elif self.lastpos == -1:
        #             self.intraTradeLow = float(self.getperioddata(lasttradedata[0][6],'low'))
        #             self.direction = -1
        #             self.entryPrice = lasttradedata[0][2]
        #             print 'last trade is short and not closed yet,intratradelow = ',self.intraTradeLow
        # else:
        #     self.lasttradetype =0
        #     self.direction = 0
        #     self.lastpos = 0
        #     self.intraTradeLow = 9999.99999
        #     self.intraTradeHigh = 0


        for bar in initData:
            self.onBar(bar)
        #print self.intraTradeHigh,self.intraTradeLow
        self.logger.setInfoLog("初始化")
        self.putEvent()

    # ----------------------------------------------------------------------
    def onStart(self):
        """启动策略（必须由用户继承实现）"""
        self.writeCtaLog(u'%s策略启动' % self.name)
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
        """收到行情TICK推送（必须由用户继承实现）"""
        # 计算K线
        tickMinute = tick.datetime.minute
        tickHour=tick.datetime.hour
        #print tickHour , self.barHour

        # 当推送来的tick数据分钟数不等于指定周期时，生成新的K线
        #if tickMinute != self.barMinute:    #一分钟
        #if ((tickMinute != self.barMinute and tickMinute % 60 == 0) or not self.bar):  #五分钟
        if tickHour != self.barHour or not self.bar:  #1小时
            if self.bar:
                self.onBar(self.bar)

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

            self.bar = bar  # 这种写法为了减少一层访问，加快速度
            #self.barMinute = tickMinute  # 更新当前的分钟
            self.barHour = tickHour
            print 'K线已更新，最近K线时间：',self.barHour,bar.datetime,tickHour
            #print 'btc:',self.btcnum,'cny:',self.cnynum
        else:  # 否则继续累加新的K线
            bar = self.bar  # 写法同样为了加快速度
            bar.high = max(bar.high, tick.lastPrice)
            bar.low = min(bar.low, tick.lastPrice)
            bar.close = tick.lastPrice
            self.realtimeprice = bar.close  # 更新策略界面实时价格

        # 查询账户信息，判断钱/币是否足够
        self.buyresult = getPosition("buy", self.positionDict, bar.close + 1, self.lots)
        self.sellresult = getPosition("sell", self.positionDict, bar.close - 1, self.lots)
        #print self.buyresult, self.sellresult
        #持仓状态下判断出场
        if self.trading == True:
            if self.direction > 0 and self.pos > 0:
                self.intraTradeHigh = max(self.intraTradeHigh, bar.high)
                #self.longStop = self.intraTradeHigh - self.atrArray[-1]*self.atrFactor
                if bar.close < self.atsvalue:
                    self.direction = 0
                    self.signal = 0
                    self.entryPrice = 0
                    self.lasttradetype = 1
                    self.sell(bar.close - self.slip, self.lots)
                    print '平多'
                    #if self.pos != 0:
                        #self.pos = 0

            if self.direction < 0 and self.pos < 0:
                self.intraTradeLow = min(self.intraTradeLow, bar.low)

                #self.shortStop = self.intraTradeLow + self.atrArray[-1]*self.atrFactor
                if bar.close > self.atsvalue:
                    self.direction = 0
                    self.signal = 0
                    self.entryPrice = 0
                    self.lasttradetype = -1
                    self.buy(bar.close + self.slip, self.lots)
                    print '平空'
                    #if self.pos != 0:
                        #self.pos = 0



            # 做多
            if self.pos == 0 and  self.buyresult  and self.direction == 0 and self.signal == 1 and bar.close > self.upLineArray[-1] and bar.close > self.atsvalue:
                self.direction = 1
                self.entryPrice = bar.close
                self.shortStop = 0
                self.intraTradeHigh = bar.close
                self.intraTradeHigh = max(self.intraTradeHigh, bar.high)
                self.lasttradetype = 1
                self.buy(bar.close + self.slip, self.lots)
                print '做多'
                #if self.pos == 0:
                    #self.pos = self.lots
            elif self.pos == 0 and not self.buyresult:
                print "账户余额不足，无法买入"
            # 做空
            if self.pos == 0 and self.sellresult  and self.direction == 0 and self.signal == -1 and bar.close < self.lowLineArray[-1] and bar.close < self.atsvalue:
                self.direction = -1
                self.entryPrice = bar.close
                self.longStop = 0
                self.intraTradeLow = bar.close
                self.intraTradeLow = min(self.intraTradeLow, bar.low)
                self.lasttradetype = -1
                self.sell(bar.close - self.slip, self.lots)
                print '做空'
                #if self.pos == 0:
                    #self.pos = 0-self.lots
            elif self.pos == 0 and not self.sellresult:
                 print "账户币不足，无法卖出"
    # ----------------------------------------------------------------------
    def onBar(self, bar):
        """收到Bar推送（必须由用户继承实现）"""
        # 撤销之前发出的尚未成交的委托（包括限价单和停止单）
        for orderID in self.orderList:
            self.cancelOrder(orderID)
        self.orderList = []

        # 保存K线数据
        self.closeArray[0:self.bufferSize - 1] = self.closeArray[1:self.bufferSize]
        self.highArray[0:self.bufferSize - 1] = self.highArray[1:self.bufferSize]
        self.lowArray[0:self.bufferSize - 1] = self.lowArray[1:self.bufferSize]

        self.closeArray[-1] = bar.close
        self.highArray[-1] = bar.high
        self.lowArray[-1] = bar.low
        self.typpArray =(self.closeArray+self.highArray+self.lowArray)/3
        self.typp = (bar.close+bar.high+bar.low)/3
        self.bufferCount += 1
        if self.bufferCount == 1:
            self.atsvalue = self.closeArray[-1]     # 初始化atrts

        if self.bufferCount < self.atrLength:
            print "self.bufferCount, self.atrLength",self.bufferCount, self.atrLength
            return


        # 计算指标数值
        self.atrValue = talib.ATR(self.highArray,
                                  self.lowArray,
                                  self.closeArray,
                                  self.atrLength)[-1]

        self.atrArray[0:self.bufferSize - 1] = self.atrArray[1:self.bufferSize]
        self.atrArray[-1] = self.atrValue
        #print 'atr:',self.atrArray[-1],self.atrValue,self.bufferCount

        if self.closeArray[-1] > self.atsvalue:
            if self.closeArray[-2] < self.atsvalue:
                self.atsvalue = self.closeArray[-1] - self.atsfactor * self.atrArray[-1]
            else:
                self.atsvalue = max(self.atsvalue,self.closeArray[-1] - self.atsfactor * self.atrArray[-1])
        else:
            if self.closeArray[-2] > self.atsvalue:
                self.atsvalue = self.closeArray[-1] + self.atsfactor * self.atrArray[-1]
            else:
                self.atsvalue = min(self.atsvalue,self.closeArray[-1] + self.atsfactor * self.atrArray[-1])
        #print 'close:',self.closeArray[-1]
        #print 'atsvalue:',self.atsvalue

        if self.bufferCount < self.bollingLength:
            print "self.bufferCount, self.bollingLength:",self.bufferCount, self.bollingLength
            return

        self.trendMaArray = talib.MA(self.typpArray,self.maLength)
        self.trendMa = self.trendMaArray[-1]
        self.lasttrendMa = self.trendMaArray[-2]
        bbtemp = talib.BBANDS(self.closeArray,self.bollingLength)
        self.upLine = bbtemp[0][-1]
        self.lowLine = bbtemp[2][-1]
        self.midLine = bbtemp[1][-1]
        self.upLineArray[0:self.bufferSize-1] = self.upLineArray[1:self.bufferSize]
        self.upLineArray[-1] = self.upLine

        self.lowLineArray[0:self.bufferSize-1] = self.lowLineArray[1:self.bufferSize]
        self.lowLineArray[-1] = self.lowLine

        self.midLineArray[0:self.bufferSize-1] = self.midLineArray[1:self.bufferSize]
        self.midLineArray[-1] = self.midLine

        self.atrCount += 1

        if self.atrCount < 3:
            return
        # 判断是否要进行交易
        # 当前无仓位
        if self.direction == 0:

            # 均线上穿，轨道在均线上/下，轨道突破前持仓高/低，发出信号
            if self.lasttradetype == 0:
                if self.trendMaArray[-1] > self.trendMaArray[-2] and self.upLineArray[
                    -1] > self.trendMaArray[-1] :
                    # 前一单空单的情况下，发出多单信号
                    self.signal = 1
                elif self.trendMaArray[-1] < self.trendMaArray[-2] and self.lowLineArray[
                    -1] < self.trendMaArray[-1]:
                    # 前一单多单情况下，发出空单信号
                    self.signal = -1
                else:
                    self.signal = 0
            elif self.lasttradetype == 1 :
                if self.trendMaArray[-1] > self.trendMaArray[-2] and self.upLineArray[
                    -1] > self.trendMaArray[-1] and self.upLineArray[-1] > self.intraTradeHigh :
                    # 前一单多单的情况下，发出多单信号
                    self.signal = 1
                elif self.trendMaArray[-1] < self.trendMaArray[-2] and self.lowLineArray[
                    -1] < self.trendMaArray[-1] :
                    #前一单多单情况下，发出空单信号
                    self.signal = -1
                else:
                    self.signal = 0

            elif self.lasttradetype == -1:
                if self.trendMaArray[-1] > self.trendMaArray[-2] and self.upLineArray[
                    -1] > self.trendMaArray[-1] :
                    # 前一单空单的情况下，发出多单信号
                    self.signal = 1
                elif self.trendMaArray[-1] < self.trendMaArray[-2] and self.lowLineArray[
                    -1] < self.trendMaArray[-1] and self.lowLineArray[-1] < self.intraTradeLow :
                    # 前一单空单情况下，发出空单信号
                    self.signal = -1
                else:
                    self.signal = 0

        #self.onAccount()
        print "self.buyresult, self.sellresult:",self.buyresult, self.sellresult
        # 发出状态更新事件
        self.putEvent()
    # ----------------------------------------------------------------------
    def onOrder(self, order):
        """收到委托变化推送（必须由用户继承实现）"""
        print 'orderinfo:'+ order.direction, order.price, order.tradedVolume
        pass

    def onTrade(self, trade):
        """收到成交变化推送（必须由用户继承实现）"""
        if self.direction == 0 :
            tradedirection = trade.direction.encode('utf-8') + '平'
        else :
            tradedirection = trade.direction.encode('utf-8') + '开'

        value = [tradedirection, trade.price, trade.volume, self.intraTradeHigh, self.intraTradeLow, datetime.now(), self.lasttradetype, self.direction]
        sqlcontent = 'insert into ' + self.tablename + '(trade_type,price,volume,intrahigh,intralow,trade_time,lasttradetype,pos) values(%s,%s,%s,%s,%s,%s,%s,%s)'
        #print  '价格：',trade.price
        self.dbCon.insUpdMySqlData(sqlcontent, value,dbFlag=DATABASE_VNPY)
        pass

    '''
    def onPosition(self,position):
        if position.symbol == 'btc':
            self.btcnum = position.position
            #print position.symbol,':',position.position
        if position.symbol == 'cny':
            self.cnynum = position.position
            #print position.symbol,':',position.position
        pass
    '''
    def onPosition(self,position):
        self.positionDict = position


if __name__ == '__main__':
    # ----------------------------------------------------------------------
    # 提供直接双击回测的功能
    # 导入PyQt4的包是为了保证matplotlib使用PyQt4而不是PySide，防止初始化出错
    '''
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
    '''
    conn = pymysql.connect(host='10.10.10.180',user='rw_trading',passwd='Abcd1234',db='dqpt',port=3306)
    cur = conn.cursor()
    backday = 100
    cur.execute('SELECT sequence,opening_price,closing_price,max_price,min_price,volume_quantity,volume_price FROM (SELECT * FROM okcoincn_spot_btc_cny_aggregation_minute1 ORDER BY sequence DESC LIMIT 0,100)  AS total ORDER BY sequence ASC ')
    data = cur.fetchall()
    datalength = len(data)
    h = np.zeros(backday)
    l = np.zeros(backday)
    o = np.zeros(backday)
    c = np.zeros(backday)
    volume = np.zeros(backday)
    date = []
    for i in range(backday):
        o[i] = (data[i][1])
        h[i] = (data[i][3])
        l[i] = (data[i][4])
        c[i] = (data[i][2])
        volume[i] = (data[i][5])
        date.append(data[i][0])
    cur.close()
    conn.close()
#     h = h[::-1]
#     l = l[::-1]
#     c = c[::-1]
#     o = o[::-1]
    atr = talib.ATR(h,l,c,15)
    
    
    
    
    
    
    
    
    
    
    