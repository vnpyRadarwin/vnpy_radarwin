#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time, socket, threading

from vtEngine import MainEngine
from radarwinFunction.rwDbConnection import *
from radarwinFunction.rwConstant import *
def tcplink(sock, addr):
    print 'Accept new connection from %s:%s...' % addr
    sock.send('Welcome!')
    mainEngine = MainEngine()

    while True:
        data = sock.recv(1024)
        time.sleep(1)
        if data == 'exit' or not data:
            break
        mainEngine.ctaEngine.loadSetting()
        mainEngine.ctaEngine.initStrategy(data)
        mainEngine.ctaEngine.startStrategy(data)
        sock.send("SEVER OK")
    sock.close()
    #print 'Connection from %s:%s closed.' % addr


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

dbCon = rwDbConnection()
#SQL = 'SELECT strategy_name as name , port as port FROM strategy_master WHERE flag = 1'
data = dbCon.getMySqlData(GET_STRATEGY_MASTER, dbFlag=DATABASE_VNPY)
stragety=data[0]
# 监听端口:
s.bind((SERVER_HOST, stragety['port']))
#s.bind(('localhost', stragety['port']))
s.listen(5)
print 'Waiting for connection...'

while True:
    # 接受一个新连接:
    sock, addr = s.accept()
    # 创建新线程来处理TCP连接:
    t = threading.Thread(target=tcplink, args=(sock, addr))
    t.start()
