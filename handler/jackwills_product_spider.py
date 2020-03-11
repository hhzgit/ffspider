# -*- coding: UTF-8 -*-
from __future__ import division
import sys

sys.path.append("..")
import re
import json
from bs4 import BeautifulSoup
from base_product_spider import BaseProductSpider
from db.models import Product, ProductImages, ProductSku


class JackwillsProductSpider(BaseProductSpider):
    def __init__(self):
        BaseProductSpider.__init__(self)
        self.HOSTURL = "http://www.jackwills.com"
        self.COOKIEFILE = "jackwills_cookie.txt"
        self.init_opener()
        self.LOGFILE = "./log/jackwills_log.txt"

    # 解析商品描述信息
    def get_desc_str(self, source_str):
        # 去掉html代码
        temp_str = re.sub(r'<[^>]*>', '', source_str)
        # 替换html空格
        temp_str = temp_str.replace('&nbsp;', " ")
        # 以换行分割
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
        # 使用BeautifulSoup解析页面
        soup = BeautifulSoup(pg, "html.parser")
        pname = soup.select('h1[class="product-name"]')
        # 没有商品名的视为爬取失败
        if len(pname) == 0:
            return False
        # 商品图片
        imgs_dom = soup.select('div[id="thumbnails"]')
        # 没找到图片的视为爬取失败
        if len(imgs_dom) == 0:
            return False
        imgs = imgs_dom[0].select('ul')[0].select('img')
        product.images = []
        for img in imgs:
            img_url = str(img.attrs["src"])
            # 将图片链接换成 1000*1500的
            product.images.append("".join([img_url.split("?")[0], "?sw=1000&sh=1500&sm=fit"]))
        # 品牌
        product.brand = "Jack Wills"
        # 商品名
        product.name = pname[0].text.strip()
        # 商品信息结构部分（有推荐套装的和没有的结构不一样）
        maindom = soup.select(".main-product-col-2")
        if len(maindom) > 0:
            # 有套装的描述和护理信息
            pcontent = maindom[0].select(".main-product")[0]
            desc_wrapper = pcontent.select(".desc-wrapper")[0]
            product.desc = "".join([desc_wrapper.p.text.strip(), "\n", desc_wrapper.ul.text.strip()])
            product.constitute = desc_wrapper.select('div')[0].ul.text.strip()
        else:
            # 没有套装的描述和护理信息
            pcontent = soup.select(".product-detail")[0]
            desc_wrapper = pcontent.select('div[id="accordion"]')[0].select('div')
            product.desc = desc_wrapper[0].text.strip()
            product.constitute = desc_wrapper[1].text.strip()
        # 颜色
        color_str = pcontent.select('span[class="selectedColor"]')
        # 没有颜色信息的视为爬取失败，因为没颜色信息的会没有尺码信息
        if len(color_str) == 0:
            return False
        product.color = color_str[0].text.strip()
        # 部分商品信息在页面 app.ga.data 参数中
        pdata = json.loads(re.findall(r'app.ga.data = ([^;]*)', pg)[0])
        # 分类
        category_str = pdata["context"]["category"]
        product.category = category_str
        # 以 Ladies 开头的为女性，其他为男性
        product.gender = category_str.startswith("Ladies") and 1 or 2
        # 站点对商品唯一编码
        product.resource_code = pcontent.select('div[class="product-number"]')[0].text.strip()
        # 此站点为品牌官网，品牌对商品唯一编码同站点对商品唯一编码
        product.code = product.resource_code
        # 售价
        sale_price = pcontent.select('span[class="price-sales"]')[0].text
        product.price = sale_price[1:len(sale_price)]
        # 原价
        standard_price =  pcontent.select('span[class="price-standard"]')
        if len(standard_price) > 0:
            og_price = standard_price[0].text
            product.original_price = og_price[1:len(sale_price)]
        else:
            # 无原价的，同售价
            product.original_price = product.price
        # 货币为英镑
        product.currency = "GBP"
        # 尺码
        size_arr = pcontent.select('.size')[0].select('.in-stock')
        if len(size_arr) > 0:
            product.size = []
            for sitem in size_arr:
                product.size.append(str(sitem.a.text.strip()))
        return True

    # 解析商品sku
    def ana_and_save_product_sku(self, psku, product):
        psku.spid = product.spider_product_id
        # 折扣价
        psku.discount_price = product.price
        # 原价
        psku.price = product.original_price
        # 币种
        psku.currency = product.currency
        if len(product.size) > 0:
            for size in product.size:
                psku.size = size
                self.save_product_skus(psku)
        else:
            # 记录没有尺码的商品
            tipstr = "".join([str(product.spider_product_id), " no sku find!"])
            print tipstr
            self.log_info(tipstr)

    # 爬取商品
    def grab_product(self, flag, url):
        product = Product()
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
            self.save_product(product)
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
            # 解析并保存sku信息
            self.ana_and_save_product_sku(psku, product)
        else:
            self.log_info("".join([url, " product not saved!"]))


if __name__ == "__main__":
        nps = JackwillsProductSpider()
        nps.grab_product("022", "http://www.jackwills.com/alvechurch-biker-jacket-100013066001.html?cgid=Ladies%20Clothing#start=2")