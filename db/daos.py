# -*- coding: UTF-8 -*-
import time


# dao原始类
class Dao(object):
    def __init__(self, conn, cur):
        self.conn = conn
        self.cur = cur

    # 清空表
    def truncate(self):
        sql = "".join(["TRUNCATE TABLE ", self.table])
        self.cur.execute(sql)
        self.conn.commit()

    # 保存一条数据
    def save(self, object):
        sql = "".join(["INSERT INTO ", self.table, self.clumns, " VALUES ", self.params])
        id = self.execute_save(sql, object)
        self.conn.commit()
        return id

    # 提供给子类按自己特性实现保存
    def execute_save(self, sql, object):
        print("don't call me")

    # 获取最新的一条记录id，用于插入数据后查询id
    def get_last_insert_id(self):
        sql = "".join(["SELECT ", self.tableId, " FROM ", self.table, " ORDER BY ", self.tableId, " DESC LIMIT 0,1"])
        self.cur.execute(sql)
        result = self.cur.fetchone()
        if result is not None:
            return result[0]
        return None


# 商品DAO
class ProductDao(Dao):
    def __init__(self, conn, cur):
        Dao.__init__(self, conn, cur)
        self.table = "`t_spider_product`"
        self.tableId = "`spider_product_id`"
        self.clumns = "(`designer`,`gender`,`category`,`status`,`color_code`,`designer_code`,`resource_code`,`flag`,`source_url`)"
        self.params = "(%s,%s,%s,%s,%s,%s,%s,%s,%s)"

    # 类型保存方法，覆盖父类供save方法调用
    def execute_save(self, sql, c):
        self.cur.execute(sql,
                         [c.brand, c.gender, c.category, c.status, c.color, c.code, c.resource_code, c.flag, c.url])
        return self.cur.lastrowid

    def update_product_info(self, c):
        sql = "".join(["UPDATE ", self.table, " SET `designer`=%s,`gender`=%s,`category`=%s,`status`=%s,`color_code`=%s,`designer_code`=%s,`resource_code`=%s,`flag`=%s,`source_url`=%s WHERE `spider_product_id`=%s"])
        self.cur.execute(sql, [c.brand, c.gender, c.category, c.status, c.color, c.code, c.resource_code, c.flag, c.url, c.spider_product_id])
        self.conn.commit()

    def get_all_spider_product(self):
        sql = "".join(["SELECT * FROM ", self.table])
        self.cur.execute(sql)
        result = self.cur.fetchall()
        if result is not None:
            return result
        return None

    def get_products_by_id_between(self, from_id, to_id):
        sql = "".join(["SELECT * FROM ", self.table, " where spider_product_id > %s and spider_product_id <= %s"]);
        self.cur.execute(sql, [from_id, to_id])
        result = self.cur.fetchall()
        if result is not None:
            return result
        return None

    def update_selling_status(self, spid, status):
        sql = "".join(["UPDATE ", self.table, " SET selling_status=%s WHERE spider_product_id=%s"]);
        self.cur.execute(sql, [status, spid])
        self.conn.commit()

    def get_id_by_code(self, code):
        sql = "".join(["SELECT `spider_product_id` FROM ", self.table, " WHERE `resource_code`=%s"])
        self.cur.execute(sql, [code])
        result = self.cur.fetchall()
        if result is not None and len(result) > 0:
            result = result[0]
            if result is not None and len(result) > 0:
                return result[0]
        return None

    def get_need_update_products_by_flag(self, flag):
        sql = "".join(["SELECT a.* FROM ", self.table, " a WHERE a.flag=%s AND EXISTS(SELECT spider_product_sku_id FROM t_spider_product_sku WHERE spider_product_id=a.spider_product_id AND stock_status=1)"]);
        self.cur.execute(sql, [flag])
        result = self.cur.fetchall()
        if result is not None:
            return result
        return None

    def get_need_update_products_by_site(self, site):
        sql = "".join(["SELECT a.* FROM ", self.table, " a LEFT JOIN t_spider_source b on a.flag=b.flag WHERE b.site_name=%s AND EXISTS(SELECT spider_product_sku_id FROM t_spider_product_sku WHERE spider_product_id=a.spider_product_id AND stock_status=1)"]);
        self.cur.execute(sql, [site])
        result = self.cur.fetchall()
        if result is not None:
            return result
        return None

    def get_products_by_flag_and_id_between(self, flag, sid, eid):
        sql = "".join(["SELECT * FROM ", self.table, " WHERE flag=%s AND spider_product_id >= %s AND spider_product_id <= %s"]);
        self.cur.execute(sql, [flag, sid, eid])
        result = self.cur.fetchall()
        if result is not None:
            return result
        return None

    def get_farfetch_need_update_products(self):
        sql = "".join(["SELECT a.* FROM ", self.table,
                       " a WHERE a.flag in ('001','002','003','004','005','006','007','008','009','010','011') AND EXISTS(SELECT spider_product_sku_id FROM t_spider_product_sku WHERE spider_product_id=a.spider_product_id AND stock_status=1)"]);
        self.cur.execute(sql)
        result = self.cur.fetchall()
        if result is not None:
            return result
        return None

    def updateProductCover(self, pId, imgUrl):
        sql = "".join(["UPDATE ", self.table, " SET `cover` = %s WHERE ", self.tableId, " = %s"])
        self.cur.execute(sql, [imgUrl, pId])
        self.conn.commit()


