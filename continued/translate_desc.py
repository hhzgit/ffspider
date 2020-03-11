# -*- coding: UTF-8 -*-
from __future__ import division
import sys
defaultencoding = 'utf-8'
if sys.getdefaultencoding() != defaultencoding:
    reload(sys)
    sys.setdefaultencoding(defaultencoding)
sys.path.append("..")
from tools.translate import GGTranslater
from db.dbconnecter import get_param_conn
from db.daos import ProductDescDao
from db.models import Product, DBParams


def translate_desc():
    # 初始化数据库连接
    db_params = DBParams()
    db_params.host = "172.16.8.149"
    db_params.port = "3306"
    db_params.user = "dba"
    db_params.passwd = "123456"
    db_params.db = "test"
    conn = get_param_conn(db_params)
    if conn is None:
        print("没有此数据库")
        return False
    cur = conn.cursor()
    pddao = ProductDescDao(conn, cur)

    # 初始化Google翻译工具
    gg_translater = GGTranslater()

    # 获取需要翻译的商品描述
    need_trans_pds = pddao.get_en_desc_no_zh()
    for item in need_trans_pds:
        product = Product()
        product.spider_product_id = item[0]
        product.language_id = 1
        # 已经有中文翻译的，不再翻译
        if pddao.is_exists_product_desc(product.spider_product_id, product.language_id):
            print "".join([str(product.spider_product_id), " exists!"])
            continue
        # 翻译商品名
        pname = item[1]
        if pname and pname != "":
            product.name = gg_translater.en_to_zh(pname)
        # 翻译描述
        pdesc = item[2]
        if pdesc and pdesc != "":
            product.desc = gg_translater.en_to_zh(pdesc)
        # 翻译材质
        pconstitue = item[3]
        if pconstitue and pconstitue != "":
            product.constitute = gg_translater.en_to_zh(pconstitue)
        # 翻译尺码描述
        psizedesc = item[5]
        if psizedesc and psizedesc != "":
            product.size_desc = gg_translater.en_to_zh(psizedesc)
        # 翻译完成，存库
        pddao.save(product)
        print str(product.spider_product_id)


def do_trans():
    try:
        translate_desc()
    except Exception:
        do_trans()


if __name__=="__main__":
    do_trans()
