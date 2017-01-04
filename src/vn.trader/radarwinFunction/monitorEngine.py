# encoding: UTF-8

'''
本文件中实现了CTA策略引擎，针对CTA类型的策略，抽象简化了部分底层接口的功能。

关于平今和平昨规则：
1. 普通的平仓OFFSET_CLOSET等于平昨OFFSET_CLOSEYESTERDAY
2. 只有上期所的品种需要考虑平今和平昨的区别
3. 当上期所的期货有今仓时，调用Sell和Cover会使用OFFSET_CLOSETODAY，否则
   会使用OFFSET_CLOSE
4. 以上设计意味着如果Sell和Cover的数量超过今日持仓量时，会导致出错（即用户
   希望通过一个指令同时平今和平昨）
5. 采用以上设计的原因是考虑到vn.trader的用户主要是对TB、MC和金字塔类的平台
   感到功能不足的用户（即希望更高频的交易），交易策略不应该出现4中所述的情况
6. 对于想要实现4中所述情况的用户，需要实现一个策略信号引擎和交易委托引擎分开
   的定制化统结构（没错，得自己写）
'''
from threading import Thread, Condition

from eventEngine import *
from weixinWarning import *
#from rwDbConnection import *
from rwFunction import *
from vtGateway import VtSubscribeReq, VtOrderReq, VtCancelOrderReq, VtLogData
from vtConstant import *

