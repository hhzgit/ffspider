# -*- coding: UTF-8 -*-
from __future__ import division
import sys

sys.path.append("..")
import re
import json
from base_product_spider import BaseProductSpider
from db.models import Product, ProductImages, ProductSku


class FarfetchProdctSpider(BaseProductSpider):
    def __init__(self):
        BaseProductSpider.__init__(self)
        self.HOSTURL = "https://www.farfetch.cn"
        self.COOKIEFILE = "farfetch_cookie.txt"
        self.init_opener()
        self.LOGFILE = "./log/farfetch_log.txt"

    # 截取商品描述片段代码并去除代码部分留下文字部分
    def split_info(self, start, end, page):
        result_str = ""
        temp_str_arr = page.split(start)
        if len(temp_str_arr) > 1:
            temp_str = temp_str_arr[1]
            temp_str_arr = temp_str.split(end)
            constitute_dom_str = temp_str_arr[0]
            # 将间括弧之间的文字取出来
            constitute_str_arr = re.findall(r'>([^<]*)<', constitute_dom_str)
            if len(constitute_str_arr) > 0:
                constitute_arr = []
                for citem in constitute_str_arr:
                    # 将文字去空格
                    citem = citem.strip()
                    if len(citem) > 0:
                        constitute_arr.append(citem)
                        # 以换行形式拼接文字
                        result_str = "\n".join(constitute_arr)
        return result_str

    # 解析商品信息
    def ana_product_info(self, product, page):
        # 页面参数 window.universal_variable.product 中有商品基础信息
        product_info_arr = re.findall(r'window.universal_variable.product = (\{[^\}]*\});', page)
        # 没有这个参数的视为爬取失败
        if len(product_info_arr) == 0:
            return False
        # 将参数解析成json形式对象
        product_info_str = product_info_arr[0]
        product_info = json.loads(product_info_str)
        # 颜色在页面中取
        color_str = re.findall(r'<span itemprop="color">([^>]*)</span>', page)
        color = len(color_str) > 0 and color_str[0] or ""
        # 护理描述在页面中取
        constitute = self.split_info('<dl class="product-detail-dl">', "</dl>", page)
        # 商品描述在页面中取
        size_desc = self.split_info('<div id="js-product-cm" data-tstid="measurementInfo">', "</div>", page)
        # 产地在页面中取
        location_str = re.findall(r'<span data-tstid="MadeInLabel">([^<]*)</span>', page)
        location = len(location_str) > 0 and location_str[0] or ""

        # 站点对商品唯一编码
        product.resource_code = product_info["id"]
        # 商品名
        product.name = product_info["name"]
        # 品牌
        product.brand = product_info["designerName"]
        # 性别
        product.gender = product_info["gender"] == "Women" and "1" or "2"
        # 分类
        product.category = product_info["subCategory"]
        # 颜色
        product.color = color
        # 品牌对商品唯一编码
        product.code = product_info.get("designerStyleId")
        # 描述
        product.desc = product_info["description"]
        # 产地
        product.location = location
        # 护理
        product.constitute = constitute
        # 尺码信息
        product.size_desc = size_desc
        return True

    # 解析商品图片
    def ana_product_images(self, pimg, page):
        # 图片在页面中取
        img_arr = re.findall(r'<img trk="25" src="([^"]*)"', page)
        result_arr = []
        if len(img_arr) > 0:
            for img_item in img_arr:
                # 将图片后缀替换，更改为1000宽的
                img_url = img_item.replace("70.jpg", "1000.jpg")
                if img_url in result_arr:
                    continue
                result_arr.append(img_url)
            pimg.images = ",".join(result_arr)
        else:
            # 记录没有图片的商品
            self.log_info("".join([str(pimg.spid), " no images!"]))

    # 将商品价格转为数字
    def get_price_num(self, priceStr):
        if priceStr == "":
            return None
        pstr = str(priceStr.split(" ")[0])
        # 替换“.”，在此站点“.” 为千分位符号
        pstr = pstr.replace(".", "")
        return pstr

    # 解析商品sku信息
    def ana_and_save_skus(self, spid, sku_info):
        # sku 信息在参数 SizesInformationViewModel 的 AvailableSizes中
        skus = sku_info["SizesInformationViewModel"]["AvailableSizes"]
        if len(skus) == 0:
            # 记录没有尺码的商品
            tipstr = "".join([str(spid), " no sku find!"])
            print tipstr
            self.log_info(tipstr)
            return
        psku = ProductSku()
        psku.spid = spid
        for sku in skus:
            # 尺码
            size_str = sku["Description"]
            # 尺码所属（国家标准）
            size_scale = sku["ScaleDescription"]
            if size_scale is not None:
                # 以 尺码[标准] 形式保存
                size_str = "".join([size_str, "[", size_scale, "]"])
            psku.size = size_str
            # 价格信息
            pinfo = sku["PriceInfo"]
            # 原价
            oprice = self.get_price_num(pinfo["FormatedPriceWithoutPromotion"])
            # 当前售价
            dprice = self.get_price_num(pinfo["FormatedPrice"])
            psku.discount_price = dprice
            if oprice is not None:
                psku.price = oprice
            else:
                psku.price = dprice
            # 保存
            self.save_product_skus(psku)

    # 爬取商品
    def grab_product(self, flag, url):
        # 先爬取意大利站的信息
        iturl = url.replace("/cn/", "/it/")

        it_page = self.do_visit(iturl)
        product = Product()
        product.flag = flag
        # 源链接
        product.url = iturl
        # 状态设为在架
        product.status = "1"
        # 先爬取的意大利站信息，记录描述的语言为英语
        product.language_id = "2"
        # 解析商品信息
        if self.ana_product_info(product, it_page):
            # 保存商品信息
            self.save_product(product)
            # 保存描述信息
            self.save_product_desc(product)
            pimg = ProductImages()
            pimg.spid = product.spider_product_id
            # 解析保存图片信息
            self.ana_product_images(pimg, it_page)
            self.save_product_images(pimg)
            # 换成中国站，爬取中文描述
            cnurl = iturl.replace("/it/", "/cn/")
            cn_page = self.do_visit(cnurl)
            # 设置描述语言为中文
            product.language_id = "1"
            # 解析并保存商品描述
            self.ana_product_info(product, cn_page)
            self.save_product_desc(product)
            # 调用商品sku信息接口获取sku信息
            product_url = "".join(["https://www.farfetch.cn/it/product/GetDetailState?productId=", product.resource_code, "&designerId=0"])
            skus = self.get_json(product_url)
            # 解析并保存sku信息
            self.ana_and_save_skus(product.spider_product_id, skus)
        else:
            # 未解析成功的记录爬取失败
            self.log_info("".join([url, " product not find!"]))


if __name__=="__main__":
    fps = FarfetchProdctSpider()
    fps.grab_product("015", "https://www.farfetch.cn/cn/shopping/women/kenzo---item-12342851.aspx")