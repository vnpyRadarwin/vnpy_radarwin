# encoding: UTF-8
import logging
from rwConstant import *
class rwLoggerFunction(object):

    def __init__(self):
        self.logger=logging.getLogger('loggingmodule.NomalLogger')
        handler = logging.FileHandler(LOGGER_FILE_NAME)
        # handler = logging.FileHandler("/home/owenpanhao/vnpy_src/log/atr_test.log")
        formatter = logging.Formatter("[%(levelname)s][%(funcName)s][%(asctime)s]%(message)s")
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.DEBUG)

    def setInfoLog(self,info):
        self.logger.info(info)