# encoding: UTF-8

'''
本文件包含了CTA引擎中的策略开发用模板，开发策略时需要继承CtaTemplate类。
'''

from ctaBase import *
from vtConstant import *
import logging
import numpy as np
import pymysql
import datetime
########################################################################
class CtaTemplate(object):
    """CTA策略模板"""
    
    # 策略类的名称和作者
    className = 'CtaTemplate'
    author = EMPTY_UNICODE
    
    # MongoDB数据库的名称，K线数据库默认为1分钟
    tickDbName = TICK_DB_NAME
    barDbName = MINUTE_DB_NAME

    #mysql数据库参数
    host = EMPTY_STRING
    user = EMPTY_STRING
    passwd = EMPTY_STRING
    db = EMPTY_STRING
    port = EMPTY_INT
    tablename = EMPTY_STRING
    # 策略的基本参数
    name = EMPTY_UNICODE           # 策略实例名称
    vtSymbol = EMPTY_STRING        # 交易的合约vt系统代码    
    productClass = EMPTY_STRING    # 产品类型（只有IB接口需要）
    currency = EMPTY_STRING        # 货币（只有IB接口需要）
    
    # 策略的基本变量，由引擎管理
    inited = False                 # 是否进行了初始化
    trading = False                # 是否启动交易，由引擎管理
    pos = 0                        # 持仓情况
    
    # 参数列表，保存了参数的名称
    paramList = ['name',
                 'className',
                 'author',
                 'vtSymbol']
    
    # 变量列表，保存了变量的名称
    varList = ['inited',
               'trading',
               'pos']
    # ----------------------------------------------------------------------
    # 以下为自定义添加内容，记录log用
    logger = logging.getLogger("loggingmodule.NomalLogger")
    #handler = logging.FileHandler("D:/python_workspace/log/atr_test.log")
    handler = logging.FileHandler("/home/owenpanhao/vnpy_project/log/atr_test.log")
    formatter = logging.Formatter("[%(levelname)s][%(funcName)s][%(asctime)s]%(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    # ----------------------------------------------------------------------
    # 以下为自定义添加内容，读取mysql的配置
    conn = pymysql.connect(host='56533bf41fb88.gz.cdb.myqcloud.com', user='radarwinBitrees', passwd='jDt63iDH72df3',
                           db='bitrees', port=14211)
    cur = conn.cursor()
    #----------------------------------------------------------------------
    def __init__(self, ctaEngine, setting):
        """Constructor"""
        self.ctaEngine = ctaEngine
        # 设置策略的参数
        if setting:
            d = self.__dict__
            for key in self.paramList:
                if key in setting:
                    d[key] = setting[key]
    
    #----------------------------------------------------------------------
    def onInit(self):
        """初始化策略（必须由用户继承实现）"""
        raise NotImplementedError
    
    #----------------------------------------------------------------------
    def onStart(self):
        """启动策略（必须由用户继承实现）"""
        raise NotImplementedError
    
    #----------------------------------------------------------------------
    def onStop(self):
        """停止策略（必须由用户继承实现）"""
        raise NotImplementedError

    #----------------------------------------------------------------------
    def onTick(self, tick):
        """收到行情TICK推送（必须由用户继承实现）"""
        raise NotImplementedError

    #----------------------------------------------------------------------
    def onOrder(self, order):
        """收到委托变化推送（必须由用户继承实现）"""
        raise NotImplementedError
    
    #----------------------------------------------------------------------
    def onTrade(self, trade):
        """收到成交推送（必须由用户继承实现）"""
        raise NotImplementedError
    
    #----------------------------------------------------------------------
    def onBar(self, bar):
        """收到Bar推送（必须由用户继承实现）"""
        raise NotImplementedError
    
    #----------------------------------------------------------------------
    def buy(self, price, volume, stop=False):
        """买开"""
        return self.sendOrder(CTAORDER_BUY, price, volume, stop)
    
    #----------------------------------------------------------------------
    def sell(self, price, volume, stop=False):
        """卖平"""
        return self.sendOrder(CTAORDER_SELL, price, volume, stop)       

    #----------------------------------------------------------------------
    def short(self, price, volume, stop=False):
        """卖开"""
        return self.sendOrder(CTAORDER_SHORT, price, volume, stop)          
 
    #----------------------------------------------------------------------
    def cover(self, price, volume, stop=False):
        """买平"""
        return self.sendOrder(CTAORDER_COVER, price, volume, stop)
        
    #----------------------------------------------------------------------
    def sendOrder(self, orderType, price, volume, stop=False):
        """发送委托"""
        if self.trading:
            # 如果stop为True，则意味着发本地停止单
            if stop:
                vtOrderID = self.ctaEngine.sendStopOrder(self.vtSymbol, orderType, price, volume, self)
            else:
                vtOrderID = self.ctaEngine.sendOrder(self.vtSymbol, orderType, price, volume, self) 
            return vtOrderID
        else:
            # 交易停止时发单返回空字符串
            return ''        
        
    #----------------------------------------------------------------------
    def cancelOrder(self, vtOrderID):
        """撤单"""
        # 如果发单号为空字符串，则不进行后续操作
        if not vtOrderID:
            return
        
        if STOPORDERPREFIX in vtOrderID:
            self.ctaEngine.cancelStopOrder(vtOrderID)
        else:
            self.ctaEngine.cancelOrder(vtOrderID)
    
    #----------------------------------------------------------------------
    def insertTick(self, tick):
        """向数据库中插入tick数据"""
        self.ctaEngine.insertData(self.tickDbName, self.vtSymbol, tick)
    
    #----------------------------------------------------------------------
    def insertBar(self, bar):
        """向数据库中插入bar数据"""
        self.ctaEngine.insertData(self.barDbName, self.vtSymbol, bar)
        
    #----------------------------------------------------------------------
    def loadTick(self, days):
        """读取tick数据"""
        return self.ctaEngine.loadTick(self.tickDbName, self.vtSymbol, days)
    
    #----------------------------------------------------------------------
    def loadBar(self, days):
        """读取bar数据"""
        return self.ctaEngine.loadBar(self.barDbName, self.vtSymbol, days)
    
    #----------------------------------------------------------------------
    def writeCtaLog(self, content):
        """记录CTA日志"""
        content = self.name + ':' + content
        self.ctaEngine.writeCtaLog(content)
        
    #----------------------------------------------------------------------
    def putEvent(self):
        """发出策略状态变化事件"""
        self.ctaEngine.putStrategyEvent(self.name)
    #----------------------------------------------------------------------
    def log(self,info):
        '''记录log'''
        self.logger.info(info)
    # ----------------------------------------------------------------------
    # def loadbitressdata(self,backday):
    #     self.cur.execute(
    #         'SELECT open,high,low,close,volumn,date FROM okcn_btc_cny_1 ORDER BY date DESC LIMIT 1,%d' % backday)
    #     data = self.cur.fetchall()
    #     datalength = len(data)
    #     l = []
    #     if self.cur:
    #         for d in range(datalength)[::-1]:
    #             bar = CtaBarData()
    #             bar.open = data[d][0]
    #             bar.high = data[d][1]
    #             bar.low = data[d][2]
    #             bar.close = data[d][3]
    #             bar.volume = data[d][4]
    #             bar.datetime = data[d][5]
    #             bar.date = data[d][5]
    #             bar.time = data[d][5]
    #             bar.symbol = 'BTC_CNY_SPOT'
    #             bar.vtSymbol = 'BTC_CNY_SPOT'
    #             l.append(bar)
    #     return l

    def getperioddata(self,date,type):
        sqlcontent = 'SELECT high,low,DATE FROM okcn_btc_cny_1  WHERE DATE > '+'\''+str(date)+'\''+' ORDER BY DATE DESC'
        self.cur.execute(sqlcontent)
        data = self.cur.fetchall()
        high = []
        low = []
        date = []
        if self.cur:
            for i in data[::-1]:
                high.append(i[0])
                low.append(i[1])
                date.append(i[2])
        if type == 'high':
            return max(high)
        if type == 'low':
            return min(low)




    def writetradelog2mysql(self,value):
        conn = pymysql.connect(host=self.host,user=self.user,passwd=self.passwd,db=self.db,port=self.port)
        cur = conn.cursor()
        sqlcontent = 'insert into '+self.tablename+'(trade_type,price,volume,intrahigh,intralow,trade_time,lasttradetype,pos) values(%s,%s,%s,%s,%s,%s,%s,%s)'
        cur.execute(sqlcontent,value)
        conn.commit()
        cur.close()
        conn.close()

    def readtradelog2mysql(self):
        conn = pymysql.connect(host=self.host,user=self.user,passwd=self.passwd,db=self.db,port=self.port)
        cur = conn.cursor()
        sqlcontent = 'select * from ' + self.tablename + ' order by order_id desc limit 0,1'
        cur.execute(sqlcontent)
        data = cur.fetchall()
        cur.close()
        conn.close()
        return  data

# if __name__ == '__main__':
#     conn = pymysql.connect(host='localhost', user='root', passwd='root', db='tradelog', port=3306)
#     cur = conn.cursor()
#     sqlcontent = 'select * from ' + 'okcoin_ltc' + ' order by order_id desc limit 0,1'
#     cur.execute(sqlcontent)
#     data = cur.fetchall()
#     cur.close()
#     conn.close()