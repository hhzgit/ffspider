# -*- coding: UTF-8 -*-


class DBParams(object):
    def __init__(self):
        self.host = ""
        self.port = ""
        self.user = ""
        self.passwd = ""
        self.db = ""


class ProductUrls(object):
    def __init__(self):
        self.brand = ""
        self.product_url = ""
        self.is_spider = ""
        self.asos_id = ""


class Product(object):
    def __init__(self):
        self.spider_product_id = ""
        self.name = ""
        self.brand = ""
        self.gender = ""
        self.category = ""
        self.cover = ""
        self.status = ""
        self.price = ""
        self.size = ""
        self.desc = ""
        self.constitute = ""
        self.size_desc = ""
        self.language_id = ""
        self.color = ""
        self.code = ""
        self.location = ""
        self.resource_code = ""
        self.images = ""
        self.url = ""
        self.flag = ""
        self.original_price = ""
        self.currency = ""


class ProductImages(object):
    def __init__(self):
        self.spid = ""
        self.images = ""


class ProductSku(object):
    def __init__(self):
        self.spider_product_sku_id = ""
        self.spid = ""
        self.size = ""
        self.price = ""
        self.discount_price = ""
        self.currency = "EURO"


class FarfetchDesigner(object):
    def __init__(self):
        self.id = ""
        self.designer_name = ""
        self.farfetch_designer_id = ""
        self.url_name = ""


class ProductUrl(object):
    def __init__(self):
        self.url_id = ""
        self.source_code = ""
        self.flag = ""
        self.url = ""
        self.spider_flag = 0
        self.record_time = ""
        self.spider_time = ""
