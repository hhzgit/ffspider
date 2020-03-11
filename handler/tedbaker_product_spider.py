# -*- coding: UTF-8 -*-
from __future__ import division
import sys
reload(sys)
sys.setdefaultencoding('utf8')
sys.path.append("..")
import re
import json
from base_product_spider import BaseProductSpider
from db.models import Product, ProductImages, ProductSku


class TedbakerProductSpider(BaseProductSpider):
    def __init__(self):
        BaseProductSpider.__init__(self)
        self.HOSTURL = "https://www.tedbaker.com"
        self.COOKIEFILE = "tedbaker_cookie.txt"
        self.init_opener()
        self.LOGFILE = "./log/tedbaker_log.txt"

    # 解析商品描述信息
    def get_desc_str(self, source_str):
        # 以<li> <h4>为换行标识
        temp_str = source_str.replace('<li>', "\n")
        temp_str = temp_str.replace('<h4>', "\n")
        # 去掉html代码提取文字
        temp_str = re.sub(r'<[^>]*>', '', temp_str)
        # 替换 html 空格
        temp_str = temp_str.replace('&nbsp;', " ")
        # 以换行分割
        temp_str_arr = temp_str.split("\n")
        new_temp_arr = []
        for item in temp_str_arr:
            temp_item = item.strip()
            if len(temp_item) > 0:
                new_temp_arr.append(temp_item)
        if len(new_temp_arr) > 0:
            # 以换行拼接
            return "\n".join(new_temp_arr)
        return ""

    # 解析商品信息
    def ana_product_info(self, product, pg):
        # 商品信息在页面参数 utag_data 中
        pinfo_str_arr = re.findall(r'var utag_data = (\{"[^}]*});', pg)
        # 没取到商品信息视为爬取失败
        if len(pinfo_str_arr) == 0:
            return False
        pinfo_str = str(pinfo_str_arr[0])
        pinfo = json.loads(pinfo_str)
        # 没取到尺码信息视为爬取失败
        if pinfo.has_key('product_sizes_available') and len(pinfo['product_sizes_available']) > 0:
            product.size = pinfo['product_sizes_available'][0]
        else:
            return False
        # 商品名
        rname = pinfo['product_names'][0]
        sname = str(re.findall(r'<h2 class="summary">([^<]*)<', pg)[0])
        product.name = "".join(["'", rname, "'", " ", sname])
        # 站点对商品唯一编码
        product.resource_code = pinfo['product_codes'][0]
        # 品牌对商品唯一编码
        product.code = product.resource_code
        # 分类
        product.category = pinfo['product_categories'][0]
        # 颜色
        product.color = pinfo['product_colours'][0]
        # gender_str = pinfo['site_section']
        # 性别 W开头的为女士 M 开头的为男士
        gender_str = product.category[0:1]
        product.gender = gender_str == "W" and 1 or 2
        # 描述信息
        desc_half_pg = pg.split('<div id="product_details" class="colour_light">')[1]
        desc_str_arr = desc_half_pg.split('</div>')
        product.desc = self.get_desc_str(desc_str_arr[0])
        # 售价
        product.price = pinfo['product_prices'][0]
        if pinfo.has_key('product_previous_prices') and len(pinfo['product_previous_prices']) > 0:
            # 原价
            product.original_price = pinfo['product_previous_prices'][0]
        else:
            # 没有原价的取售价作为原价
            product.original_price = product.price
        # 币种
        product.currency = pinfo['site_currency']

        return True

    # 解析商品sku
    def ana_and_save_product_sku(self, psku, product):
        psku.spid = product.spider_product_id
        # 币种
        psku.currency = product.currency
        # 折扣价
        psku.discount_price = product.price
        # 原价
        psku.price = product.original_price
        # 尺码信息
        size_str = product.size
        size_arr = size_str.split("|")
        if len(size_arr) > 0:
            for item in size_arr:
                temp_str = item.strip()
                if len(temp_str) > 0:
                    size_info_arr = temp_str.split(":")
                    size_name = size_info_arr[0]
                    size_stock = int(size_info_arr[1])
                    # 取库存大于零的
                    if size_stock > 0:
                        psku.size = size_name.strip()
                        self.save_product_skus(psku)
        else:
            # 记录没有sku的商品
            tipstr = "".join([str(product.spider_product_id), " no sku find!"])
            print tipstr
            self.log_info(tipstr)

    # 解析商品图片
    def ana_product_images(self, pimg, pg):
        # 图片信息在 imageFormat[view.imgSizes]['pdp_zoom'] 中
        imgs_str = re.findall(r'"([^"]*)\{\{imageFormat\[view.imgSizes\]\[\'pdp_zoom\'\]\}\}"', pg)
        if len(imgs_str) > 0:
            temp_arr = []
            for img in imgs_str:
                # 取 764*955 尺寸的图片
                img_src = "".join([img, "w=764%26h=955%26q=85"])
                temp_arr.append(img_src)
            pimg.images = ",".join(temp_arr)
        else:
            # 记录没有图片的商品
            self.log_info("".join([str(pimg.spid), " no images!"]))

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
        # 品牌
        product.brand = "Ted Baker"

        pg = self.do_visit(url)
        # 解析商品信息
        if self.ana_product_info(product, pg):
            # 保存商品信息
            self.save_product(product)
            # 保存描述信息
            self.save_product_desc(product)
            pimg = ProductImages()
            pimg.spid = product.spider_product_id
            # 解析图片信息
            self.ana_product_images(pimg, pg)
            # 保存图片信息
            self.save_product_images(pimg)
            psku = ProductSku()
            # 解析并保存sku信息
            self.ana_and_save_product_sku(psku, product)
        else:
            self.log_info("".join([url, " product not saved!"]))


if __name__ == "__main__":
        nps = TedbakerProductSpider()
        nps.grab_product("021", "http://www.tedbaker.com/uk/Womens/Outlet/IDELLA-PORCELAIN-ROSE-MATINEE-PURSE-Pink/p/144090-NUDE-PINK")