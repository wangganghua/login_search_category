#!/usr/bin/python
# -*- coding:utf-8 -*-

import requests
import json
import sys
import xlwt
import redis
import threading
import re
import time
import cookielib
import urllib2
import urllib
from PIL import Image, ImageEnhance
from datetime import datetime
from pytesser import *
import cStringIO
import os

default_encoding = "utf-8"
if sys.getdefaultencoding() != default_encoding:
    reload(sys)
    sys.setdefaultencoding(default_encoding)
# sys.setrecursionlimit(1000000)
rconnection_yz = redis.Redis(host='117.122.192.50', port=6479, db=0)
rconnection_test = redis.Redis(host='192.168.2.245', port=6379, db=0)
# 代理ip
redis_key_proxy = "proxy:iplist4"
redis_url_key = "dpc_maijiawang:url_list"
cookies = "encentSig=3598261248; Hm_lvt_8c619410770b1c3446a04be9cfb938f7=1490604155,1490605167,1490663171,1490666286; _qddaz=QD.kq926r.pqmz8c.j0sud4s5; Hm_lpvt_8c619410770b1c3446a04be9cfb938f7=1490750407; _qddab=3-x88bfb.j0uaaqek; auth=ed3fcddf4f617e24fc99d8c94d3ab9742039210e; __nick=1; mjcc=e3ea0b817e4d2bdcad3fb82d6654838e38c9681b; _qdda=3-1.1; _qddamta_800098528=3-0"
# try:
#     r_cookies = open("cookies.txt", "r")  # 读取配置cookies
#     if r_cookies:
#         ctxt = r_cookies.read()
#         cookvalue = json.loads(ctxt)
#         cookies = cookvalue["Cookie"]
# except Exception, e:
#     print "cookie error: %s " % e


def search(cid, savedfilename):
    tmsc = "天猫商城".encode("gbk")
    path = os.path.abspath(".") + "\\" + datetime.now().strftime("%Y%m%d") + "\\" + tmsc
    if os.path.exists(path):
        print path
    else:
        cdend = (datetime.now().strftime("%Y%m%d") + "\\" + "天猫商城").encode("gbk")
        os.makedirs(cdend)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:52.0) Gecko/20100101 Firefox/52.0",
        "Cookie": cookies
    }
    tm_url ="http://detail.tmall.com/item.htm?id={0}&amp;areaid=&amp;"
    openurl = requests.session()
    # excel 标题
    booktitle = ["宝贝名称", "宝贝链接", "掌柜", "信用", "标价", "成交价", "销售量", "销售金额"]
    workbook = xlwt.Workbook(encoding="utf-8", style_compression=0)  # 创建一个workbook
    sheet = workbook.add_sheet("sheet1", cell_overwrite_ok=True)  # 添加一个sheet
    index_title = 0
    for i in booktitle:
        sheet.write(0, index_title, i)
        index_title += 1
    isTrue = True
    index = 1
    intPage = 1
    while isTrue:
        # 随机获取代理ip
        proxy = rconnection_yz.srandmember(redis_key_proxy)
        proxyjson = json.loads(proxy)
        proxiip = proxyjson["ip"]
        openurl.proxies = {'http': 'http://' + proxiip, 'https': 'https://' + proxiip}
        url = "http://www.maijia.com/data/industry/hotitems/list?cid={0}&brand=&type=B&date=&pageNo={1}&pageSize=60&orderType=desc".format(cid, intPage)
        try:
            print "第 %s 页 : %s" % (intPage, url)
            req = openurl.get(url, headers=headers, timeout=10)
            intPage += 1
            if req:
                data = json.loads(req.text)
                if data["result"] == 501:
                    print "等待10s"
                    time.sleep(10)
                    continue
                wj = data["data"]["list"]
                if len(wj) == 0:
                    isTrue = False
                    filename = ("{0}_最近7天.xls".format(savedfilename)).encode("gbk")
                    print "save file [ %s ] success" % filename
                    workbook.save(path + "\\" + filename)  # 保存
                for i in wj:
                    baobei = i["title"]
                    lianjie = tm_url.format(i["id"])
                    zhanggui = i["sellerNick"]
                    xinyong = "天猫"
                    biaojia = i["oriPrice"]
                    chengjiaojia = i["price"]
                    xiaoliang = i["amount30"]
                    xiaoe = i["price30"]
                    sheet.write(index, 0, baobei)
                    sheet.write(index, 1, lianjie)
                    sheet.write(index, 2, zhanggui)
                    sheet.write(index, 3, xinyong)
                    sheet.write(index, 4, biaojia)
                    sheet.write(index, 5, chengjiaojia)
                    sheet.write(index, 6, xiaoliang)
                    sheet.write(index, 7, xiaoe)
                    index += 1
        except Exception, e:
            print "errormessage : %s" % e
            if intPage > 1:
                intPage -= 1
            # time.sleep(10)


