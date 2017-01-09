# encoding: UTF-8

"""
包含一些开发中常用的函数
"""
from time import sleep

import requests

TRADE_TYPE_BUY = 'buy'
TRADE_TYPE_SELL = 'sell'
SYMBOL_CNY='cny'
SYMBOL_BTC='btc'


#----------------------------------------------------------------------
# 根据当前账户信息判断是否可买卖
#参数
# params:buy,sell
# positionDict:当前账户信息
# pos:买/卖量
# price：买/卖价格
#返回值：False-》不可交易，True-》可交易
def getPosition(params, positionDict, price, pos):
    if not positionDict:
        return False
    if params == TRADE_TYPE_BUY:
        if SYMBOL_CNY in positionDict:
            posData = positionDict[SYMBOL_CNY]
            if posData.position < pos * price:
                return False
    elif params == TRADE_TYPE_SELL:
        if SYMBOL_BTC in positionDict:
            posData = positionDict[SYMBOL_BTC]
            if posData.position < pos:
                return False
    return True


def getPosition_1(params, positionDict, price, pos):
    if not positionDict:
        return False
    if params == TRADE_TYPE_BUY:
        if SYMBOL_CNY in positionDict:
            posData = positionDict[SYMBOL_CNY]
            if posData< pos * price:
                return False
    elif params == TRADE_TYPE_SELL:
        if SYMBOL_BTC in positionDict:
            posData = positionDict[SYMBOL_BTC]
            if posData< pos:
                return False
    return True
#----------------------------------------------------------------------
# 断线重连机制

#def reConnection(host,paramas=None,style='post',sleepTime=0.5,times=3):
# def reConnection_tick(times,**kwargs):
#     result =None
#     tickError=False
#     print "reConnection_tick start"
#     try:
#         result = requests.post(kwargs['host'])
#     except Exception, e:
#         sleep(kwargs['sleepTime'])
#         times = times - 1
#         if times > 0:
#             reConnection_tick(times,**kwargs)
#         else:
#             print "Tick Data connectin fail"
#             tickError =True
#     print "tickError:",tickError
#     return result,tickError
#
# def reConnection_info(times,**kwargs):
#
#     result =None
#     infoError=False
#     if 'paramas' in kwargs:
#         try:
#             result=requests.post(kwargs['host'],kwargs['paramas'])
#         except Exception, e:
#             sleep(kwargs['sleepTime'])
#             times = times - 1
#             if times > 0:
#                 reConnection_info(times, **kwargs)
#             else:
#                 print "Account Info connectin fail"
#                 infoError = True
#
#     #print error
#     return result,infoError

if __name__ == '__main__':
    result=reConnection_tick(times=3,host='http://api.huobi.coms/staticmarket/ticker_btc_json.js',sleepTime=0.5)
    #print result

 
