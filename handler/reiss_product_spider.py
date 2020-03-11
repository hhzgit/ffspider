# -*- coding: UTF-8 -*-
from __future__ import division
import sys

sys.path.append("..")
import re
import json
from base_product_spider import BaseProductSpider
from db.models import Product, ProductImages, ProductSku


class ReissProductSpider(BaseProductSpider):
    def __init__(self):
        BaseProductSpider.__init__(self)
        self.HOSTURL = "https://www.reiss.com"
        self.COOKIEFILE = "reiss_cookie.txt"
        self.init_opener()
        self.LOGFILE = "./log/reiss_log.txt"

    # 解析商品描述
    def get_desc_str(self, source_str):
        # 去掉 html 代码
        temp_str = re.sub(r'<[^>]*>', '', source_str)
        # 替换html 空格
        temp_str = temp_str.replace('&nbsp;', " ")
        # 以换行切割
        temp_str_arr = temp_str.split("\n")
        new_temp_arr = []
        for item in temp_str_arr:
            # 去空
            temp_item = item.strip()
            if len(temp_item) > 0:
                new_temp_arr.append(temp_item)
        if len(new_temp_arr) > 0:
            # 以换行拼接
            return "\n".join(new_temp_arr)
        return ""

    # 解析商品信息
    def ana_product_info(self, product, pg):
        # 商品信息在 window["dataLayer"] 中
        pinfo_str_arr = re.findall(r'window\["dataLayer"\]=([^<]*)', pg)
        # 没有商品信息视为爬取失败
        if len(pinfo_str_arr) == 0:
            return False
        pinfo_str = str(pinfo_str_arr[0])
        pinfo_str = pinfo_str[0:len(pinfo_str) - 1]
        # 将商品信息封装成json格式
        pinfo = json.loads(pinfo_str)
        rname = pinfo['reiss.product.name']
        rname_arr = rname.split(' - ')
        # 品牌
        product.brand = "Reiss"
        # 名称
        product.name = "".join(["'", rname_arr[0], "'", " ", pinfo['reiss.product.short_description']])
        # 站点对商品唯一编码
        product.resource_code = pinfo['reiss.product.code']
        # 品牌对商品唯一编码
        product.code = product.resource_code
        # 分类
        if pinfo.has_key('reiss.product.category'):
            product.category = pinfo['reiss.product.category']
        # 颜色
        product.color = pinfo['reiss.product.color']
        # 性别 w 开头为女士 m 开头为男士
        gender_str = pinfo['reiss.product.gender']
        product.gender = gender_str.lower() == "w" and 1 or 2
        # 描述
        desc_half_pg = pg.split('<div id="design" class="accordion__content collapse text--left " role="tabpanel">')[1]
        desc_str_arr = desc_half_pg.split('</div>')
        product.desc = self.get_desc_str(desc_str_arr[0])
        # 成分护理信息
        constitute_half_pg = pg.split('<div id="care" class="accordion__content collapse text--left" role="tabpanel">')[1]
        constitute_str_arr = constitute_half_pg.split("</div>")
        product.constitute = self.get_desc_str(constitute_str_arr[0])
        # 图片
        product.images = pinfo['reiss.product.images']
        # 价格
        product.price = pinfo['reiss.product.price']
        # 币种
        product.currency = pinfo['reiss.basket.currency']
        return True

    # 解析并保存商品sku信息
    def ana_and_save_product_sku(self, psku, product, page):
        psku.spid = product.spider_product_id
        # 尺码信息
        size_arr = re.findall(r'<span class="radio-squared__num[^>]*>([^<]*)', page)
        # 库存信息
        stock_arr = re.findall(r'<link itemprop="availability" href="([^"]*)', page)
        # 折扣价等于当前售价
        psku.discount_price = product.price
        # 币种
        psku.currency = product.currency
        # 原价
        og_price_str = re.findall(r'<span class="product__price--old inline--block">([^<]*)', page)
        if len(og_price_str) > 0:
            og_price = str(og_price_str[0])
            og_price = og_price.replace("£", "")
            psku.price = og_price
        else:
            # 没有原价的，取售价
            psku.price = psku.discount_price
        len_num = len(size_arr)
        if len_num > 0:
            for idx in range(len_num):
                stock_str = stock_arr[idx]
                # OutOfStock 的是售罄商品
                if "OutOfStock" in stock_str:
                    continue
                psku.size = size_arr[idx]
                self.save_product_skus(psku)
        else:
            # 记录没有sku的商品
            tipstr = "".join([str(product.spider_product_id), " no sku find!"])
            print tipstr
            self.log_info(tipstr)

    # 爬取商品
    def grab_product(self, flag, url):
        product = Product()
        # 来源
        product.flag = flag
        # 源链接
        product.url = url
        # 状态正常
        product.status = "1"
        # 英语
        product.language_id = "2"

        pg = self.do_visit(url)
        # 解析商品信息
        if self.ana_product_info(product, pg):
            # 保存商品信息
            self.save_product(product)
            # 保存描述信息
            self.save_product_desc(product)
            pimg = ProductImages()
            pimg.spid = product.spider_product_id
            img_arr = []
            if len(product.images) > 0:
                for img in product.images:
                    # -20后缀结束的图片不是需要的图片
                    if "-20." in img:
                        continue
                    img_arr.append(img)
                pimg.images = ",".join(img_arr)
                # 保存图片信息
                self.save_product_images(pimg)
            else:
                # 记录没有图片的商品
                self.log_info("".join([str(pimg.spid), " no images!"]))
            psku = ProductSku()
            # 解析并保存sku信息
            self.ana_and_save_product_sku(psku, product, pg)
        else:
            self.log_info("".join([url, " product not saved!"]))



if __name__ == "__main__":
        nps = ReissProductSpider()
        nps.grab_product("020", "https://www.reiss.com/p/ruffle-front-blouse-womens-goldie-in-merlot-red/?category_id=1122")