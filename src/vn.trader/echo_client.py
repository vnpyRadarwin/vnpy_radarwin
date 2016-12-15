#!/usr/bin/env python
# -*- coding: utf-8 -*-

'a socket example which send echo message to server.'

import socket

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# 建立连接:
#s.connect(('172.16.1.128', 9998))
s.connect(('localhost', 9999))
# 接收欢迎消息:
print s.recv(1024)
for data in ['Bolling']:
    # 发送数据:
    s.send(data)
    print s.recv(1024)
s.send('exit')
s.close()
