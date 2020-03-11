# -*- coding: UTF-8 -*-
import sys

sys.path.append("..")
import multiprocessing
import time
import os
from db.dbconnecter import get_param_conn
from db.daos import ProductDao, ProductImagesDao
from db.models import DBParams
from netvisiter.net_openner import NetOpener


# 下载不同站点的图片启用不同的 OPENER
# OPENER = NetOpener("https://www.net-a-porter.com/it/zh/", "netaporter_cookie.txt")
OPENER = NetOpener("https://www.farfetch.cn", "farfetch_cookie.txt")
# OPENER = NetOpener("https://www.reiss.com", "reiss_cookie.txt")
# OPENER = NetOpener("https://www.tedbaker.com", "tedbaker_cookie.txt")
# OPENER = NetOpener("http://www.jackwills.com", "jackwills_cookie.txt")
OPENER.init_cookie()
OPENER.load_cookie()
OPENER.load_opener()


# 记录日志
def log_info(info):
    file = open("./log/image_log.txt", "a")
    file.write("".join([info, "\n"]))
    file.close()


# 图片下载的实现方法，当出现报错时会调用自身重新下载，连续错误3次后不再下载，记入日志中
def do_update_image(img_url, img_file, trycount, pid):
    imgf = open(img_file, "wb")
    try:
        global OPENER
        # 访问图片
        img_response = OPENER.visit_url(img_url, None)
        # 下载图片到指定目录
        imgf.write(img_response.read())
        # 完成下载关闭下载文件
        imgf.close()
        return True
    except Exception:
        imgf.close()
        trycount = trycount+1
        # 连续出错大于3次，不再下载，记入日志未下载图片
        if trycount > 3:
            print "error can't resolve!"
            log_info("".join([str(pid), ":", img_url, " not download!"]))
            if os.path.exists(img_file):
                # 删除下载失败的残留文件
                os.remove(img_file)
            return False
        print("some error happend,retrying...........")
        # 出现错误，递归调用自身，重新下载图片
        return do_update_image(img_url, img_file, trycount, pid)


def downAndUpImg(imgPath, pId, idx, pDao):
    downImg = imgPath
    # 每个商品的目录以100000 + 商品爬虫id 命名
    imgDir = str(100000 + pId)
    # 图片以商品爬虫id + 188765432 + 第几张 命名
    imgName = int(imgDir) + 188765432
    imgName = str(imgName) + "_" + str(idx) + ".jpg"
    # 下载图片的根目录，请根据自己的需要做修改，根目录名 ptncp 不要修改
    imgPath = "G:/spider/ptncp/" + imgDir
    # 另存封面图片的根目录，根据自己的需要修改，提供给运营的相关负责人做标准化处理
    coverPath = "G:/spider/cover/"
    if not os.path.exists(imgPath):
        os.mkdir(imgPath)

    # 拼接完整的图片文件路径
    imgFile = imgPath + "/" + imgName
    # 生成本站对应的图片url
    newImgUrl = "http://ssfk-media01.oss-cn-shenzhen.aliyuncs.com/ptncp/" + imgDir + "/" + imgName
    # 下载图片
    if do_update_image(downImg, imgFile, 0, pId):
        # 如果是首图，则为封面，将其在商品目录复制一份命名为cover.jpg的作为临时封面图，并保存一份到cover文件夹
        if idx == 0:
            coverFile = coverPath + imgDir + ".jpg"
            cvpt = imgPath + "/cover.jpg"
            imgf = open(imgFile, "rb").read()
            open(coverFile, "wb").write(imgf)
            open(cvpt, "wb").write(imgf)
            # 生成本站封面url并存到爬虫库t_spider_product 的 cover 字段
            coverUrl = "http://ssfk-media01.oss-cn-shenzhen.aliyuncs.com/ptncp/" + imgDir + "/cover.jpg"
            pDao.updateProductCover(pId, coverUrl)

        return newImgUrl
    return False


def updateImgsNeedDL(global_param):
    # 初始化数据库连接
    db_params = DBParams()
    db_params.host = "172.16.8.147"
    db_params.port = "3306"
    db_params.user = "dba"
    db_params.passwd = "123456"
    db_params.db = "spider2"
    conn = get_param_conn(db_params)
    if conn is None:
        print("没有此数据库")
        return False
    cur = conn.cursor()

    # 初始化dao
    piDao = ProductImagesDao(conn, cur)
    pDao = ProductDao(conn, cur)

    # 获取需要下载的图片数据集（在t_spider_product_images 表中 images 为null的数据）
    pDatas = piDao.getNeedDownLoadImgs()
    for item in pDatas:
        prodId = item[0]
        imgsStr = item[1]
        if (len(imgsStr) > 0):
            # 源图片链接是以“,”隔开的url
            imgsArr = imgsStr.split(",")
            newImgsStr = ""
            # 循环下载图片
            for imgIdx in range(len(imgsArr)):
                imgPath = downAndUpImg(imgsArr[imgIdx], prodId, imgIdx, pDao)
                if imgPath == False:
                    continue
                imgPath = "".join(['"', imgPath, '"'])
                newImgsStr = "".join([newImgsStr, ",", imgPath])
            slen = len(newImgsStr)
            # 一个商品的下载完成后以json数组字符串的形式保存
            newImgsStr = newImgsStr[1:int(len(newImgsStr))]
            newImgsStr = "".join(["[", newImgsStr, "]"])
            piDao.updateProductImgs(prodId, newImgsStr)
        print str(prodId)
        global_param["count"] = prodId

    cur.close()
    conn.close()


def start_process(global_param):
    print "start"
    global_param["count"] = 0
    # 开启子进程下载图片
    pro1 = multiprocessing.Process(target=updateImgsNeedDL, args=(global_param,))
    pro1.start()
    f_pid = pro1.pid
    while True:
        b = global_param["count"]
        # 每90秒查看一下当前更新到的商品id是否有变化
        time.sleep(90)
        c = global_param["count"]
        # 没有变化，则认为是下载进程卡死，启动新的进程下载图片
        if b == c:
            # 杀掉老进程（未起作用，有待改进）
            os.popen('taskkill.exe /pid:' + str(f_pid))
            print "process is killed"
            break
    print "restarting.........."
    time.sleep(5)
    start_process(global_param)


if __name__ == "__main__":
    mgr = multiprocessing.Manager()
    global_param = mgr.dict()
    start_process(global_param)