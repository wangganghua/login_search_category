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
import os

default_encoding = "utf-8"
if sys.getdefaultencoding() != default_encoding:
    reload(sys)
    sys.setdefaultencoding(default_encoding)
# sys.setrecursionlimit(1000000)
# 亦庄
# rconnection_yz = redis.Redis(host='117.122.192.50', port=6479, db=0)
# 西安
# rconnection_yz = redis.Redis(host='117.23.4.139', port=15480, db=0)
rconnection_yz = redis.Redis(host='192.168.2.245', port=6379, db=0)
rconnection_test = redis.Redis(host='192.168.2.245', port=6379, db=0)
# 代理ip
redis_key_proxy = "proxy123:iplist"
redis_url_key = "dpc_maijiawang:url_list"
# user = "avcspider"
# pwd = "aowei123"

cookies = "auth=5b21f3cclksjfldjflaskjflfaadc716994841b4aa29415a8d0"


# 加载cookie
def loadcookie(category):
    try:
        if "智能手机" in category or "投影仪" in category:
            r_cookies = open("cookies_sj.txt", "r")  # 读取配置cookies
        else:
            r_cookies = open("cookies.txt", "r")  # 读取配置cookies
        if r_cookies:
            ctxt = r_cookies.read()
            cookvalue = json.loads(ctxt)
            cookies = cookvalue["Cookie"]
            r_cookies.close()
            return cookies
    except Exception, e:
        print "cookie error: %s " % e
        r_cookies.close()
        return ""

# 开始采集


def search(cid, savedfilename):
    tmsc = "天猫商城".encode("gbk")
    path = os.path.abspath(".") + "\\" + datetime.now().strftime("%Y%m%d") + "\\" + tmsc
    if os.path.exists(path):
        print path
    else:
        cdend = (datetime.now().strftime("%Y%m%d") + "\\" + "天猫商城").encode("gbk")
        os.makedirs(cdend)

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
        cookies = loadcookie(savedfilename)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:52.0) Gecko/20100101 Firefox/52.0",
            "Cookie": cookies
        }
        # 随机获取代理ip
        proxy = rconnection_yz.srandmember(redis_key_proxy)
        proxyjson = json.loads(proxy)
        proxiip = proxyjson["ip"]
        openurl.proxies = {'http': 'http://' + proxiip, 'https': 'https://' + proxiip}
        # 若你的代理需要使用HTTP Basic Auth，可以使用 http: // user:password @ host / 语法：eg： "http": "http://user:pass@10.10.1.10:3128/",
        # openurl.proxies = {'http': 'http://'+user+':'+pwd+'@' + proxiip+'/', 'https': 'https://'+user+':'+pwd+'@' + proxiip+'/'}
        url = "http://www.maijia.com/data/industry/hotitems/list?cid={0}&brand=&type=B&date=&pageNo={1}&pageSize=60&orderType=desc".format(cid, intPage)
        try:
            time.sleep(1)
            print "第 %s 页 : %s" % (intPage, url)
            time.sleep(2)
            req = openurl.get(url, headers=headers, timeout=25)
            intPage += 1
            if req:
                data = json.loads(req.text)
                try:
                    print data["message"]
                    if "重新登录" in data["message"] or "未监控该行业" in data["message"]:
                        time.sleep(1)
                        login(savedfilename)    # 重新登陆获取新的cookie
                except Exception, e:
                    pass
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
                    try:
                        zhanggui = i["sellerNick"]
                    except Exception,e:
                        zhanggui = ""
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
            openurl.keep_alive = False
        except Exception, e:
            print "errormessage : %s" % e
            # # 删除无效的 ip
            if "timeout" not in e:
                rx = rconnection_yz.srem(redis_key_proxy, proxy)
            #     print rx
            if intPage > 1:
                intPage -= 1
                time.sleep(1)


def run():
    global urldata
    if urldata:
        url_list = str(urldata.pop()).decode("gbk")
        value = json.loads(url_list)
        regeid = re.search("(?<=\?cid=)\d+", value["url"])
        search(regeid.group(), value["category"])
    else:
        print "读取txt url结束,等待1分钟"


def beginwork(istrue):
     global urldata
     urldata = []
     if istrue:
         w_url = open("dataurl.txt")
         if w_url:
             urldata = w_url.readlines()
         w_url.close()
     else:
         print "select all--------------------------------------------------------------"
         urldata = selectall()
     isTrue = True
     while isTrue:
         if len(urldata) > 0:
             threads = []
             threadcount = 20
             for ai in range(threadcount):
                 threads.append(threading.Thread(target=run, args=()))
             for tx in threads:
                 tx.start()
             for tx in threads:
                 tx.join()
             print "end thread : %s" % datetime.now()
             isTrue = True
         else:
             print "等txt待1分钟"
             isTrue = False
             # time.sleep(60)

# 登陆


