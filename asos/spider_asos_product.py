# -*- coding: UTF-8 -*-
from __future__ import division
import sys

sys.path.append("..")
import re
from json import *
from db.dbconnecter import get_param_conn
from db.daos import ProductUrlsDao, ProductDao, ProductDescDao, ProductImagesDao, ProductSkuDao
from db.models import DBParams, Product, ProductImages, ProductSku
from netvisiter.net_openner import NetOpener
from bs4 import BeautifulSoup


def save_product(p_data, pdao, source_url, brand):
    product = Product()
    product.name = p_data['name']
    product.brand = brand
    product.gender = p_data['gender'].lower() == "women" and "1" or "2"
    categories = p_data['categories']
    if len(categories) > 0:
        cat = categories[len(categories) - 1]
        product.category = cat['friendlyName']
    else:
        product.category = ""
        print source_url
    product.status = "1"
    p_images = p_data['images']
    product.images = p_images
    product.color = p_images[0]['colourCode']
    product.code = p_data['productCode']
    product.resource_code = p_data['id']
    product.flag = "013"
    product.url = source_url
    exists_id = pdao.get_id_by_code(product.resource_code)
    if exists_id is not None:
        product.spider_product_id = exists_id
        # pdao.update_product_info(product)
        print "".join([str(exists_id), " is exists!"])
    else:
        product.spider_product_id = pdao.save(product)
    return product


def save_product_desc(page_html, product, pddao):
    soup = BeautifulSoup(page_html, "html.parser")
    desc_div = soup.find("div", class_="product-description")
    if desc_div is not None:
        desc_ul = desc_div.find("ul")
        desc_arr = []
        if desc_ul is not None:
            desc_list = desc_ul.find_all("li")
            for desc in desc_list:
                if desc is not None:
                    desc_arr.append("".join(desc.strings))
        else:
            desc_strs = desc_div.span.strings
            desc_item = None
            for desc_item in desc_strs:
                continue
            if desc_item is not None and len(desc_item) > 0:
                desc_item_arr = desc_item.split("\n")
                for d_item in desc_item_arr:
                    if len(d_item) > 0:
                        temp_item = d_item[0: 1] == "-" and d_item[1: len(d_item)] or d_item
                        temp_item = temp_item.strip()
                        if temp_item != "":
                            desc_arr.append(temp_item)
        product.desc = len(desc_arr) > 0 and "\n".join(desc_arr) or ""

        size_descs = soup.find("div", class_="size-and-fit")
        size_descs = size_descs is not None and size_descs.span.strings or None
        product.size_desc = size_descs is not None and "\n".join(size_descs) or ""

        constitute = []
        about_me = soup.find("div", class_="about-me")
        if about_me is not None:
            about_me_strs = about_me.span.strings
            for str_item in about_me_strs:
                constitute.append(str_item.strip())

        care_info = soup.find("div", class_="care-info")
        if care_info is not None:
            care_info_strs = care_info.span.strings
            for str_item in care_info_strs:
                constitute.append(str_item.strip())

        product.constitute = len(constitute) > 0 and "\n".join(constitute) or ""
        product.location = ""
        product.language_id = "2"
        if pddao.is_exists_product_desc(product.spider_product_id, product.language_id):
            # pddao.update_product_desc(product)
            print "".join([str(product.spider_product_id), " desc is exists!"])
        else:
            pddao.save(product)


def save_product_images(product, pidao):
    pimg = ProductImages()
    pimg.spid = product.spider_product_id
    images = product.images
    img_arr = []
    for img in images:
        img_url = "".join([img['url'], "?wid=750"])
        img_arr.append(img_url)
    pimg.images = ",".join(img_arr)
    if pidao.is_exists_product_images(pimg.spid):
        # pidao.update_product_images(pimg)
        print "".join([str(pimg.spid), " images is exists!"])
    else:
        pidao.save(pimg)


def save_product_sku(spid, p_variants, price_variants, psdao):
    psku = ProductSku()
    psku.spid = spid
    for provitem in p_variants:
        p_variant_id = provitem['variantId']
        for priceitem in price_variants:
            price_variant_id = priceitem['variantId']
            if p_variant_id == price_variant_id:
                psku.size = provitem['size']
                curr_price = priceitem['price']['current']['value']
                rrp_price = priceitem['price']['rrp']['value']
                previous_price = priceitem['price']['previous']['value']
                psku.discount_price = curr_price
                if rrp_price == 0 and previous_price == 0:
                    psku.price = curr_price
                else:
                    psku.price = rrp_price or previous_price
                exists_id = psdao.get_id_by_spid_size(psku)
                if exists_id is not None:
                    psku.spider_product_sku_id = exists_id
                    # psdao.update_product_sku(psku)
                    print "".join([str(exists_id), " sku is exists!"])
                else:
                    psdao.save(psku)


def analysis_page_to_product(page_html, url_data, pdao, pidao, pddao, psdao, pudao, opener, brand):
    # test_html = open("C:\\Users\\Administrator\\Desktop\\spidertemp\\asos\\test.html", "w")
    # test_html.write(page_html)
    swc_str = page_html.replace("\\'", "xiaoyinhao")
    view_str = re.findall(r'view\(\'([^\']*)\'', swc_str)
    if view_str is not None and len(view_str) > 0:
        json_str = view_str[0]
        json_str = json_str.replace("xiaoyinhao", "'")
        p_data = JSONDecoder().decode(json_str)
        p_id = p_data['id']
        p_store = p_data['store']
        p_variants = p_data['variants']

        price_url = "".join(
            ["http://www.asos.com/api/product/catalogue/v2/stockprice?productIds=", str(p_id), "&store=", p_store['code'],
             "&currency=EUR"])
        price_page = opener.visit_url(price_url, None)
        price_json = price_page.read()
        price_dist = JSONDecoder().decode(price_json)
        price_variants = price_dist[0]['variants']

        try:
            group_url = "".join(
                ["http://www.asos.com/api/product/catalogue/v2/productgroups/ctl/", str(p_id), "?store=", p_store['code'],
                 "&currency=EUR"])
            group_respone = opener.visit_url(group_url, None)
            group_json = group_respone.read()
            group_dist = JSONDecoder().decode(group_json)
        except Exception as err:
            group_dist = None

        if group_dist is not None:
            group_products = group_dist['products']
            g_id_arr = []
            for g_item in group_products:
                g_id_arr.append(str(g_item['product']['id']))
            if len(g_id_arr) > 0:
                pudao.update_group_ids(",".join(g_id_arr), p_id)

        product = save_product(p_data, pdao, url_data[3], brand)
        save_product_desc(page_html, product, pddao)
        save_product_images(product, pidao)
        save_product_sku(product.spider_product_id, p_variants, price_variants, psdao)
        print(product.spider_product_id)
        return 1
    return 2


def iterate_product_urls():
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
    pdao = ProductDao(conn, cur)
    pddao = ProductDescDao(conn, cur)
    pidao = ProductImagesDao(conn, cur)
    psdao = ProductSkuDao(conn, cur)

    product_urls = pudao.get_need_spider_urls()
    for url_item in product_urls:
        page_response = opener.visit_url(url_item[3], None)
        page_html = page_response.read()
        result = analysis_page_to_product(page_html, url_item, pdao, pidao, pddao, psdao, pudao, opener, url_item[2])
        pudao.sign_spider(url_item[0], result)
    cur.close()
    conn.close()


if __name__ == "__main__":
    iterate_product_urls()