def run():
    url_list = rconnection_test.lpop(redis_url_key)
    if url_list:
        value = json.loads(url_list)
        regeid = re.search("(?<=\?cid=)\d+", value["url"])
        search(regeid.group(), value["category"])
    else:
        print "读取url结束,等待1分钟"


def beginwork():
    while True:
        url_l = rconnection_test.lrange(redis_url_key, 0, -1)
        if len(url_l) > 0:
            threads = []
            threadcount = 7
            for ai in range(threadcount):
                threads.append(threading.Thread(target=run, args=()))
            for tx in threads:
                tx.start()
            for tx in threads:
                tx.join()
            print "end thread : %s" % datetime.now()
        else:
            print "等待1分钟"
            time.sleep(60)


def login():
    login_url = "https://login.maijia.com"
    post_url = "https://login.maijia.com/user/login?redirectURL="
    data = urllib.urlencode({"loginCode": "18053276660", "loginPassword": "xiaoxin123"})

    getUrl = login_url
    print getUrl

    url = "http://www.maijia.com/industry/index.html#/data/hotitems/?cid=50016465&pcid=4&brand=&type=B&date=&pageNo=1"
    try:
        # request = urllib2.Request(getUrl, headers=headers)
        # response = urllib2.urlopen(url)
        # print response.read()

        cj = cookielib.LWPCookieJar()
        cookie_support = urllib2.HTTPCookieProcessor(cj)
        opener = urllib2.build_opener(cookie_support, urllib2.HTTPHandler)
        urllib2.install_opener(opener)

        h = urllib2.urlopen(login_url)
        headers = {
            "User-Agent":"Mozilla/5.0 (Windows NT 6.1; WOW64; rv:52.0) Gecko/20100101 Firefox/52.0",
            "Referer":"http://www.maijia.com/"
        }
        rquest = urllib2.Request(post_url, data, headers)
        print rquest
        response = urllib2.urlopen(rquest)
        txt = response.read()
        print txt


        #     cj = cookielib.CookieJar()
    #     openner = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    #     print openner
    #     openner.addheaders=[('User-agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:52.0) Gecko/20100101 Firefox/52.0')]
    #     openner.open(login_url, data)
    #     op = openner.open(url)
    #     txt = op.read()
    #     print txt
    except Exception, e:
        print e


def image():
    images = Image.open("1.png")
    enhancer = ImageEnhance.Contrast(images)
    im = enhancer.enhance(2)
    images1 = im.convert("1")
    data = images1.getdata()
    w, h = images1.size
    print images1.size
    block_point = 0
    for x in xrange(1,w-1):
        for y in xrange(1, h-1):
            mid_pixel = data[w*y + x]   # 中央像素点 值
            if mid_pixel == 0:  # 找寻上、下、左、右四个方位的像素值
                top_pixel = data[w*(y-1) + x]
                left_pixel = data[w*y + (x-1)]
                down_pixel = data[w*(y+1) + x]
                right_pixel = data[w*y + (x+1)]
                # 判断上下左右的黑色像素点总个数
                if top_pixel == 0:
                    block_point += 1
                if left_pixel == 0:
                    block_point += 1
                if down_pixel == 0:
                    block_point += 1
                if right_pixel == 0:
                    block_point += 1
                if block_point >= 3:
                    images1.putpixel((x, y), 0)
                block_point = 0

    images1.show()
    # threshold = 140
    # table = []
    # for i in range(256):
    #     if i < threshold:
    #         table.append(0)
    #     else:
    #         table.append(1)
    # out = images1.point(table, "1")
    # out.show()
    # txt = image_to_string(out)
    # print txt

# login()
beginwork()
# image()
