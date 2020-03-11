# -*- coding: UTF-8 -*-
from __future__ import division
import sys

sys.path.append("..")
import re
import json
from db.dbconnecter import get_param_conn
from db.daos import ProductDao, ProductSkuDao
from db.models import DBParams, ProductSku
from netvisiter.net_openner import NetOpener
import time


PDAO = None
PSDAO = None
OPENER = None


def init_daos():
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
    global PDAO
    global PSDAO
    PDAO = ProductDao(conn, cur)
    PSDAO = ProductSkuDao(conn, cur)


def init_opener():
    global OPENER
    OPENER = NetOpener("http://www.asos.com/women/", "asos_cookie.txt")
    OPENER.init_cookie()
    OPENER.load_cookie()
    OPENER.load_opener()


def update_size_info(spid, sizes, prices):
    global PSDAO
    for size in sizes:
        for price in prices:
            if size["variantId"] == price["variantId"]:
                if not price["isInStock"]:
                    PSDAO.set_sku_out_of_stock(spid, size["size"])
                    print "".join([str(spid), ":", str(size["size"])])
                else:
                    psku = ProductSku()
                    psku.spid = spid
                    psku.size = size['size']
                    curr_price = price['price']['current']['value']
                    rrp_price = price['price']['rrp']['value']
                    previous_price = price['price']['previous']['value']
                    psku.discount_price = curr_price
                    if rrp_price == 0 and previous_price == 0:
                        psku.price = curr_price
                    else:
                        psku.price = rrp_price or previous_price
                    exists_id = PSDAO.get_id_by_spid_size(psku)
                    if exists_id is not None:
                        psku.spider_product_sku_id = exists_id
                        PSDAO.update_product_sku(psku)
                        print "".join([str(spid), ":", str(psku.spider_product_sku_id), ":", psku.size, ":", str(psku.price)])


def do_visit(url):
    try:
        global OPENER
        return OPENER.visit_url(url, None).read()
    except Exception:
        return do_visit(url)


def do_update():
    init_daos()
    init_opener()
    global PDAO
    global PSDAO

    products = PDAO.get_need_update_products_by_site("asos")
    for product in products:
        spid = product[0]
        pgct = do_visit(product[10])
        size_arr = re.findall(r'"variants":([^\]]*\])', pgct)
        if len(size_arr) == 0:
            PSDAO.set_skus_out_of_stock_by_spid(spid)
            continue
        store_str = re.findall(r'"store":(\{[^\}]*\})', pgct)
        store = json.loads(store_str[0])
        price_url = "".join(
            ["http://www.asos.com/api/product/catalogue/v2/stockprice?productIds=", str(product[9]), "&store=",
             store['code'],
             "&currency=EUR"])
        price_page = do_visit(price_url)
        price_dist = json.loads(price_page)
        prices = price_dist[0]['variants']
        size_desc = size_arr[0]
        sizes = json.loads(size_desc)
        update_size_info(spid, sizes, prices)


if __name__ == "__main__":
    do_update()