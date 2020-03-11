# -*- coding: UTF-8 -*-
from __future__ import division
import sys

sys.path.append("..")
import re
import json
import math
from base_product_spider import BaseProductSpider
from db.models import Product, ProductImages, ProductSku


class NetaporterProductSpider(BaseProductSpider):
    def __init__(self):
        BaseProductSpider.__init__(self)
        self.HOSTURL = "https://www.net-a-porter.com"
        self.COOKIEFILE = "netaporter_cookie.txt"
        self.init_opener()
        self.LOGFILE = "./log/netaporter_log.txt"

    # 解析商品描述
    def get_desc_str(self, source_str):
        # 商品描述信息在<ul class="font-list-copy"></ul> 中
        size_info_arr = source_str.split('<ul class="font-list-copy">')
        if len(size_info_arr) == 1:
            return None
        size_info = size_info_arr[1].split("</ul>")[0].strip()
        # 去掉多余的html代码剩下文字
        size_info = size_info.replace("\t", "")
        size_info = size_info.replace("<li>", "")
        size_info = size_info.replace("</li>", "")
        size_info = size_info.replace("<b>", "")
        size_info = size_info.replace("</b>", "")
        size_info = size_info.replace("<br>", "")
        size_info = re.sub(r'<a id="styling-inspiration-link"[^>]*>[^<]*</a>', "", size_info)
        return size_info

    # 解析商品信息
    def ana_product_info(self, product, pg):
        # 商品信息在 product-data 参数中
        product_info = re.findall(r'<meta class="product-data"([^>]*)', pg)
        # 没有则视为爬取失败
        if len(product_info) == 0:
            return False
        product_info = product_info[0]
        p_sold_out = re.findall(r'data-sold-out="([^"]*)"', product_info)[0]
        # 售罄的不爬
        if p_sold_out == "true":
            return False
        # 品牌
        product.brand = re.findall(r'<span itemprop="name">([^<]*)<', pg)[0]
        # 商品名
        pname = re.findall(r'<h2 class="product-name">([^<]*)<', pg)
        # 没商品名的视为爬取失败
        if len(pname) == 0:
            return False
        product.name = pname[0]
        # 站点对商品的唯一编码
        product.resource_code = re.findall(r'data-pid="([^"]*)"', product_info)[0]
        # 所属分类
        cats_str = re.findall(r'data-breadcrumb-names="([^"]*)"', product_info)[0]
        cats_arr = cats_str.split("/")
        cat_str = cats_arr[len(cats_arr)-1]
        product.category = cat_str.strip()
        # 尺码信息
        temp_arr = pg.split('<div class="show-hide-content">')
        size_desc = self.get_desc_str(temp_arr[1])
        product.size_desc = size_desc
        # 描述信息
        p_desc_str = temp_arr[2].split("</div>")[0]
        p_desc_more = self.get_desc_str(p_desc_str)
        # 没有护理信息的只用描述信息
        if p_desc_more is None:
            p_desc_p = p_desc_str.split("<p>")[1]
            p_desc_p = p_desc_p.split("</p>")[0].strip()
            p_desc = p_desc_p.replace("\t", "")
            p_desc = p_desc.replace("<br>", "")
        else:
            # 有护理信息的拼上护理信息
            p_desc = p_desc_str.split("<br>")[0]
            p_desc = p_desc.split("<br/>")[0]
            p_desc = re.sub(r'<[^>]*>', "", p_desc).strip()
            p_desc = "".join([p_desc, "\n", p_desc_more])
        product.desc = p_desc

        return True

    # 解析商品图片
    def ana_product_images(self, pimg, page):
        # 获取图片列表
        images_arr = re.findall(r'<img class="thumbnail-image" src="([^"]*)"', page)
        temp_arr = []
        if len(images_arr) > 0:
            for img in images_arr:
                temp_img_arr = img.split("_")
                # 取 xl 的大图
                temp_img_arr[len(temp_img_arr) - 1] = "xl.jpg"
                temp_arr.append("".join(["https:", "_".join(temp_img_arr)]))
            pimg.images = ",".join(temp_arr)
        else:
            # 记录没有图片的商品
            self.log_info("".join([str(pimg.spid), " no images!"]))

    # 解析商品sku
    def ana_and_save_product_sku(self, psku, page):
        # 尺码列表
        size_arr = re.findall(r'options="([^"]*)"', page)
        # 价格信息
        priceInfoArr = re.findall(r' price="([^"]*)"', page)
        if len(priceInfoArr) > 0:
            pricetemp = priceInfoArr[0]
            pricetemp = pricetemp.replace("&quot;", "\"")
            # 将价格信息解析成json格式
            pricetemp = json.loads(pricetemp)
            divisor = pricetemp["divisor"]
            # 当前售价
            psku.discount_price = math.ceil(pricetemp["amount"] / divisor)
            # 有原价设置原价
            if pricetemp.has_key("originalAmount"):
                psku.price = math.ceil(pricetemp["originalAmount"] / divisor)
            else:
                # 没有原价则当前售价即为
                psku.price = psku.discount_price
        if len(size_arr) > 0:
            size_desc = size_arr[0]
            size_desc = size_desc.replace("&quot;", "\"")
            sizes = json.loads(size_desc)
            for size in sizes:
                size_data = size["data"]
                stock_str = size_data["stock"]
                # Out_of_Stock 为售罄状态
                if stock_str == "Out_of_Stock":
                    continue
                else:
                    psku.size = size_data["size"]
                    self.save_product_skus(psku)
        else:
            # 没标尺码的是均码商品
            psku.size = "OS"
            self.save_product_skus(psku)

    # 爬取商品
    def grab_product(self, flag, url):
        # 将连接替换成意大利站点（意大利站是欧元价）
        surl = url.replace("/cn/", "/it/")
        pg = self.do_visit(surl)
        product = Product()
        # 来源
        product.flag = flag
        # 源链接
        product.url = surl
        # 此站只有女士
        product.gender = "1"
        # 状态正常
        product.status = "1"
        # 中文
        product.language_id = "1"
        # 解析商品信息
        if self.ana_product_info(product, pg):
            # 保存商品信息
            self.save_product(product)
            # 保存商品描述
            self.save_product_desc(product)
            pimg = ProductImages()
            pimg.spid = product.spider_product_id
            self.ana_product_images(pimg, pg)
            self.save_product_images(pimg)
            psku = ProductSku()
            psku.spid = product.spider_product_id
            self.ana_and_save_product_sku(psku, pg)
            # 语言切换成英文
            en_pg = self.do_visit(surl.replace("/zh/", "/en/"))
            product.language_id = "2"
            # 保存英文版商品信息
            if self.ana_product_info(product, en_pg):
                self.save_product_desc(product)
        else:
            self.log_info("".join([surl, " product not saved!"]))


if __name__ == "__main__":
        nps = NetaporterProductSpider()
        nps.grab_product("016", "https://www.net-a-porter.com/it/zh/product/939674/balmain/---------")