def login(category):
    print "重新登陆获取cookie"
    post_url = "https://login.maijia.com/user/login?style=login_index&redirectURL=https%3A%2F%2Flogin.maijia.com%2Flogin%2Fforward.htm%3FredirectURL%3Dhttp%253A%252F%252Fwww.maijia.com%252F"
    post_data = urllib.urlencode({
        # "loginCode": "18053276660",
        # "loginPassword": "xiaoxin123"
        "loginCode": "13716810221",
        "loginPassword": "19890305hua"
    })
    if "智能手机" in category or "投影仪" in category:
        post_data = urllib.urlencode({
            "loginCode": "17710828639",
            "loginPassword": "123456"
        })
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:52.0) Gecko/20100101 Firefox/52.0",
        "Referer": "http://www.maijia.com/"
    }
    proxy = rconnection_yz.srandmember(redis_key_proxy)
    proxyjson = json.loads(proxy)
    proxiip = proxyjson["ip"]
    try:
        # proxy_support = urllib2.ProxyHandler({"http": "http://"+user+":"+pwd+"@%s" % proxiip})
        proxy_support = urllib2.ProxyHandler({"http": "http://%s" % proxiip})
        cj = cookielib.LWPCookieJar()
        cookie_support = urllib2.HTTPCookieProcessor(cj)
        opener = urllib2.build_opener(cookie_support, proxy_support)
        urllib2.install_opener(opener)
        requestx = urllib2.Request(post_url, post_data, headers=headers)
        urllib2.urlopen(requestx)
        print str(cj).split(' ')[1]
        wrcookie = '{"Cookie":"%s"}' % str(cj).split(' ')[1]
        print wrcookie
        if "智能手机" in category or "投影仪" in category:
            fwritecookie = open("cookies_sj.txt", "w")
            fwritecookie.writelines(wrcookie)
            fwritecookie.close()
        else:
            fwritecookie = open("cookies.txt", "w")
            fwritecookie.writelines(wrcookie)
            fwritecookie.close()

    except Exception, e:
        # rx = rconnection_yz.srem(redis_key_proxy, proxy)
        # print rx
        print e


def image():
    images = Image.open("a.jpg")
    enhancer = ImageEnhance.Contrast(images)

    im = enhancer.enhance(2)
    images1 = im.convert("1")
    data = images1.getdata()
    w, h = images1.size
    print images1.size
    block_point = 0
    for x in xrange(1, w-1):
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

    # images1.show()
    threshold = 140
    table = []
    for i in range(256):
        if i < threshold:
            table.append(0)
        else:
            table.append(1)
    out = images1.point(table, "1")
    out.show()
    txt = image_to_string(out)
    print txt


def openbeginwork():
     while True:
        str_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print str_time
        # 0-6 weekday 代表:周一 -- 周日
        if datetime.now().weekday() >= 5:   # 周六、日时间 下午 18点开始采集
            if "18:30:00" in str_time:
                print datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                beginwork(True)
                print "end "
                select = selectall()
                if len(select) > 0:
                    beginwork(False)
                print datetime.now()
                time.sleep(1)
            else:
                print u"周末下午采集"
                select = selectall()
                if len(select) > 0:
                    beginwork(False)
                time.sleep(1)
        else:   # 正常时间 为 9：05点开始采集
            if "08:38:00" in str_time:
                print datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                beginwork(True)
                print "end "
                select = selectall()
                if len(select) > 0:
                    beginwork(False)
                print datetime.now()
                time.sleep(1)
            else:
                select = selectall()
                if len(select) > 0:
                    beginwork(False)
                print "spider mai jia wang"
                time.sleep(1)

# 查找是否漏采集


def selectall():
    #  查找文件个数
    #   标准的品类list
    correctly_category = []
    #   采集文件品类list
    file_category = []
    #   保存原始的品类数据
    correctly_info_category = []
    path = os.path.abspath(".") + "\\" + datetime.now().strftime("%Y%m%d") + "\\天猫商城".encode("gbk")
    for i in os.walk(path):
        for ix in i[2]:
            file_category.append(ix.decode("gbk").replace("_最近7天.xls", ""))
    #   读取txt文件的品类
    w_url = open("dataurl.txt")
    if w_url:
        correctly_info_category = w_url.readlines()
    w_url.close()
    for i in correctly_info_category:
        jscategory = json.loads(str(i).decode("gbk"))
        correctly_category.append(jscategory["category"])
    # 求list 差集
    list_difference = list(set(correctly_category).difference(set(file_category)))
    list_differences = []
    for i in list_difference:
        for a in correctly_info_category:
            if i in str(a).decode("gbk"):
                # print str(a).decode("gbk")
                list_differences.append(str(a))
    # 清除
    correctly_category = []
    file_category = []
    correctly_info_category = []
    return list_differences

if __name__ == "__main__":
    # login("智能手机")
    openbeginwork()
# login()
# openbeginwork()
# image()
# run()
# print  str(int(time.time() * 1000))
# import uuid
# print str(uuid.uuid1()).upper()
# # print uuid.uuid3("","")
# print str(uuid.uuid4()).upper()
#
# add={"Cookie":"ddddd"}
# print add["Cookie"]
