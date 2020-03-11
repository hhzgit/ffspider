# -*- coding: UTF-8 -*-
from __future__ import division
import sys

sys.path.append("..")
from netvisiter.net_openner import NetOpener
from db.dbconnecter import get_param_conn
from db.daos import ProductUrlDao
from db.models import DBParams


class BaseUrlSpider(object):
    def __init__(self):
        # 初始化数据库配置
        db_params = DBParams()
        db_params.host = "172.16.8.147"
        db_params.port = "3306"
        db_params.user = "dba"
        db_params.passwd = "123456"
        db_params.db = "spider2"
        conn = get_param_conn(db_params)
        if conn is None:
            print("没有此数据库")
            return False
        cur = conn.cursor()
        self.PUDAO = ProductUrlDao(conn, cur)

        self.HOSTURL = None
        self.COOKIEFILE = None
        self.LOGFILE = None

    # 公用日志记录方法
    def log_info(self, info):
        file = open(self.LOGFILE, "a")
        file.write("".join([info, "\n"]))
        file.close()

    # 初始化网络访问工具
    def init_opener(self):
        self.OPENER = NetOpener(self.HOSTURL, self.COOKIEFILE)
        self.OPENER.init_cookie()
        self.OPENER.load_cookie()
        self.OPENER.load_opener()

    # 访问url
    def do_visit(self, url):
        try:
            rsp = self.OPENER.visit_url(url, None)
            return rsp.read()
        except Exception:
            return self.do_visit(url)

    # 保存商品url
    def save_url(self, pu):
        if self.PUDAO.is_exists_product_url(pu.source_code):
            print "".join([str(pu.source_code), " is exists!"])
        else:
            self.PUDAO.save(pu)
            print "".join([str(pu.source_code), " saved!"])
