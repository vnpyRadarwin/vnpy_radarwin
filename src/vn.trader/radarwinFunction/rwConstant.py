# encoding: UTF-8

#数据库来源分类
DATABASE_DQPT='DQPT'
DATABASE_VNPY='VNPY'
DATABASE_CLOUD='CLOUD'
DATABASE_RW_TRADING='RW_TRADING'

#--------------------------------------------------------------
#火币网接口
TRADE_TYPE_LIMIT_BUY = u'限价买'
TRADE_TYPE_LIMIT_SELL = u'限价卖'
TRADE_TYPE_MARKET_BUY = u'市价买'
TRADE_TYPE_MARKET_SELL = u'市价卖'

ORDER_TYPE_BUY = u'买'
ORDER_TYPE_SELL = u'卖'

EXCHANGE_HUOBI='HUOBI'     # HUOBI比特币交易所

#每个交易所对应的可交易对象以及货币类型
EXCHANGE_SYMBOL={'OKCOIN':['BTC','CNY'],
                'HUOBI':['BTC','CNY']
                }

SERVER_HOST='172.16.1.128'
#log输出文件名
#LOGGER_FILE_NAME = '/home/owenpanhao/vnpy_project/log/atr_test_1.log'
LOGGER_FILE_NAME = 'D:\\python_workspace\\log\\atr_test.log'

CONNECTION_MARK='_'

#SQL
#---------------------------------------------------------------------------
GET_STRATEGY_MASTER = 'SELECT sm.strategy_name as name , sm.strategy_class as className,sai.symbol as vtSymbol,ai.exchange_name as exchange_name FROM strategy_master sm,' \
                      'strategy_account_info sai,account_info ai WHERE sm.strategy_id = sai.strategy_id and sai.account_id = ai.account_id and sm.flag = 1'

GET_ACCOUNT_INFO = 'SELECT ai.api_key as apiKey,ai.secret_key as secretKey,ai.password as password FROM account_info ai WHERE ai.exchange_name=%s and ai.flag = 1'