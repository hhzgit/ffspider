# -*- coding: UTF-8 -*-
from __future__ import division
import sys
defaultencoding = 'utf-8'
if sys.getdefaultencoding() != defaultencoding:
    reload(sys)
    sys.setdefaultencoding(defaultencoding)
sys.path.append("..")
import re
from db.dbconnecter import get_param_conn
from db.daos import ProductDescDao
from db.models import Product, DBParams


def do_trans(ss):
    if ss is None or ss == "":
        return ""
    th1 = re.compile(u'型号：')
    ts = th1.sub(u'模特所穿：', ss)
    th2 = re.compile(u'型号')
    ts = th2.sub(u'模特', ts)
    th3 = re.compile(u'英国S')
    ts = th3.sub(u'UK S', ts)
    return ts


def update_desc():
    db_params = DBParams()
    db_params.host = "172.16.8.147"
    db_params.port = "3306"
    db_params.user = "dba"
    db_params.passwd = "123456"
    db_params.db = "asos"
    conn = get_param_conn(db_params)
    if conn is None:
        print("没有此数据库")
        return False
    cur = conn.cursor()
    pddao = ProductDescDao(conn, cur)

    pdescs = pddao.get_all_zh_desc()

    product = Product()
    for item in pdescs:
        product.spider_product_id = item[0]
        product.name = item[1]
        product.desc = do_trans(item[2])
        product.constitute = item[3]
        product.location = item[4]
        product.size_desc = do_trans(item[5])
        product.language_id = item[7]
        pddao.update_product_desc(product)
        print(product.spider_product_id)


if __name__=="__main__":
    update_desc()
