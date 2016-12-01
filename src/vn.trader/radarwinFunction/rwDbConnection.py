# encoding: UTF-8

from  rwConstant import *
import pymysql


class rwDbConnection(object):

    def __init__(self):

        self.config_dqpt = {
            'host': '172.16.1.116',
            'user': 'rw_dqpt',
            'password': 'Abcd1234',
            'db': 'dqpt',
            'port': 3306,
            'charset': 'utf8mb4',
            'cursorclass': pymysql.cursors.DictCursor
        }

        self.config_tradelog = {
            'host': '172.16.1.116',
            'port': 3306,
            'user': 'rw_vnpy',
            'password': 'Abcd1234',
            'db': 'vnpy',
            'charset': 'utf8mb4',
            'cursorclass': pymysql.cursors.DictCursor
        }

        self.config_cloud = {
            "host": '56533bf41fb88.gz.cdb.myqcloud.com',
            "user": 'radarwinBitrees',
            "password": 'jDt63iDH72df3',
            "db": 'bitrees',
            "port": 14211,
            'charset': 'utf8mb4',
            'cursorclass': pymysql.cursors.DictCursor
        }

    # ----------------------------------------------------------------------
    def getMySqlData(self,query,params,dbFlag=DATABASE_DQPT):

        if dbFlag == DATABASE_TRADER:
            conn = pymysql.connect(**self.config_tradelog)
        elif dbFlag == DATABASE_CLOUD:
            conn = pymysql.connect(**self.config_cloud)
        else:
            conn = pymysql.connect(**self.config_dqpt)
        try:
            with conn.cursor() as cur:
                cur.execute(query,params)
                data = cur.fetchall()
                return data
        finally:
            conn.close()


    # ----------------------------------------------------------------------
    def insUpdMySqlData(self, query, params, dbFlag=DATABASE_DQPT):
        if dbFlag == DATABASE_TRADER:
            conn = pymysql.connect(**self.config_tradelog)
        elif dbFlag == DATABASE_CLOUD:
            conn = pymysql.connect(**self.config_cloud)
        else:
            conn = pymysql.connect(**self.config_dqpt)
        try:
            with conn.cursor() as cur:
                cur.execute(query,params)
                conn.commit()
        finally:
            conn.close()



if __name__== '__main__':
    #SQL='SELECT open,high,low,close,volumn,date FROM okcn_btc_cny_1 ORDER BY date DESC LIMIT 1,%s'
    SQL='INSERT INTO VN_PY_TEST (Open,High,Low,Close,TotalVolume) Values(%s,%s,%s,%s,%s)'
    params=['1000','2000','3000','4000','5001']
    dbCon=rwDbConnection()
    data= dbCon.insUpdMySqlData(SQL,params)
    print data


