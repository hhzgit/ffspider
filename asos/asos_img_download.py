# -*- coding: UTF-8 -*-
import sys

sys.path.append("..")
import urllib
import multiprocessing
import time
import os
from db.dbconnecter import get_conn
from daos import ProductDao, ProductImagesDao


def do_update_image(img_url, img_file):
    try:
        urllib.urlretrieve(img_url, img_file)
    except urllib.ContentTooShortError:
        print("some error happend,retrying...........")
        do_update_image(img_url, img_file)


def downAndUpImg(imgPath, pId, idx, pDao):
    downImg = imgPath
    imgDir = str(100000 + pId)
    imgName = imgPath.split("/")
    imgName = imgName[len(imgName) - 1]
    imgName = imgName.split("-")
    imgName = int(imgName[0]) + 188765432
    imgName = str(imgName) + "_" + str(idx) + ".jpg"
    imgPath = "G:/spider/ptncp/" + imgDir
    coverPath = "G:/spider/ptncp/cover/"
    if not os.path.exists(imgPath):
        os.mkdir(imgPath)

    imgFile = imgPath + "/" + imgName
    newImgUrl = "http://ssfk-media01.oss-cn-shenzhen.aliyuncs.com/ptncp/" + imgDir + "/" + imgName
    # file(imgFile, "w").truncate()
    # urllib.urlretrieve(downImg, imgFile)
    do_update_image(downImg, imgFile)
    if idx == 0:
        coverFile = coverPath + imgDir + ".jpg"
        open(coverFile, "wb").write(open(imgFile, "rb").read())
        # file(coverFile, "w").truncate()
        # urllib.urlretrieve(downImg, coverFile)
        # do_update_image(downImg, coverFile)
        coverUrl = "http://ssfk-media01.oss-cn-shenzhen.aliyuncs.com/ptncp/" + imgDir + "/cover.jpg"
        pDao.updateProductCover(pId, coverUrl)

    return newImgUrl


def updateImgsNeedDL(global_param):
    # 初始化数据库连接
    conn = get_conn()
    if conn is None:
        print("没有此数据库")
        return False
    cur = conn.cursor()

    # 初始化dao
    piDao = ProductImagesDao(conn, cur)
    pDao = ProductDao(conn, cur)

    pDatas = piDao.getNeedDownLoadImgs()
    for item in pDatas:
        prodId = item[0]
        imgsStr = item[1]
        if (len(imgsStr) > 0):
            imgsArr = imgsStr.split(",")
            newImgsStr = ""
            for imgIdx in range(len(imgsArr)):
                imgPath = downAndUpImg(imgsArr[imgIdx], prodId, imgIdx, pDao)
                imgPath = "".join(['"', imgPath, '"'])
                newImgsStr = "".join([newImgsStr, ",", imgPath])
            slen = len(newImgsStr)
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
    pro1 = multiprocessing.Process(target=updateImgsNeedDL, args=(global_param,))
    pro1.start()
    f_pid = pro1.pid
    while True:
        b = global_param["count"]
        if b == 36109:
            os.popen('taskkill.exe /pid:' + str(f_pid))
            print "end"
            return
        time.sleep(90)
        c = global_param["count"]
        if b == c:
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