class ProductUrlsDao(Dao):
    def __init__(self, conn, cur):
        Dao.__init__(self, conn, cur)
        self.table = "`t_asos_product_urls`"
        self.tableId = "`asos_product_url_id`"
        self.clumns = "(`asos_id`,`brand`,`product_url`,`is_spider`)"
        self.params = "(%s, %s, %s, %s)"

    def execute_save(self, sql, c):
        self.cur.execute(sql, [c.asos_id, c.brand, c.product_url, c.is_spider])
        return self.cur.lastrowid

    def exist_product(self, asos_id):
        sql = "".join(["SELECT * FROM ", self.table, " WHERE `asos_id`=%s"])
        self.cur.execute(sql, [asos_id])
        result = self.cur.fetchall()
        if result is not None and len(result) > 0:
            return True
        return False

    def get_need_spider_urls(self):
        sql = "".join(["SELECT * FROM ", self.table, " WHERE `is_spider`=0 ORDER BY `asos_product_url_id` asc"]);
        self.cur.execute(sql)
        result = self.cur.fetchall()
        if result is not None:
            return result
        return None

    def sign_spider(self, aid, flag):
        sql = "".join(["UPDATE ", self.table, " SET `is_spider`=%s WHERE `asos_product_url_id`=%s"])
        self.cur.execute(sql, [flag, aid])
        self.conn.commit()

    def update_group_ids(self, ids, asos_id):
        sql = "".join(["UPDATE ", self.table, " SET `group_product_ids`=%s WHERE `asos_id`=%s"])
        self.cur.execute(sql, [ids, asos_id])
        self.conn.commit()


class ProductDescDao(Dao):
    def __init__(self, conn, cur):
        Dao.__init__(self, conn, cur)
        self.table = "`t_spider_product_description`"
        self.tableId = "`spider_product_id`"
        self.clumns = "(`spider_product_id`,`name`,`description`,`constitute`,`location`,`size_description`,`language_id`)"
        self.params = "(%s,%s,%s,%s,%s,%s,%s)"

    # 类型保存方法，覆盖父类供save方法调用
    def execute_save(self, sql, c):
        self.cur.execute(sql,
                         [c.spider_product_id, c.name, c.desc, c.constitute, c.location, c.size_desc, c.language_id])
        return self.cur.lastrowid

    def is_exists_product_desc(self, spid, language_id):
        sql = "".join(["SELECT * FROM ", self.table, " WHERE `spider_product_id`=%s and `language_id`=%s"])
        self.cur.execute(sql, [spid, language_id])
        result = self.cur.fetchall()
        if result is not None and len(result) > 0:
            return True
        return False

    def update_product_desc(self, c):
        sql = "".join(["UPDATE ", self.table, " SET `name`=%s,`description`=%s,`constitute`=%s,`location`=%s,`size_description`=%s WHERE `spider_product_id`=%s AND `language_id`=%s"])
        self.cur.execute(sql, [c.name, c.desc, c.constitute, c.location, c.size_desc, c.spider_product_id, c.language_id])
        self.conn.commit()

    def get_en_desc_no_zh(self):
        sql = "".join(["SELECT a.* FROM ", self.table, " a LEFT JOIN ", self.table, " b ON a.`spider_product_id`=b.`spider_product_id` AND b.`language_id`=1 WHERE a.`language_id`=2 AND b.`spider_product_id` IS NULL"])
        self.cur.execute(sql)
        result = self.cur.fetchall()
        if result is not None:
            return result
        return None

    def get_all_zh_desc(self):
        sql = "".join(["SELECT * FROM ", self.table, " WHERE `language_id`=1"])
        self.cur.execute(sql)
        result = self.cur.fetchall()
        if result is not None:
            return result
        return None

