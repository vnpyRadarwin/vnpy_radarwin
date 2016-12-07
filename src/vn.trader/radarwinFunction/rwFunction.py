# encoding: UTF-8

"""
包含一些开发中常用的函数
"""

#----------------------------------------------------------------------
# 根据当前账户信息判断是否可买卖
#参数
# params:buy,sell
# positionDict:当前账户信息
# pos:买/卖量
# price：买/卖价格
#返回值：False-》不可交易，True-》可交易
def getPosition(params, positionDict, pos, price):
    if params == 'buy':
        if 'cny' in positionDict:
            posData = positionDict['cny']
            if posData.position < pos * price:
                return False
    elif params == 'sell':
        if 'btc' in positionDict:
            posData = positionDict['btc']
            if posData.position < pos:
                return False
    return True



 
