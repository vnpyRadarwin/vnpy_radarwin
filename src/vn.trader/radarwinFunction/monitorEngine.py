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


########################################################################
class MonitorEngine(object):
    """CTA策略引擎"""
    EVENT_MONITOR='eMonitor'
    PRICE_DIFFERENC=3

    #----------------------------------------------------------------------
    def __init__(self, mainEngine, eventEngine):
        """Constructor"""
        self.mainEngine = mainEngine
        self.eventEngine = eventEngine
        self.tickDict={}
        self.messageFlag=True
        
        # 注册事件监听
        self.registerEvent()
        #self.reqThread = Thread(target=self.processQueue)
        #self.reqThread.start()


    #----------------------------------------------------------------------
    def processTickEvent(self, event):
        """处理行情推送"""

        tick = event.dict_['data']
        # 收到tick行情后，先处理本地停止单（检查是否要立即发出）
        self.tickDict[tick.gatewayName]=tick.lastPrice
        event = Event(type_=self.EVENT_MONITOR)
        event.dict_['data'] = self.tickDict
        self.eventEngine.put(event)
        #print "processTickEvent:",self.tickDict
        self.orderCondition = Condition()

    #----------------------------------------------------------------------
    def registerEvent(self):
        """注册事件监听"""
        self.eventEngine.register(EVENT_TICK, self.processTickEvent)
        self.eventEngine.register(self.EVENT_MONITOR, self.processQueue)

    def processQueue(self,event):

        tick=event.dict_['data']
        if 'HUOBI' in tick and 'OKCOIN' in tick:

            if abs(tick['HUOBI']-tick['OKCOIN']) > self.PRICE_DIFFERENC:
                print "yes:",abs(tick['HUOBI'] - tick['OKCOIN'])
                if self.messageFlag:
                    sendMessage="套利执行："+str(abs(tick['HUOBI']-tick['OKCOIN']))
                    send_msg(sendMessage)
                    self.messageFlag=False
            else:
                self.messageFlag = True
                print 'no:',abs(tick['HUOBI'] - tick['OKCOIN'])

        #print "processQueue:",tick['HUOBI'],tick['OKCOIN']




class Event:
    """事件对象"""

#----------------------------------------------------------------------
    def __init__(self, type_=None):
        """Constructor"""
        self.type_ = type_      # 事件类型
        self.dict_ = {}         # 字典用于保存具体的事件数据

#----------------------------------------------------------------------
 

        
    
    