# 商品图片DAO
class ProductImagesDao(Dao):
    def __init__(self, conn, cur):
        Dao.__init__(self, conn, cur)
        self.table = "`t_spider_product_images`"
        self.tableId = "`spider_product_id`"
        self.clumns = "(`spider_product_id`,`farfetch_images`)"
        self.params = "(%s,%s)"

    # 类型保存方法，覆盖父类供save方法调用
    def execute_save(self, sql, c):
        self.cur.execute(sql, [c.spid, c.images])
        return self.cur.lastrowid

    def is_exists_product_images(self, spid):
        sql = "".join(["SELECT * FROM ", self.table, " WHERE `spider_product_id`=%s"])
        self.cur.execute(sql, [spid])
        result = self.cur.fetchall()
        if result is not None and len(result) > 0:
            return True
        return False

    def getNeedDownLoadImgs(self):
        sql = "".join(["SELECT `spider_product_id`,`farfetch_images` FROM ", self.table, " WHERE `images` is null"])
        self.cur.execute(sql)
        result = self.cur.fetchall()
        if result is not None:
            return result
        return None

    def updateProductImgs(self, pId, imgUrl):
        sql = "".join(["UPDATE ", self.table, " SET `images` = %s WHERE ", self.tableId, " = %s"])
        self.cur.execute(sql, [imgUrl, pId])
        self.conn.commit()

    def update_product_images(self, c):
        sql = "".join(["UPDATE ", self.table, " SET `farfetch_images`=%s WHERE `spider_product_id`=%s"])
        self.cur.execute(sql, [c.images, c.spid])
        self.conn.commit()


# 商品Sku DAO
class ProductSkuDao(Dao):
    def __init__(self, conn, cur):
        Dao.__init__(self, conn, cur)
        self.table = "`t_spider_product_sku`"
        self.tableId = "`spider_product_sku_id`"
        self.clumns = "(`spider_product_id`,`size`,`price`,`currency`,`discount_price`)"
        self.params = "(%s,%s,%s,%s,%s)"

    # 类型保存方法，覆盖父类供save方法调用
    def execute_save(self, sql, c):
        self.cur.execute(sql, [c.spid, c.size, c.price, c.currency, c.discount_price])
        return self.cur.lastrowid

    def get_id_by_spid_size(self, c):
        sql = "".join(["SELECT `spider_product_sku_id` FROM ", self.table, " WHERE `spider_product_id`=%s AND `size`=%s"])
        self.cur.execute(sql, [c.spid, c.size])
        result = self.cur.fetchall()
        if result is not None and len(result) > 0:
            result = result[0]
            if result is not None and len(result) > 0:
                return result[0]
        return None

    def get_skus_by_spid(self, spid):
        sql = "".join(["SELECT * FROM ", self.table, " WHERE `spider_product_id`=%s"])
        self.cur.execute(sql, [spid])
        return self.cur.fetchall()

    def get_on_skus_by_spid(self, spid):
        sql = "".join(["SELECT * FROM ", self.table, " WHERE `spider_product_id`=%s AND `stock_status`=1"])
        self.cur.execute(sql, [spid])
        return self.cur.fetchall()

    def update_product_sku(self, c):
        sql = "".join(["UPDATE ", self.table, " SET `price`=%s,`currency`=%s,`discount_price`=%s WHERE `spider_product_sku_id`=%s"])
        self.cur.execute(sql, [c.price, c.currency, c.discount_price, c.spider_product_sku_id])
        self.conn.commit()

    def update_sku_discount_price(self, code, flag, price):
        sql = "".join(["UPDATE ", self.table, " a,t_spider_product b set a.discount_price=%s where a.spider_product_id=b.spider_product_id and b.resource_code=%s and b.flag=%s"])
        self.cur.execute(sql, [price, code, flag])
        self.conn.commit()

    def set_sku_out_of_stock(self, spid, size):
        sql = "".join(["UPDATE ", self.table, " SET `stock_status`=0 WHERE `spider_product_id`=%s AND `size`=%s"])
        self.cur.execute(sql, [spid, size])
        self.conn.commit()

    def set_skus_out_of_stock_by_spid(self, spid):
        sql = "".join(["UPDATE ", self.table, " SET `stock_status`=0 WHERE `spider_product_id`=%s"])
        self.cur.execute(sql, [spid])
        self.conn.commit()