########################################################################
class MonitorEngine(object):
    """CTA策略引擎"""
    PRICE_DIFFERENC=2

    #----------------------------------------------------------------------
    def __init__(self, mainEngine, eventEngine,gatewayName_1,gatewayName_2):
        """Constructor"""
        self.mainEngine = mainEngine
        self.eventEngine = eventEngine
        self.tickDict={}
        self.signalDict={}
        self.positionDict_huobi={}
        self.positionDict_okcoin={}
        self.messageFlag=True
        #self.dbCon = rwDbConnection()
        self.gatewayName_1 = gatewayName_1
        self.gatewayName_2 = gatewayName_2
        self.registerEvent()
        self.lots=0.01



    # ----------------------------------------------------------------------
    # def strategyStart(self):
    #     # 注册事件监听
    #     self.registerEvent()
    #----------------------------------------------------------------------
    def __processTickEvent(self, event):
        """处理行情推送"""

        tick = event.dict_['data']
        # 收到tick行情后，先处理本地停止单（检查是否要立即发出）
        self.tickDict[tick.gatewayName]=tick.lastPrice

        if self.gatewayName_1 in self.tickDict and self.gatewayName_2 in self.tickDict:
            self.weixinPost()


    #----------------------------------------------------------------------
    def registerEvent(self):
        # data = self.dbCon.getMySqlData(GET_STRATEGY_MASTER, dbFlag=DATABASE_VNPY)
        # for d in data:
        #     if d['name'] <> 'price_different_test':
        #         return
        """注册事件监听"""
        self.eventEngine.register(EVENT_TICK, self.__processTickEvent)
        self.eventEngine.register(EVENT_POSITION + self.gatewayName_1, self.__positionEvent_1)
        self.eventEngine.register(EVENT_POSITION + self.gatewayName_2, self.__positionEvent_2)

    def weixinPost(self):
        if abs(self.tickDict[self.gatewayName_1] - self.tickDict[self.gatewayName_2]) > self.PRICE_DIFFERENC:

            #print "yes:", self.tickDict[self.gatewayName_1], self.tickDict[self.gatewayName_2]
            if self.messageFlag:
                sendMessage = "套利执行：" + str(abs(self.tickDict[self.gatewayName_1] - self.tickDict[self.gatewayName_2])) + " 火币：" + str(
                    self.tickDict[self.gatewayName_1]) + " OKCOIN：" + str(self.tickDict[self.gatewayName_2])
                #print sendMessage
                # send_msg(sendMessage)
                self.messageFlag = False
        else:
            self.messageFlag = True
            #print 'no:', self.tickDict[self.gatewayName_1], self.tickDict[self.gatewayName_2]




    def pd_sendOrder(self):
        print "sendOrder"
        if self.gatewayName_1 in self.tickDict and self.gatewayName_2 in self.tickDict:
            if self.tickDict[self.gatewayName_1] > self.tickDict[self.gatewayName_2]:
                sellResult=getPosition("sell",self.positionDict_huobi,self.tickDict[self.gatewayName_1],self.lots)
                buyResult = getPosition("buy", self.positionDict_okcoin, self.tickDict[self.gatewayName_2], self.lots)
                if sellResult and buyResult:
                    req = VtOrderReq()
                    req.symbol="BTC_CNY_SPOT"
                    req.direction=DIRECTION_SHORT
                    req.price=self.tickDict[self.gatewayName_1]-10
                    req.volume=self.lots
                    self.writeLog(u'火币发送委托卖单，%s@%s' % (req.volume, req.price))
                    #print (u'HUOBI发送委托卖单，%s@%s' % (req.volume, req.price))
                    self.mainEngine.sendOrder(req,self.gatewayName_1)
                    req.symbol="BTC_CNY_SPOT"
                    req.direction=DIRECTION_LONG
                    req.priceType = PRICETYPE_LIMITPRICE
                    req.price = self.tickDict[self.gatewayName_2]+10
                    req.volume = self.lots
                    self.writeLog(u'OKCOIN发送委托买单，%s@%s' % (req.volume, req.price))
                    #print (u'OKCOIN发送委托买单，%s@%s' % (req.volume, req.price))
                    self.mainEngine.sendOrder(req, self.gatewayName_2)
                else:
                    if not sellResult:
                        self.writeLog(u'火币账户币不足无法执行卖出单')
                    if not buyResult:
                        self.writeLog(u'OKCOIN账户钱不足无法执行买入单')
            else:
                buyResult = getPosition("buy", self.positionDict_huobi, self.tickDict[self.gatewayName_1], self.lots)
                sellResult = getPosition("sell", self.positionDict_okcoin, self.tickDict[self.gatewayName_2], self.lots)
                if sellResult and buyResult:
                    req = VtOrderReq()
                    req.symbol = "BTC_CNY_SPOT"
                    req.direction = DIRECTION_LONG
                    req.price = self.tickDict[self.gatewayName_1] + 10
                    req.volume = self.lots
                    self.writeLog(u'火币发送委托买单，%s@%s' % (req.volume, req.price))
                    #print (u'HUOBI发送委托买单，%s@%s' % (req.volume, req.price))
                    self.mainEngine.sendOrder(req, self.gatewayName_1)
                    req.symbol = "BTC_CNY_SPOT"
                    req.direction = DIRECTION_SHORT
                    req.priceType = PRICETYPE_LIMITPRICE
                    req.price = self.tickDict[self.gatewayName_2] - 10
                    req.volume = self.lots
                    self.writeLog(u'OKCOIN发送委托卖单，%s@%s' % (req.volume, req.price))
                    #print (u'OKCOIN发送委托卖单，%s@%s' % (req.volume, req.price))
                    self.mainEngine.sendOrder(req, self.gatewayName_2)
                else:
                    if not sellResult:
                        self.writeLog(u'OKCOIN账户币不足无法执行卖出单')
                    if not buyResult:
                        self.writeLog(u'火币账户钱不足无法执行买入单')


    def __positionEvent_1(self,event):
        pos = event.dict_['data']
        self.positionDict_huobi[pos.vtSymbol] = pos

    def __positionEvent_2(self,event):
        pos = event.dict_['data']
        self.positionDict_okcoin[pos.vtSymbol] = pos


    def writeLog(self, content):
        """快速发出日志事件"""
        log = VtLogData()
        log.logContent = content
        event = Event(type_=EVENT_LOG)
        event.dict_['data'] = log
        self.eventEngine.put(event)
class Event:
    """事件对象"""

#----------------------------------------------------------------------
    def __init__(self, type_=None):
        """Constructor"""
        self.type_ = type_      # 事件类型
        self.dict_ = {}         # 字典用于保存具体的事件数据

#----------------------------------------------------------------------
 

        
    
    


