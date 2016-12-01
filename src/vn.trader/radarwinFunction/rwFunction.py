# encoding: UTF-8

"""
包含一些开发中常用的函数
"""

import os
import json
#----------------------------------------------------------------------
def loadMySqlSetting():
    """载入MySqlDB数据库的配置"""
    fileName = 'RW_setting.json'
    path = os.path.abspath(os.path.dirname(__file__)) 
    fileName = os.path.join(path, fileName)  
    
    try:
        f = file(fileName)
        setting = json.load(f)
        host = setting['host']
        userName = setting['userName']
        password = setting['password']
        db = setting['db']
        port = setting['port']
    except:
        host = '172.16.1.116'
        userName = 'rw_dqpt'
        password = 'Abcd1234'
        db = 'dqpt'
        port = 3306
        
    return host, userName,password,db,port



 
