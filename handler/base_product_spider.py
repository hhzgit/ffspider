# -*- coding: UTF-8 -*-
from __future__ import division
import sys

sys.path.append("..")
import json
from netvisiter.net_openner import NetOpener
from db.dbconnecter import get_param_conn
from db.daos import ProductDao, ProductDescDao, ProductImagesDao, ProductSkuDao
from db.models import DBParams


class BaseProductSpider(object):
    def __init__(self):
        # 初始化数据库参数
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
        self.PDAO = ProductDao(conn, cur)
        self.PDDAO = ProductDescDao(conn, cur)
        self.PIDAO = ProductImagesDao(conn, cur)
        self.PSDAO = ProductSkuDao(conn, cur)

        self.OPENER = None
        self.COOKIEFILE = None
        self.LOGFILE = None

    # 初始化网络访问工具
    def init_opener(self):
        self.OPENER = NetOpener(self.HOSTURL, self.COOKIEFILE)
        self.OPENER.init_cookie()
        self.OPENER.load_cookie()
        self.OPENER.load_opener()

    # 公用日志记录方法
    def log_info(self, info):
        file = open(self.LOGFILE, "a")
        file.write("".join([info, "\n"]))
        file.close()

    # 公用url访问方法
    def do_visit(self, url):
        try:
            rsp = self.OPENER.visit_url(url, None)
            return rsp.read()
        except Exception:
            return self.do_visit(url)

    # 公用json型返回请求解析方法
    def get_json(self, url):
        try:
            rsp = self.do_visit(url)
            return json.loads(rsp)
        except Exception:
            return self.get_json(url)

    # 公用商品信息保存方法
    def save_product(self, product):
        exists_id = self.PDAO.get_id_by_code(product.resource_code)
        # 如果已经存在改商品（已存在相同resource_code的商品），则不做处理。（如果需要更新商品信息，可以调用self.PDAO.update_product_info）
        if exists_id is not None:
            product.spider_product_id = exists_id
            print "".join([str(exists_id), ":", str(product.resource_code), " exists!"])
        else:
            # 保存商品信息
            product.spider_product_id = self.PDAO.save(product)
            print "".join([str(product.spider_product_id)])

    def save_product_desc(self, product):
        # 如果已经存在该商品描述，则不做处理。（如需更新商品描述，可调用 self.PDDAO.update_product_desc）
        if self.PDDAO.is_exists_product_desc(product.spider_product_id, product.language_id):
            print "".join([str(product.spider_product_id), ":", product.language_id, " desc is exists!"])
        else:
            # 保存商品描述信息
            self.PDDAO.save(product)

    def save_product_images(self, pimg):
        # 如果已经存在该商品图片信息，则不做处理
        if self.PIDAO.is_exists_product_images(pimg.spid):
            print "".join([str(pimg.spid), " images exists!"])
        else:
            # 保存商品图片信息
            self.PIDAO.save(pimg)

    def save_product_skus(self, psku):
        # 如果已经存在该商品尺码信息，则不做处理
        if self.PSDAO.get_id_by_spid_size(psku) is not None:
            print "".join([str(psku.spid), ":", str(psku.size), " size is exists!"])
        else:
            # 保存商品尺码信息
            self.PSDAO.save(psku)
