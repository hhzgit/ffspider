# -*- coding: UTF-8 -*-
import pymysql


def get_conn():
    return pymysql.connect(host='172.16.8.147', port=3306, user='dba', passwd='123456', db='asos', charset='utf8mb4')


def get_param_conn(params):
    return pymysql.connect(host=params.host, port=int(params.port), user=params.user, passwd=params.passwd, db=params.db, charset='utf8mb4')


if __name__ == "__main__":
    print(get_conn())
