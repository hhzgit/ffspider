# -*- coding: UTF-8 -*-
from __future__ import division
import sys

sys.path.append("..")
import re
import json
from base_product_spider import BaseProductSpider
from db.models import Product, ProductImages, ProductSku


class FrenchconnectionProductSpider(BaseProductSpider):
    def __init__(self):
        BaseProductSpider.__init__(self)
        self.HOSTURL = "https://www.frenchconnection.com"
        self.COOKIEFILE = "frenchconnection_cookie.txt"
        self.init_opener()
        self.LOGFILE = "./log/frenchconnection_log.txt"

    # 获取商品描述信息
    def get_desc_str(self, source_str):
        # 信息换行的标记为</li> 符号
        temp_str = source_str.replace("</li>", "\n")
        # 将html代码全去掉
        temp_str = re.sub(r'<[^>]*>', '', temp_str)
        # 处理html空格
        temp_str = temp_str.replace('&nbsp;', " ")
        temp_str_arr = temp_str.split("\n")
        new_temp_arr = []
        for item in temp_str_arr:
            temp_item = item.strip()
            # 取有长度的字符串
            if len(temp_item) > 0:
                new_temp_arr.append(temp_item)
        if len(new_temp_arr) > 0:
            # 以换行形式拼接
            return "\n".join(new_temp_arr)
        return ""

    # 解析商品信息
    def ana_product_info(self, product, pg):
        # 页面参数 productJson 中有部分商品信息
        pjson_str = re.findall(r'var productJson = ([^;]*);', pg)
        # 没有此参数则认为页面访问失败
        if len(pjson_str) == 0:
            return False
        # wishlist 中参数为加引号引起解析失败，此参数无用，直接替换成空
        pjson_str = re.sub(r'"wishlist": {[^}]*}', '"wishlist": {}', pjson_str[0])
        pjson = json.loads(pjson_str)
        # 商品信息在 window.universal_variable 的 description 中
        uvariable = re.findall(r'window.universal_variable = ([^<]*description:"[^"]*"[^;]*)', pg)
        # 没有描述信息的视为异常页面，不爬取
        if len(uvariable) == 0:
            return False
        uvariable = uvariable[0]

        # 品牌
        product.brand = "French Connection"
        # 站点对商品的唯一编码
        product.resource_code = re.findall(r'id:"([^"]*)"', uvariable)[0]
        # 此为品牌官网，品牌对商品唯一编码同站点唯一编码
        product.code = product.resource_code
        # 商品名称
        product.name = re.findall(r'name:"([^"]*)"', uvariable)[0]
        # 描述
        product.desc = self.get_desc_str(re.findall(r'description:"([^"]*)"', uvariable)[0])
        # 大分类的开头会标明所属性别
        category_str = re.findall(r' category:"([^"]*)"', uvariable)[0]
        # man开头的为男，woman 为女
        if category_str == "man":
            product.gender = 2
        else :
            product.gender = 1
        # 子分类
        product.category = re.findall(r'subcategory:"([^"]*)"', uvariable)[0]
        # 原价
        product.original_price = re.findall(r'unit_price:([^,]*)', uvariable)[0]
        # 售价
        product.price = re.findall(r'unit_sale_price:([^,]*)', uvariable)[0]
        # 货币
        product.currency = re.findall(r'currency:"([^"]*)"', uvariable)[0]
        # 页面参数 variants 中有颜色和尺码信息
        pinfo = pjson["variants"][0]
        # 颜色
        product.color = pinfo["Colour"]
        # 尺码信息
        product.size = pinfo["SizeVariantInfos"]
        # 护理信息在页面中
        constitute_half_pg = pg.split('<div class="product_information_row product_information_care">')
        if len(constitute_half_pg) > 1:
            constitute_half_pg = constitute_half_pg[1]
            constitute_str_arr = constitute_half_pg.split('<div class="product_information_row_inner">')[1].split("</div>")
            # 解析出文字信息
            product.constitute = self.get_desc_str(constitute_str_arr[0])
        # 图片信息根据 images 参数生成
        imgjson = pjson["images"]
        idxshots = []
        # 此站点访问多次后IndexShots将丢失，暂时固定图片5张
        if imgjson.has_key("IndexShots"):
            idxshots = pjson["images"]["IndexShots"]
        else:
            idxshots = ["", "2", "3", "4", "5"]
        # 用于生成图片链接的参数
        media_base = re.findall(r"media_base: '([^']*)", pg)[0]
        site_code = re.findall(r"site_code: '([^']*)", pg)[0]
        image_resource_code = re.findall(r"image_resource_code: '([^']*)", pg)[0]
        dynamic_enabled = re.findall(r'"Enabled":([^,]*)', pg)[0] == "true" and True or False
        dynamic_baseurl = re.findall(r'"BaseUrl":"([^"]*)', pg)[0]
        product.images = []
        # 根据站点上的公式生成图片链接
        for idx in idxshots:
            ident = idx=="" and "".join([product.resource_code, ".jpg"]) or "".join([product.resource_code, "_", idx, ".jpg"])
            ident = ident.replace("/", "")
            if dynamic_enabled:
                product.images.append("".join(["https:", dynamic_baseurl, image_resource_code, "/", ident, "?height=1537&width=1024"]))
            else:
                product.images.append("".join(["https:", media_base, site_code, "/", ident]))

        return True

    # 解析商品sku信息
    def ana_and_save_product_sku(self, psku, product):
        psku.spid = product.spider_product_id
        # 折扣价（当前售价）
        psku.discount_price = product.price
        # 币种
        psku.currency = product.currency
        # 原价
        psku.price = product.original_price
        if len(product.size) > 0:
            for size in product.size:
                psku.size = size["Text"]
                instock = size["VariantInStock"]
                # 只保存在架尺码
                if instock:
                    self.save_product_skus(psku)
        else:
            # 记录没有尺码的商品
            tipstr = "".join([str(psku.spid), " no sku find!"])
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
        # 英文
        product.language_id = "2"

        pg = self.do_visit(url)
        # 解析商品信息
        if self.ana_product_info(product, pg):
            # 保存商品信息
            self.save_product(product)
            # 保存描述信息
            self.save_product_desc(product)
            # 保存图片信息
            pimg = ProductImages()
            pimg.spid = product.spider_product_id
            if len(product.images) > 0:
                pimg.images = ",".join(product.images)
                self.save_product_images(pimg)
            else:
                # 记录没有图片的商品
                self.log_info("".join([str(pimg.spid), " no images!"]))
            psku = ProductSku()
            # 保存sku信息
            self.ana_and_save_product_sku(psku, product)
        else:
            self.log_info("".join([url, " product not saved!"]))



if __name__ == "__main__":
        fps = FrenchconnectionProductSpider()
        fps.grab_product("023", "https://www.frenchconnection.com/product/woman-collections-sale/71ifz/delphine-draped-one-shoulder-dress.htm")