class FarfetchDesignerDao(Dao):
    def __init__(self, conn, cur):
        Dao.__init__(self, conn, cur)
        self.table = "`t_farfetch_designer`"
        self.tableId = "`id`"
        self.clumns = "(`designer_name`,`farfetch_designer_id`,`url_name`)"
        self.params = "(%s,%s,%s)"

    def execute_save(self, sql, c):
        self.cur.execute(sql, [c.designer_name, c.farfetch_designer_id, c.url_name])
        return self.cur.lastrowid

    def get_farfetch_designer_by_urlname(self, name):
        sql = "".join(["SELECT * FROM ", self.table, " WHERE `url_name` like %s"])
        self.cur.execute(sql, [name])
        return self.cur.fetchall()

    def get_all_designer(self):
        sql = "".join(["SELECT * FROM ", self.table])
        self.cur.execute(sql)
        return self.cur.fetchall()

    def get_designer_by_name(self, name):
        sql = "".join(["SELECT * FROM ", self.table, " WHERE `designer_name` like %s"])
        self.cur.execute(sql, [name])
        return self.cur.fetchall()


class FFProductDao(Dao):
    def __init__(self, conn, cur):
        Dao.__init__(self, conn, cur)
        self.table = "`t_product`"
        self.tableId = "`product_id`"

    def get_farfetch_product_need_update(self):
        sql = "".join(["SELECT a.`product_id`,a.`source`,b.`name` FROM ", self.table, " a LEFT JOIN t_designer b ON a.designer_id=b.designer_id WHERE `product_status`=1 AND `source` LIKE '%www.farfetch.cn%'"])
        self.cur.execute(sql)
        return self.cur.fetchall()

    def get_on_skus_by_product_id(self, productId):
        sql = "".join(["SELECT * FROM t_product_sku WHERE `product_id`=%s AND `sku_status`='ON'"])
        self.cur.execute(sql, [productId])
        return self.cur.fetchall()


class FarfetchNewProductDao(Dao):
    def __init__(self, conn, cur):
        Dao.__init__(self, conn, cur)
        self.table = "`t_farfetch_new_product_urls`"
        self.tableId = "`url_id`"
        self.clumns = "(`farfetch_id`,`flag`,`url`,`spider_flag`)"
        self.params = "(%s,%s,%s,%s)"

    def execute_save(self, sql, c):
        self.cur.execute(sql, [c.farfetch_id, c.flag, c.url, c.spider_flag])
        return self.cur.lastrowid

    def is_exists_product_url(self, npid):
        sql = "".join(["SELECT * FROM ", self.table, " WHERE `netaporter_id`=%s"])
        self.cur.execute(sql, [npid])
        result = self.cur.fetchall()
        if result is not None and len(result) > 0:
            return True
        return False

    def get_urls_wait_grab(self):
        sql = "".join(["SELECT * FROM ", self.table, " WHERE `spider_flag` = 0"])
        self.cur.execute(sql)
        return self.cur.fetchall()

    def sign_finished(self, urlid):
        sql = "".join(["UPDATE ", self.table, " SET `spider_flag`=1 WHERE `url_id` = %s"])
        self.cur.execute(sql, [urlid])
        self.conn.commit()

class ProductUrlDao(Dao):
    def __init__(self, conn, cur):
        Dao.__init__(self, conn, cur)
        self.table = "`t_spider_product_url`"
        self.tableId = "`url_id`"
        self.clumns = "(`source_code`,`flag`,`url`,`spider_flag`)"
        self.params = "(%s,%s,%s,%s)"

    def execute_save(self, sql, c):
        self.cur.execute(sql, [c.source_code, c.flag, c.url, c.spider_flag])
        return self.cur.lastrowid

    def is_exists_product_url(self, scode):
        sql = "".join(["SELECT * FROM ", self.table, " WHERE `source_code`=%s"])
        self.cur.execute(sql, [scode])
        result = self.cur.fetchall()
        if result is not None and len(result) > 0:
            return True
        return False

    def get_urls_wait_grab(self, site_name):
        sql = "".join(["SELECT a.* FROM ", self.table, " a LEFT JOIN t_spider_product b ON a.source_code=b.resource_code LEFT JOIN t_spider_source c ON a.`flag`=c.`flag` WHERE a.`spider_flag` = 0 AND c.`site_name`=%s AND b.`spider_product_id` IS NULL"])
        self.cur.execute(sql, [site_name])
        return self.cur.fetchall()

    def sign_finished(self, urlid):
        sql = "".join(["UPDATE ", self.table, " SET `spider_flag`=1 WHERE `url_id` = %s"])
        self.cur.execute(sql, [urlid])
        self.conn.commit()