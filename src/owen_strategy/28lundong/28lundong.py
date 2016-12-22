#encoding:utf-8

#######################
#策略名：28轮动策略
#策略对象：上证50ETF【510050】，中证500ETF【510500】
#策略概要：根据20天的涨幅，选取涨幅高的持有，如果都为负的，选择空仓
#######################
import tushare as ts
import datetime
from pandas import DataFrame,Series
import vtPath
from itchat import *

class lundong28(object):
    def __init__(self):
        self.symbolList=['510050','510500']
        self.trueDay=20
        self.falseDay=35
        self.dToday=datetime.date.today()
        self.sToday=self.dToday.strftime('%Y-%m-%d')



    def strategy(self):
        dStartDate=self.dToday+datetime.timedelta(days=-self.falseDay)
        dEndDate = self.dToday + datetime.timedelta(days=-1)
        sStartDate=dStartDate.strftime('%Y-%m-%d')
        sEndDate=dEndDate.strftime('%Y-%m-%d')
        sz50hisList=ts.get_k_data(self.symbolList[0],start=sStartDate,end=sEndDate,ktype='D',retry_count=3,pause=1).sort_values(by='date', ascending=False)
        zz500hisList= ts.get_k_data(self.symbolList[1], start=sStartDate, end=sEndDate, ktype='D', retry_count=3, pause=1).sort_values(by='date', ascending=False)
        sz50tickList=ts.get_today_ticks(self.symbolList[0],3,1)
        zz500tickList = ts.get_today_ticks(self.symbolList[1], 3, 1)

        sz50hisDate=sz50hisList.iloc[self.trueDay-1]['close']
        sz50tickDate=sz50tickList.iloc[0]['price']

        zz500hisDate = zz500hisList.iloc[self.trueDay - 1]['close']
        zz500tickDate = zz500tickList.iloc[0]['price']

        sz50Bias=(sz50tickDate-sz50hisDate)/sz50hisDate
        zz500Bias=(zz500tickDate-zz500hisDate)/zz500hisDate

        if sz50Bias>=zz500Bias and sz50Bias>0:
            print "sz50Bias"
        elif zz500Bias>sz50Bias and zz500Bias>0:
            print 'zz500Bias'
        else:
            print 'kongcang'
        send_msg("zz500Bias")

        #sz50hisClose1 = sz50hisList.sort_values(by='date', ascending=False)[self.trueDay - 2:self.trueDay-1]['close']
        datee=sz50hisDate/sz50tickDate
        print datee

if __name__=='__main__':
    stantanc=lundong28()
    stantanc.strategy()




