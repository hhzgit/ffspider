# -*- coding: UTF-8 -*-
from __future__ import division
import sys

sys.path.append("..")
import re
import math
from db.dbconnecter import get_param_conn
from db.daos import ProductUrlsDao
from db.models import DBParams,ProductUrls
from netvisiter.net_openner import NetOpener


def get_spider_brand_urls():
    opener = NetOpener("http://www.asos.com", "asos_cookie.txt")
    # opener.init_cookie()
    opener.load_cookie()
    opener.load_opener()

    brand_file = open("C:\\Users\\Administrator\\Desktop\\spidertemp\\asos\\asos_brands_men.txt", "r")
    brand_url_file = open("C:\\Users\\Administrator\\Desktop\\spidertemp\\asos\\brand_urls_men.txt", "a")
    brands = brand_file.readlines()

    page_response = opener.visit_url("http://www.asos.com/men/a-to-z-of-brands/cat/?cid=1361", None)
    page_html = page_response.read().lower()
    # test_html = open("C:\\Users\\Administrator\\Desktop\\spidertemp\\asos\\test.html", "w")
    # test_html.write(page_html)

    for brand in brands:
        brand_str = brand.strip().lower()
        r_str = "".join(['href="(http://www.asos.com/[^"]*)"[^<]*', brand_str, "[^<]*<"])
        match_strs = re.findall(r_str, page_html)
        match_strs = len(match_strs) > 0 and (",".join(str(match_item) for match_item in match_strs)) or ""
        brand_url_file.write("".join([brand.strip(), "|", match_strs, "\n"]))


def save_product_urls(brand, page_html, pudao):
    product_urls_arr = re.findall(r'<a class="product product-link " href="([^"]*)"', page_html)
    purls = ProductUrls()
    for url in product_urls_arr:
        asos_id_str_arr = re.findall(r'prd/([0-9]*)?', url)
        if len(asos_id_str_arr) > 0:
            purls.asos_id = asos_id_str_arr[0]
            if pudao.exist_product(purls.asos_id):
                continue
            purls.product_url = url
            purls.brand = brand
            purls.is_spider = "0"
            pudao.save(purls)
            print "".join([brand, ":", str(purls.asos_id)])
        else:
            print url
            continue


def get_spider_product_urls():
    opener = NetOpener("http://www.asos.com", "asos_cookie.txt")
    opener.init_cookie()
    opener.load_cookie()
    opener.load_opener()

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
    pudao = ProductUrlsDao(conn, cur)

    brand_url_file = open("C:\\Users\\Administrator\\Desktop\\spidertemp\\asos\\brand_urls_20171010.txt", "r")
    brand_urls = brand_url_file.readlines()
    for url_str in brand_urls:
        url_item_arr = url_str.split("|")
        brand_name = url_item_arr[0].strip()
        url = url_item_arr[1].strip()
        page_response = opener.visit_url(url, None)
        page_html = page_response.read()
        save_product_urls(brand_name, page_html, pudao)
        # test_html = open("C:\\Users\\Administrator\\Desktop\\spidertemp\\asos\\test.html", "w")
        # test_html.write(page_html)
        styles_num = int(re.findall(r'<span data-bind="text: formatedNumber" class="total-results">([0-9|,]*)</span>', page_html)[0].replace(",", ""))
        pages_num = int(math.ceil(styles_num/36))
        if pages_num > 1:
            for i in range(1, pages_num):
                page_url = "".join([url, "&pge=", str(i), "&pgesize=36"])
                page_response = opener.visit_url(page_url, None)
                page_html = page_response.read()
                save_product_urls(brand_name, page_html, pudao)

    cur.close()
    conn.close()


if __name__=="__main__":
    # get_spider_brand_urls()
    get_spider_product_urls()