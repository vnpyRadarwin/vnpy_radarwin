#!/usr/bin/env python
# -*- coding: utf-8 -*-

'a socket example which send echo message to server.'

import socket
from radarwinFunction.rwDbConnection import *
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# 建立连接:

dbCon = rwDbConnection()
SQL = 'SELECT strategy_name as name , port as port FROM strategy_master WHERE flag = 1'
data = dbCon.getMySqlData(SQL, dbFlag=DATABASE_VNPY)
stragety=data[0]

s.connect(('172.16.1.128', stragety['port']))
#s.connect(('localhost', stragety['port']))
# 接收欢迎消息:
s.recv(1024)


#for data in stragety['name']:
# 发送数据:
s.send(stragety['name'])
s.recv(1024)

s.send('exit')
s.close()



