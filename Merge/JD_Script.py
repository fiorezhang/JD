#-*- coding: utf-8 -*-

# ================================================================  #
#                                                                   #
#                    INTERNAL STUDY ONLY !                          #
#                        VERSION 7.4                                #
#                                                                   #
# ================================================================  #

import os
import requests
import urllib.request
from lxml import etree
import re
import json
import csv
import pandas
import numpy
import argparse
import time
import sys
from collections import Counter
import matplotlib.pyplot as plt
from wordcloud import WordCloud, STOPWORDS
import jieba
import imageio
import cv2
from PIL import ImageFont, ImageDraw, Image

# ======== COOKIE FOR WEB REQUEST ========
#cookie需要timely更新，否则影响抓取comment等等功能（退出再登陆，页面刷新，控制台-网络-搜索'club'-请求标头-cookie，删除thor这一项）
COOKIE = "__jdu=1662379846916272156429; shshshfpa=d99c5362-8a4b-a678-0024-58552f251967-1665473602; shshshfpb=iBuenWAhnUwZUs_Jf4CzWUA; TrackID=1YK2pXdZgAd6aZmz8KNcMcxp70DtjlW1eirjhGicSFs7oI2jGQqvkae32IZxw6MGR444uv27SvxAHPQtcsLo8KB_gbqDOnplZlqN1sgo1i2lb6wZ1pHYxgZ1n5oiOmsjb; pinId=lSwRbMKd-74tBDbKmwsL1w; pin=FioreZhang; unick=FioreZhang; _tp=IcTvqSKCNvN8JKtp2uhsOg==; _pst=FioreZhang; __jdv=76161171|direct|-|none|-|1668993673036; PCSYCityID=CN_310000_310100_0; jsavif=0; __jda=122270672.1662379846916272156429.1662379847.1667356629.1668993673.13; __jdc=122270672; shshshfp=80d8ef1a0606c264960f09f5e2bc236b; areaId=2; token=ae4c9f56f95861a472004865e50c72de,2,927218; __tk=jifolUeFJUuqkvn1Isq1JvkikUtEkpeyIDJilcaxJpG0jzIFjUnzJn,2,927218; ip_cityCode=2817; ipLoc-djd=2-2817-51973-0; 3AB9D23F7A4B3C9B=ZOEVZOLRXLAUYWGYULQOKKHNLEAI7UOZRJHAVT7FQIUXREAPSHYQPPA2QJBCKBUQDQDK4RGCEXEDSUW4HLIL62DJNU; __jdb=122270672.5.1662379846916272156429|13.1668993673; shshshsID=f26bc4f06c6de120ede89d866cb8c380_5_1668993721789"
#cookie需要timely更新，否则影响抓取comment等等功能（退出再登陆，页面刷新，找一个海外购商品页面，控制台-网络-第一行当前页面-请求标头-cookie，删除thor这一项）
COOKIE_EX = "shshshfpa=862a6605-db4a-6154-47e5-af19cfa7c8bf-1664271435; __jdv=181809404|search.jd.com|-|referral|-|1664271435321; shshshfpb=whRyyEaaTJJ9UrwxkKsPvPg; areaId=2; ipLoc-djd=2-2817-51973-0; shshshfp=4fb4889ad884f65329321193d8b66aa0; __jdc=181809404; 3AB9D23F7A4B3C9B=IABYFHSAZ5YE4JK67BOOHWXZM3E3Q6LHRDFAOMFFBNIQYMWUZOXRA33UAIVOJD5FAGMHAXRKCCL2HARJ4LAJGRSQHE; shshshsID=feb97181256df9fca61850206dfd023e_1_1665448565902; __jda=181809404.1664271435320884582036.1664271435.1665420953.1665448566.6; __jdb=181809404.1.1664271435320884582036|6.1665448566"

USERAGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:105.0) Gecko/20100101 Firefox/105.0"

# ======== MACROS ========
MAXPAGE = 100
TIMEOUT = 10
RETRY = 1
NUMTAGS = 12
FILE_CONFIG_MASTER = "configMaster.csv"
FILE_CONFIG_DETAIL = "configDetail.csv"
FILE_CONFIG_FILTER = "configFilter.csv"
FILE_CONFIG_COMMENT = "configComment.csv"
FILE_CONFIG_EXTRACT = "configExtract.csv"
SPECIAL_SPLIT = "█"
SPECIAL_ID_HEAD = "_"

#表头
# "年", "月", "日", "星期", "时间", "ID", "LINK", "京东页数", "销量排名", "商品全名", "虚价", "原价", "价格", "店铺", "京东自营", "品牌", SPECIAL_SPLIT, =INDEX=, SPECIAL_SPLIT, =DETAIL=, SPECIAL_SPLIT, "好评率", "中评率", "差评率", "好评数", "中评数", "差评数"

HELP  = "---------------------------------------------------------------------------------------------\n"
HELP += "==  JD Script to capture data from end-user interface                                      ==\n"
HELP += "==                                                                                         ==\n"
HELP += "==  Usage:                                                                                 ==\n"
HELP += "==         --search x: Search for segment[x] from configMaster.csv                         ==\n"
HELP += "==           --count x: Plan to capture x+ skus for current segment                        ==\n"
HELP += "==           --setup 1/0: Turn on/off generate parameter for current segment               ==\n" 
HELP += "==           --filter: Input URL with filters for current segment                          ==\n"
HELP += "==         --extract 1/0: Turn on/off extract function                                     ==\n"
HELP += "==           --profile x: Load extract parameters from configExtract.csv                   ==\n"
HELP += "==           --inputfile: Provide input csv file with original data                        ==\n" 
HELP += "==           --outputfile: Provide output csv file path for extracted data                 ==\n"
HELP += "==         --comment 1/0: Turn on/off capture comments function                            ==\n"
HELP += "==           --text 1/0: Turn on/off comments list and excel function                      ==\n"
HELP += "==           --sku x: Capture comments for sku x                                           ==\n"
HELP += "==           --index x: Capture comments for index x in configComment.csv                  ==\n"
HELP += "==                                                                                         ==\n"
HELP += "==  Examples:                                                                              ==\n"
HELP += "==         python jd.py --search 2 --count 100                                             ==\n"
HELP += "==           Capture data for 100+ top volume skus for segment[2]                          ==\n"
HELP += "==         python jd.py --search 2 --filter 1 --count 100                                  ==\n"
HELP += "==           Capture data for 100+ top volume skus for segment[2] filter[1]                ==\n"
HELP += "==         python jd.py --search 3 --setup 1                                               ==\n"
HELP += "==           Generate parameters in configDetail.csv for segment[3]                        ==\n"
HELP += "==         python jd.py --extract 1 --profile 0 --inputfile 'a.csv' --outputfile 'b.csv'   ==\n"
HELP += "==           According to profile 0, extract data from a.csv to b.csv                      ==\n"
HELP += "==         python jd.py --comment 1 --sku 10000 --text 1                                   ==\n"
HELP += "==           Capture comments for sku 10000, and generate text and csv                     ==\n"
HELP += "==         python jd.py --comment 1 --index all                                            ==\n"
HELP += "==           Capture comments for all categories in config file                            ==\n"
HELP += "==         python jd.py --comment 1 --index 2                                              ==\n"
HELP += "==           Capture comments for category 2 in config file                                ==\n"
HELP += "==                                                                                         ==\n"
HELP += "---------------------------------------------------------------------------------------------\n"


# ======== MISC ========
#剥离skuname并去除无用字符
def getSkuname(listSkuname):
    skuname = ""
    if listSkuname != [] and listSkuname != None:
        for item in listSkuname:
            skuname = item.strip()
            if skuname != "":
                break

    #print(listSkuname)
    #print(skuname)
    
    return skuname

def normalizeCountStr(countStr):
    countStr_1 = countStr.rstrip('+')
    countStr_2 = countStr_1.rstrip('万')
    if countStr_2 == countStr_1:
        count = int(countStr_2)
    else:
        count = int(10000 * float(countStr_2))
    return count

def getRankPage(sku, skupagelist):
    page = ""
    for skupagenum, skupage in enumerate(skupagelist):
        if sku in skupage:
            break
    page = str(skupagenum + 1)
    return page

def getRankSku(sku, skulist):
    if sku in skulist:
        return skulist.index(sku) + 1
    else:
        return 0

#写入CSV文件
def appendCsv(file, row):
    with open(file, mode='a', newline='', encoding='utf-8-sig') as f:
        write=csv.writer(f)
        write.writerow(row)
        f.close

#读出CSV文件
def parseCsv(file):
    rows = []
    with open(file, mode='r', encoding='utf-8-sig') as f:
        read=csv.reader(f)
        rows = [row for row in read]
        f.close
    return rows

#保存文件时候, 去除名字中的非法字符
def validateTitle(title):
    rstr = r"[\t\/\\\:\*\?\"\<\>\|.]"  # '/ \ : * ? " < > |'
#    rstr = r"[\*\?\"\<\>\|]"  # '/ \ : * ? " < > |'
    new_title = re.sub(rstr, r"_", title)  # 替换为下划线
    new_title = new_title.rstrip()
    #new_title = new_title.replace(" ", "")
    return new_title

#创建新目录
def mkdir(path):
    path = path.strip()
    # 判断路径是否存在
    # 存在     True
    # 不存在   False
    isExists=os.path.exists(path)
    #print(isExists)
    # 判断结果
    if not isExists:
        # 如果不存在则创建目录
        # 创建目录操作函数
        os.makedirs(path)
        return True
    else:
        # 如果目录存在则不创建，并提示目录已存在
        return False  


# ======== CAPTURE LIST OF SKU ========
#JD页面每一页默认刷新30个物品，下拉后再刷新30个。所以需要对于每一页分上下部分分别处理。
#抓取上半页的物品sku number
def getListPageUp(keyword, url, page):
    #对上半页，简单的构建header即可
    head = {'authority': 'search.jd.com',
            'method': 'GET',
            'scheme': 'https',
            'User-Agent': USERAGENT,
            }
    #对上半页，构造请求的页面
    if url == None:
        urlPage = 'https://search.jd.com/Search?keyword='+str(keyword)+'&enc=utf-8&page='+str(2*page-1)+'&psort=3'
    else:
        urlPage = url + '&page='+str(2*page-1)+'&psort=3'

    #获得页面HTML
    response = requests.get(urlPage, headers=head)
    response.encoding = 'utf-8'
    htmltree = etree.HTML(response.text)
    
    #定位每一个sku的标签，在class=gl-item的li中
    skus = htmltree.xpath('//li[contains(@class,"gl-item")]')
    
    #获取所有sku的sku number
    skulist = [sku.xpath('@data-sku')[0] for sku in skus]
    if len(skulist) == 0:
        print("    == Error getting new page(1st half), or No more item for this search", page)

    return skulist

#抓取下半页的物品sku number
def getListPageDown(keyword, url, page): 
    #对下半页，构建header时需要包入referer等元素
    head = {'authority': 'search.jd.com',
            'method': 'GET',
            'scheme':'https',
            'referer': 'https://search.jd.com/Search?keyword=PC&enc=utf-8',
            'User-Agent': USERAGENT,
            'x-requested-with': 'XMLHttpRequest',
    }
    #对下半页，构造请求的页面
    timestp = '%.5f'%time.time() #获取当前的Unix时间戳，并且保留小数点后5位
    if url == None: 
        urlPage = 'https://search.jd.com/s_new.php?keyword='+str(keyword)+'&enc=utf-8&page='+str(2*page)+'&psort=3&s='+str(48*page-20)+'&scrolling=y&log_id='+str(timestp)
    else:
        urlPage = url + '&page='+str(2*page)+'&psort=3&s='+str(48*page-20)+'&scrolling=y&log_id='+str(timestp)

    #获得页面HTML
    response = requests.get(urlPage, headers=head)
    response.encoding = 'utf-8'
    htmltree = etree.HTML(response.text)
    
    #定位每一个sku的标签，在class=gl-item的li中
    skus = htmltree.xpath('//li[contains(@class,"gl-item")]')
    
    #获取所有sku的sku number
    skulist = [sku.xpath('@data-sku')[0] for sku in skus]
    if len(skulist) == 0:
        print("    == Error getting new page(2nd half), or No more item for this search", page)
 
    return skulist

#根据指定的关键字以及sku数，返回所有满足条件的sku number（已经去重）
def getList(keyword, url, countnum):
    skulist = []
    skupagelist = []
    for page in range(1, MAXPAGE):
        print("Getting sku list for Page "+str(page))
        #获得每页上半页，如果没有新的sku就跳出循环
        skulistUpdate = getListPageUp(keyword, url, page)
        if len(skulistUpdate) == 0:
            break
        skulist += skulistUpdate
        skupagelist.append(skulistUpdate)
        #获得每页下半页，如果没有新的sku就跳出循环
        skulistUpdate = getListPageDown(keyword, url, page)
        if len(skulistUpdate) == 0:
            break
        skulist += skulistUpdate
        skupagelist.append(skulistUpdate)
        #去重
        skulistold = skulist
        skulist = sorted(list(set(skulist)), key = skulistold.index)
        #如果超过希望抓取的sku数量就跳出循环
        if len(skulist) >= countnum:
            break
        time.sleep(3)   #慢一点……
    
    return skulist, skupagelist

# ======== CAPTURE PRICE ========
#旧的接口，通过p.3.cn托管价格数据，2022年9月开始疑似废弃
'''
def getPrice_Legacy(sku):
    head = {'User-Agent': USERAGENT, 
            'Cookie': COOKIE}  
    url = 'https://p.3.cn/prices/mgets?skuIds=J_'+str(sku)
    
    price = None
    retry = RETRY
    while retry > 0:
        try:
            request = urllib.request.Request(url, headers=head)
            response = urllib.request.urlopen(request, timeout=TIMEOUT)
            content = response.read()
            result = json.loads(content)
            price = result[0]['p']
        except:
            pass
        else:
            break
        retry -= 1
        ##print("    == Retry getPrice(), can fix occational network lag")
        time.sleep(2)
    #print(price)
    return price
    
#新的接口，通过fts.jd.com查询价格信息
def getPrice_Legacy_2(sku):
    head = {'User-Agent': USERAGENT, 
            'Cookie': COOKIE, 
            'Referer': 'https://item.jd.com'}  
    url = 'https://fts.jd.com/prices/mgets?callback=jQuery&skuIds=J_'+str(sku)+'&source=pc-item'
    
    #print(url)
    price_m = None
    price_op = None
    price_p = None
    retry = RETRY
    while retry > 0:
        try:
            request = urllib.request.Request(url, headers=head)
            response = urllib.request.urlopen(request, timeout=TIMEOUT)
            content = response.read().decode()
            pattern = re.compile('"m":"(.*?)"')
            price_m = re.search(pattern, content).group(1)
            pattern = re.compile('"op":"(.*?)"')
            price_op = re.search(pattern, content).group(1) 
            pattern = re.compile('"p":"(.*?)"')
            price_p = re.search(pattern, content).group(1)            
        except:
            pass
        else:
            break
        retry -= 1
        ##print("    == Retry getPrice(), can fix occational network lag")
        time.sleep(2)
    #print(price)
    return price_m, price_op, price_p    
'''
    
#新的接口，通过pctradesoa_getprice查询价格信息
def getPrice(sku):
    head = {'User-Agent': USERAGENT, 
            'Cookie': COOKIE, 
            'Referer': 'https://item.jd.com'}  
    url = 'https://api.m.jd.com/?appid=item-v3&functionId=pctradesoa_getprice&client=pc&clientVersion=1.0.0&body={"skuIds":"' + str(sku) + '","source":"pc-item"}'
    
    #print(url)
    price_m = None
    price_op = None
    price_p = None
    retry = RETRY
    while retry > 0:
        try:
            request = urllib.request.Request(url, headers=head)
            response = urllib.request.urlopen(request, timeout=TIMEOUT)
            content = response.read().decode()
            pattern = re.compile('"m":"(.*?)"')
            price_m = re.search(pattern, content).group(1)
            pattern = re.compile('"op":"(.*?)"')
            price_op = re.search(pattern, content).group(1) 
            pattern = re.compile('"p":"(.*?)"')
            price_p = re.search(pattern, content).group(1)            
        except:
            pass
        else:
            break
        retry -= 1
        ##print("    == Retry getPrice(), can fix occational network lag")
        time.sleep(2)
    #print(price)
    return price_m, price_op, price_p    

# ======== CAPTURE COMMENTS ========       
'''
def getCommentRate(sku):
    head = {'User-Agent': USERAGENT, 
            'Cookie': COOKIE, 
            'Referer': 'https://item.jd.com'}  
    url = 'https://club.jd.com/comment/productCommentSummaries.action?referenceIds=' + str(sku) + '&categoryIds='
    
    #print(url)
    #html = requests.get(url)
    #print(html.status_code)
    
    #获得原始评论页面的数据，提取总结部分与标签部分的数据
    retry = RETRY
    while retry > 0:
        try:
            request = urllib.request.Request(url, headers=head)
            response = urllib.request.urlopen(request, timeout=TIMEOUT)
            content = response.read().decode('gbk')
            #print(content)

            result = json.loads(content)
            summary = result['CommentsCount'][0]
            #print(summary)
            if summary != "" and summary != None:
                break
        except Exception as ex:
            pass            
        retry -= 1
        ##print("    == Retry getCommentRate(), can fix occational network lag")
        time.sleep(2)
    
    #提取好评率，中评率，差评率
    commentSummary = [0, 0, 0, 0, 0, 0]
    try:
        commentSummary = [summary['GoodRate'], summary['GeneralRate'], summary['PoorRate'], normalizeCountStr(summary['GoodCountStr']), normalizeCountStr(summary['GeneralCountStr']), normalizeCountStr(summary['PoorCountStr'])]
    except:
        pass
    #print(commentSummary)

    return commentSummary
'''

def getCommentRate(sku):
    head = {'User-Agent': USERAGENT,  
            'Cookie': COOKIE, 
            'Referer': 'https://item.jd.com'}  
    head_ex = {'User-Agent': USERAGENT,  
            'Cookie': COOKIE_EX, 
            'Referer': 'https://item.jd.com'}          
            
    url = 'https://sclub.jd.com/comment/skuProductPageComments.action?&productId=' + str(sku) + '&score=0&sortType=5&page=0&pageSize=10&isShadowSku=0&fold=1'
    #print(url)
    #html = requests.get(url)
    #print(html.status_code)
    
    #提取最多多少条标签，电脑页面大部分tag数量是11个及以内
    numTags = NUMTAGS
    
    #获得原始评论页面的数据，提取总结部分与标签部分的数据
    tags = []
    retry = RETRY
    while retry > 0:
        #一般场景，国内商品，可能使用了不同的编码格式，分别尝试
        try:        
            request = urllib.request.Request(url, headers=head)
            response = urllib.request.urlopen(request)
            content = response.read().decode('gbk')
            #print(content)

            result = json.loads(content)
            summary = result['productCommentSummary']
            #tags = result['hotCommentTagStatistics']
            if summary != "" and summary != None:
                break
        except Exception as ex:
            pass  
        try:        
            request = urllib.request.Request(url, headers=head)
            response = urllib.request.urlopen(request)
            content = response.read().decode('gb2312')
            #print(content)

            result = json.loads(content)
            summary = result['productCommentSummary']
            #tags = result['hotCommentTagStatistics']
            if summary != "" and summary != None:
                break
        except Exception as ex:
            pass                        
        #特殊场景，海外购，url和cookie都不一样    
        try:    
            request = urllib.request.Request(url, headers=head_ex)
            response = urllib.request.urlopen(request)
            content = response.read().decode('gbk')
            #print(content)

            result = json.loads(content)
            summary = result['productCommentSummary']
            #tags = result['hotCommentTagStatistics']
            if summary != "" and summary != None:
                break           
        except Exception as ex:
            pass            
        retry -= 1
        ##print("    == Retry getCommentTags(), can fix occational network lag")
        time.sleep(2)
    
    #提取好评率，中评率，差评率
    commentSummary = [0, 0, 0, 0, 0, 0]
    try:
        commentSummary = [summary['goodRate'], summary['generalRate'], summary['poorRate'], normalizeCountStr(summary['goodCountStr']), normalizeCountStr(summary['generalCountStr']), normalizeCountStr(summary['poorCountStr'])]
    except:
        pass
    #print(commentSummary)

    return commentSummary

def getCommentTags(sku):
    head = {'User-Agent': USERAGENT,  
            'Cookie': COOKIE, 
            'Referer': 'https://item.jd.com'}  
    head_ex = {'User-Agent': USERAGENT,  
            'Cookie': COOKIE_EX, 
            'Referer': 'https://item.jd.com'}          
            
    url = 'https://sclub.jd.com/comment/skuProductPageComments.action?&productId=' + str(sku) + '&score=0&sortType=5&page=0&pageSize=10&isShadowSku=0&fold=1'
    #print(url)
    #html = requests.get(url)
    #print(html.status_code)
    
    #提取最多多少条标签，电脑页面大部分tag数量是11个及以内
    numTags = NUMTAGS
    
    #获得原始评论页面的数据，提取总结部分与标签部分的数据
    tags = []
    retry = RETRY
    while retry > 0:
        #一般场景，国内商品
        try:        
            request = urllib.request.Request(url, headers=head)
            response = urllib.request.urlopen(request)
            content = response.read().decode('gbk')
            #print(content)

            result = json.loads(content)
            summary = result['productCommentSummary']
            tags = result['hotCommentTagStatistics']
            if summary != "" and summary != None:
                break
        except Exception as ex:
            pass  
        #特殊场景，海外购，url和cookie都不一样    
        try:    
            request = urllib.request.Request(url, headers=head_ex)
            response = urllib.request.urlopen(request)
            content = response.read().decode('gbk')
            #print(content)

            result = json.loads(content)
            summary = result['productCommentSummary']
            tags = result['hotCommentTagStatistics']
            if summary != "" and summary != None:
                break           
        except Exception as ex:
            pass            
        retry -= 1
        ##print("    == Retry getCommentTags(), can fix occational network lag")
        time.sleep(2)
       
    commentTags = []
    for i in range(numTags):
        if len(tags) > i:
            commentTags.append(tags[i]['name'])
        else:
            commentTags.append("")
    #print(commentTags)    
    return commentTags

def getCommentDetails(sku):
    head = {'User-Agent': USERAGENT,  
            'Cookie': COOKIE, 
            'Referer': 'https://item.jd.com'}  
    head_ex = {'User-Agent': USERAGENT,  
            'Cookie': COOKIE_EX, 
            'Referer': 'https://item.jd.com'}    
    
    commentPool = {'good':[], 'middle':[], 'bad':[]}
    score = {'good':3, 'middle':2, 'bad':1} #0 all, 1 bad, 2 middle, 3 good
    pagenum = {'good':100, 'middle':10, 'bad':10}
    
    for level in ['good', 'middle', 'bad']:
        for page in range(pagenum[level]):
            #url = 'https://sclub.jd.com/comment/productPageComments.action?&productId=' + str(sku) + '&score=0&sortType=5&page='+ str(page) +'&pageSize=10&isShadowSku=0&fold=1'
            url = 'https://sclub.jd.com/comment/skuProductPageComments.action?&productId=' + str(sku) + '&score=' + str(score[level]) + '&sortType=5&page='+ str(page) +'&pageSize=10&isShadowSku=0&fold=1'
            #print(url)
            html = requests.get(url)
            #print(html.status_code)
        
            #获得原始评论页面的数据，提取总结部分与标签部分的数据
            retry = RETRY
            while retry > 0:
                #一般场景，国内商品
                try:            
                    request = urllib.request.Request(url, headers=head)
                    response = urllib.request.urlopen(request)
                    content = response.read().decode('gbk')
                    #print(content)

                    result = json.loads(content)
                    #print(result['comments'])
                    commentContent = None
                    for comment in result['comments']:
                        commentContent = comment['content']
                        commentPool[level].append(commentContent)
                    if commentContent != None:
                        break
                except Exception as ex:
                    pass       
                #特殊场景，海外购，url和cookie都不一样   
                try:            
                    request = urllib.request.Request(url, headers=head_ex)
                    response = urllib.request.urlopen(request)
                    content = response.read().decode('gbk')
                    #print(content)

                    result = json.loads(content)
                    #print(result['comments'])
                    commentContent = None
                    for comment in result['comments']:
                        commentContent = comment['content']
                        commentPool[level].append(commentContent)
                    if commentContent != None:
                        break
                except Exception as ex:
                    pass                           
                retry -= 1
                #print("== RETRYING ==")
                time.sleep(1) 
            
            if retry == 0:  #没有更多评论了
                break
                
        #print(commentPool[level])
    return commentPool    
    
# ======== GENERATE WORDCLOUD ========
#根据字体属性更改颜色
def colorFunc(word=None, font_size=None, position=None, orientation=None, font_path=None, random_state=None):

    #字体大小 
    if font_size < 40:
        r=random_state.randint(224,255)
        g=random_state.randint(224,255)
        b=random_state.randint(224,255)
    else:
        r=random_state.randint(32,160)
        g=random_state.randint(32,160)
        b=random_state.randint(32,160)
 
    #返回一个rgb颜色元组
    return (r,g,b)


#生成词云
def saveComment(sku, level, commentPool, path, text):
    MAXWORD = 50
    commentList = commentPool[level]
    if path is None or path == "":
        skuname, _, _, _, _, _, _ = getInfo(sku)
        path = (str(sku) + '_' + validateTitle(skuname.replace(" ", "")))[:30]
    if (len(commentList) > 0):
        mkdir(validateTitle(path))
        #保存所有评论文本
        if text == 1:
            stringbreak = '\r\n'+'-'*20+'\r\n'
            with open(path+os.sep+path+'_'+level+'.txt', 'w') as f:
                for comment in commentList:
                    f.write(comment)
                    f.write(stringbreak)
                f.close()
        #生成词云 - jieba分词
        commentAllText = " ".join(commentList)
        commentAllWord = jieba.cut(commentAllText, cut_all = True)
        commentAllWordSplit = " ".join(commentAllWord)
        # - 导入过滤字
        stopwords = set()
        content = [line.strip() for line in open('comment/stopwords.txt','r',encoding='utf-8').readlines()]
        stopwords.update(content)
        # - 生成词云 mask = imageio.imread('comment'+os.sep+level+'.jpg'), 
        contentWordCloud = WordCloud(background_color = 'white', color_func = colorFunc, width = 640, height = 480, max_font_size= 60, min_font_size = 20, font_step = 10, font_path = 'comment/fonts/sthupo.ttf', max_words = MAXWORD, stopwords= stopwords).generate(commentAllWordSplit)
        # - 生成图片并保存
        timeStamp = time.strftime("%Y_%m_%d_%H_%M", time.localtime())
        fImage = path+os.sep+path+'_'+level+"_"+timeStamp+'.png'
        plt.imshow(contentWordCloud)
        plt.axis("off")
        plt.savefig(fImage)
        #plt.show()
        # - 生成词频
        c = Counter()
        for x in commentAllWordSplit.split(' '):
            if len(x) > 1 and x not in stopwords:
                c[x] += 1
        countFreqWord = 0
        MAX_FREQ_WORD = 5
        for (k,v)in c.most_common(MAXWORD): 
            addStringToImg(fImage, k+': '+str(v), 0, 100+countFreqWord*30, 20)
            countFreqWord+=1
            if countFreqWord == MAX_FREQ_WORD: 
                break
        if text == 1:        
            with open(path+os.sep+path+'_'+level+'.csv', 'w', encoding='utf-8-sig') as f:
                for (k,v)in c.most_common(MAXWORD):
                    f.write(k+','+str(v)+'\n')
                f.close()
                
    return path

#在图片上加字符串
def addStringToImg(image, string, x, y, fontsize=25):
    tempImg = '_temp.png'
    os.rename(image, tempImg)
    bk_img = cv2.imread(tempImg)
    #设置需要显示的字体
    fontpath = 'comment/fonts/simyou.ttf'
    font = ImageFont.truetype(fontpath, fontsize)
    img_pil = Image.fromarray(bk_img)
    draw = ImageDraw.Draw(img_pil)
    #绘制文字信息
    draw.text((x, y),  string, font = font, fill = (0, 0, 0))
    bk_img = numpy.array(img_pil)

    #cv2.imshow("add_text",bk_img)
    #cv2.waitKey()
    cv2.imwrite(tempImg,bk_img)
    os.rename(tempImg, image)

#给图片加标注        
def addFootprint(path, title, sku0, skuNum, commentNumLevel, commentNumAll): 
    # - 给图片加标记
    timeStamp = time.strftime("%Y_%m_%d_%H_%M", time.localtime())
    fImage = path+os.sep+path+'_'+level+"_"+timeStamp+'.png'
    
    if os.path.exists(fImage):
        addStringToImg(fImage, title + ' rate: ' + '%.0f%%'%(100*commentNumLevel/commentNumAll) + ' (' + str(commentNumLevel) + '/' + str(commentNumAll) + ')', 0, 0)
        if int(skuNum) > 1:
            addStringToImg(fImage, str(sku0.strip(SPECIAL_ID_HEAD)) + ' and ' + str(int(skuNum)-1) + ' other sample(s)', 0, 30)
        else:
            addStringToImg(fImage, str(sku0.strip(SPECIAL_ID_HEAD)), 0, 30)
        addStringToImg(fImage, timeStamp, 420, 455)
        print("Generated wordcloud for: "+path+"\n")

#根据index获取指定范围sku的list，返回类似于[[1, "Lenovo Y9000P", [1000, 1001, 1002, 1003]],[],[]]
def getCommentCategoryList(index):
    cateList = [] #二级list，存放需要抓取的类别的list

    try:
        if os.path.exists(FILE_CONFIG_COMMENT):
            rowList = parseCsv(FILE_CONFIG_COMMENT)
            
            if index.lower() == 'all': #抓取配置文件里所有行的评论
                for row in rowList:
                    if len(row) > 2:
                        skuIndex = row[0].lower()
                        skuCate = row[1]
                        skuList = row[2:]
                        skuList = [x for x in skuList if x != '']
                        cateList.append([skuIndex, skuCate, skuList])   
            else: #只根据index抓取指定的行
                skuIndex = index.lower()
                for row in rowList:
                    if row[0].lower() == skuIndex:
                        skuCate = row[1]
                        skuList = row[2:]
                        skuList = [x for x in skuList if x != '']
                        cateList.append([skuIndex, skuCate, skuList]) 
                        break
    except Exception as ex:
        print("Please ensure the config file is closed")
        pass             
    return cateList
    
# ======== CAPTURE OTHER INFO ========
def getInfo(sku):
    head = {'User-Agent': USERAGENT, 
            'Cookie': COOKIE}  
    head_ex = {'User-Agent': USERAGENT, 
            'Cookie': COOKIE_EX}              
    url = 'https://item.jd.com/'+str(sku)+'.html'
    url_ex = 'https://npcitem.jd.hk/'+str(sku)+'.html'

    listskuname = []
    listshop = []
    listgoodshop = []
    listbrand = []
    listinfo = []
    listtableindex = []
    listtabledata = []
    retry = RETRY
    while retry > 0:
        #一般场景，国内商品
        try:
            response = requests.get(url, headers=head, timeout=(TIMEOUT, TIMEOUT)) #timeout=(a, b) a 请求超时 b 读取超时
            response.encoding = 'utf-8'
            htmltree = etree.HTML(response.text)

            listskuname = htmltree.xpath('//div[@class="sku-name"]/text()')
            listshop = htmltree.xpath('//div[@class="J-hove-wrap EDropdown fr"]/div/div/a/text()')
            listgoodshop = htmltree.xpath('//div[@class="name goodshop EDropdown"]/em/text()')
            listbrand = htmltree.xpath('//ul[@id="parameter-brand"]/li/@title')
            listinfo = htmltree.xpath('//ul[@class="parameter2 p-parameter-list"]/li/text()')
            listtableindex = htmltree.xpath('//div[@class="Ptable"]/div/dl/dl/dt/text()')
            listtabledata = htmltree.xpath('//div[@class="Ptable"]/div/dl/dl/dd[not(contains(@class,"Ptable-tips"))]/text()')
        except Exception as ex:
            #print(ex)
            pass
        
        #if listskuname != [] and shop != [] and brand != [] and listinfo != []:
        if listskuname != [] and listinfo != []:
            break
            
        #特殊场景，海外购，url和cookie都不一样
        try:
            response = requests.get(url_ex, headers=head_ex, timeout=(TIMEOUT, TIMEOUT)) #timeout=(a, b) a 请求超时 b 读取超时
            response.encoding = 'utf-8'
            htmltree = etree.HTML(response.text)

            listskuname = htmltree.xpath('//div[@class="sku-name"]/text()')
            listshop = htmltree.xpath('//div[@class="J-hove-wrap EDropdown fr"]/div/div/a/text()')
            listgoodshop = htmltree.xpath('//div[@class="name goodshop EDropdown"]/em/text()')
            listbrand = htmltree.xpath('//ul[@id="parameter-brand"]/li/@title')
            listinfo = htmltree.xpath('//ul[@class="parameter2 p-parameter-list"]/li/text()')
            listtableindex = htmltree.xpath('//div[@class="Ptable"]/div/dl/dl/dt/text()')
            listtabledata = htmltree.xpath('//div[@class="Ptable"]/div/dl/dl/dd[not(contains(@class,"Ptable-tips"))]/text()')
        except Exception as ex:
            #print(ex)
            pass
        
        #if listskuname != [] and shop != [] and brand != [] and listinfo != []:
        if listskuname != [] and listinfo != []:
            break                   
            
        retry -= 1
        ##print("    == Retry getInfo(), can fix occational network lag")
        time.sleep(1)
    
    #处理名字
    skuname = getSkuname(listskuname)
    #处理店铺信息
    if listshop != [] and listshop != None:
        shop = listshop[0]
    else:
        shop = ''
    if listgoodshop !=[] and listgoodshop != None and "自营" in listgoodshop[0]:
        goodshop = 'Yes'
    else: 
        goodshop = 'No'
    #处理品牌信息    
    if listbrand != [] and listbrand != None:
        brand = listbrand[0]
    else:
        brand = ''
    
    #print(skuname)
    #print(shop)
    #print(goodshop)
    #print(brand)
    #print(listinfo)
    #print(listtableindex)
    #print(listtabledata)
    return skuname, shop, goodshop, brand, listinfo, listtableindex, listtabledata


# ======== Capture Data Main Flow ========
#从CSV表格检索当前关键字的配置，包括“商品介绍”“更多参数”（CSV需以逗号分隔元素）
def getConfig(keyword):
    listIndex = []
    listDetail = []
    listAdditional = []
    if os.path.exists(FILE_CONFIG_DETAIL): 
        rowsList = parseCsv(FILE_CONFIG_DETAIL)
        #print(rowsList)
        for row in rowsList:
            if row[0] == "商品介绍" and row[1] == keyword: 
                listIndex = row[2:]
                listIndex = [x for x in listIndex if x != '']
                #print(listIndex)
            if row[0] == "更多参数" and row[1] == keyword:
                listDetail = row[2:]
                listDetail = [x for x in listDetail if x!= '']
                #print(listDetail)
            if row[0] == "手动添加" and row[1] == keyword: 
                listAdditionalOrg = row[2:]
                listAdditional = [x[1:] for x in listAdditionalOrg if x != '' and x[0] == SPECIAL_ID_HEAD]
                #print(listAdditional)
    return listIndex, listDetail, listAdditional

#根据首页商品信息，生成当前搜索词对应的config字段
def generateConfig(keyword):
    TEMPFILE_CONFIG_DETAIL = "_configDetail.csv"
    BACKFILE_CONFIG_DETAIL = "_configDetail.backup.csv"
    
    print("Generating config file. It takes minute...")
    
    #删除旧的临时文件
    if os.path.exists(TEMPFILE_CONFIG_DETAIL):
        os.remove(TEMPFILE_CONFIG_DETAIL)
    
    #检查是否已经存在针对当前搜索词的config字段，有的话提取已有的设置
    listIndex, listDetail, listAdditional = getConfig(keyword)

    #创建新的临时config文件，剔除当前关键字，会在后续加上更新后的设置
    if os.path.exists(FILE_CONFIG_DETAIL): 
        rowsList = parseCsv(FILE_CONFIG_DETAIL)
        for row in rowsList:
            if len(row) >= 2 and row[0] != "" and row[1] != keyword:
                appendCsv(TEMPFILE_CONFIG_DETAIL, row)
                if row[0] == "手动添加": #每组后加一个分割行
                    appendCsv(TEMPFILE_CONFIG_DETAIL, [""])

    #抓取首页list
    listsku, _ = getList(keyword, None, 50)
    listinfoindexpool = []
    listtableindexpool = []
    
    #对首页list，获取每个sku的商品介绍目录和详细信息目录
    for sku in listsku:
        skuname, shop, goodshop, brand, listinfo, listtableindex, listtabledata = getInfo(sku)
        listinfoindex = [x.split("：")[0] for x in listinfo]
        listinfodata = [x.split("：")[1] for x in listinfo]
        listinfoindexpool.extend(listinfoindex)
        listtableindexpool.extend(listtableindex)
    
    #统计商品介绍目录和详细信息目录中出现较多的条目，排序后，加上之前设置中有而当前没有的项目
    rowInfo = ["商品介绍", keyword]
    counterInfo = Counter()
    for item in listinfoindexpool:
        counterInfo[item] += 1;
    for (keyInfo, valueInfo) in counterInfo.most_common():
        if valueInfo > 0: #int(len(listsku)/3):
            rowInfo.append(keyInfo)
    #print(list(set(listIndex) - set(rowInfo)))
    rowInfo.extend(list(set(listIndex) - set(rowInfo)))
    appendCsv(TEMPFILE_CONFIG_DETAIL, rowInfo)    
        
    rowTable = ["更多参数", keyword]
    counterTable = Counter()
    for item in listtableindexpool:
        counterTable[item] += 1;
    for (keyTable, valueTable) in counterTable.most_common(int(len(listsku)/2)):
        if valueTable > 0: #int(len(listsku)/3):
            rowTable.append(keyTable)
    #print(list(set(listDetail) - set(rowTable)))
    rowTable.extend(list(set(listDetail) - set(rowTable)))
    appendCsv(TEMPFILE_CONFIG_DETAIL, rowTable)
    
    rowOther = ["手动添加", keyword]
    rowOther.extend(listAdditional)
    appendCsv(TEMPFILE_CONFIG_DETAIL, rowOther)
    
    appendCsv(TEMPFILE_CONFIG_DETAIL, [""])
    
    #原子操作，备份之前的config文件，重命名当前临时文件为正式文件
    if os.path.exists(TEMPFILE_CONFIG_DETAIL): 
        if os.path.exists(BACKFILE_CONFIG_DETAIL):
            os.remove(BACKFILE_CONFIG_DETAIL)
        if os.path.exists(FILE_CONFIG_DETAIL):
            os.rename(FILE_CONFIG_DETAIL, BACKFILE_CONFIG_DETAIL)
        os.rename(TEMPFILE_CONFIG_DETAIL, FILE_CONFIG_DETAIL)

def loadTable(fData, keyword): 
    #读取config文件
    listIndex, listDetail, listAdditional = getConfig(keyword)
    
    #根据当前已有数据，生成二维数组
    listSkuDetail = []
    
    if os.path.exists(fData):
        rowList = parseCsv(fData)
        rowConfig = rowList[0]  #第一行，老的配置
        listSpecialSplit = [i for i,j in enumerate(rowConfig) if j == SPECIAL_SPLIT]    #找出三个分隔符的索引值，注意分隔符自身占了一个位置
        
        if len(listSpecialSplit) == 3: #如果有三个分隔符，说明格式匹配，提取数据，否则数据格式太老，不前向兼容
            for row in rowList[1:]: #后面数据行
                skuDetail = []
                #第一组普通信息
                rowConfigPart = rowConfig[: listSpecialSplit[0]]    
                for index in ["年", "月", "日", "星期", "时间", "ID", "LINK", "京东页数", "销量排名", "商品全名", "虚价", "原价", "价格", "店铺", "京东自营", "品牌"]:
                    if index in rowConfigPart:    
                        skuDetail.append(row[rowConfigPart.index(index)])
                    else:
                        skuDetail.append("")
                skuDetail.append(SPECIAL_SPLIT)
                #第二组商品介绍
                rowConfigPart = rowConfig[listSpecialSplit[0]+1 : listSpecialSplit[1]]        
                for index in listIndex:
                    if index in rowConfigPart:    
                        skuDetail.append(row[rowConfigPart.index(index) + listSpecialSplit[0]+1])
                    else:
                        skuDetail.append("") 
                skuDetail.append(SPECIAL_SPLIT)
                #第三组详细信息
                rowConfigPart = rowConfig[listSpecialSplit[1]+1 : listSpecialSplit[2]]
                for index in listDetail:
                    if index in rowConfigPart:    
                        skuDetail.append(row[rowConfigPart.index(index) + listSpecialSplit[1]+1])
                    else:
                        skuDetail.append("")                        
                skuDetail.append(SPECIAL_SPLIT)
                #第四组评价信息
                rowConfigPart = rowConfig[listSpecialSplit[2]+1 :]
                #for index in ["好评率", "中评率", "差评率", "好评数", "中评数", "差评数", "TAG00", "TAG01", "TAG02", "TAG03", "TAG04", "TAG05", "TAG06", "TAG07", "TAG08", "TAG09", "TAG10", "TAG11"]:
                for index in ["好评率", "中评率", "差评率", "好评数", "中评数", "差评数"]:
                    if index in rowConfigPart:    
                        skuDetail.append(row[rowConfigPart.index(index) + listSpecialSplit[2]+1])
                    else:
                        skuDetail.append("")    
                #汇总，将当前这条旧数据按照新的配置格式整理后，写入数组
                #print(skuDetail)
                listSkuDetail.append(skuDetail)
    return listSkuDetail

#根据需求生成表格
def generateTable(fData, keyword, url, count):
    TEMPFILE_DATA = "_data_" + str(keyword) + ".csv"
    BACKFILE_DATA = "_data_" + str(keyword) + ".backup.csv"

    #读取config文件
    listIndex, listDetail, listAdditional = getConfig(keyword)
    
    #删除旧的临时文件
    if os.path.exists(TEMPFILE_DATA):
        os.remove(TEMPFILE_DATA)

    #生成临时数据文件的表头
    row = ["年", "月", "日", "星期", "时间", "ID", "LINK", "京东页数", "销量排名", "商品全名", "虚价", "原价", "价格", "店铺", "京东自营", "品牌", SPECIAL_SPLIT]
    for index in listIndex:
        row.append(index)
    row.append(SPECIAL_SPLIT)   
    for index in listDetail:
        row.append(index) 
    row.append(SPECIAL_SPLIT)
    row.extend(["好评率", "中评率", "差评率", "好评数", "中评数", "差评数"])
    #for i in range(NUMTAGS):
    #    row.append("TAG" + str(i).zfill(2))                
    appendCsv(TEMPFILE_DATA, row)  #写入
    rowHead = row

    #将老数据写入临时文件
    listSkuDetail = loadTable(fData, keyword)
    listSkuOld = []
    for skuDetail in listSkuDetail: 
        row = skuDetail
        appendCsv(TEMPFILE_DATA, row)
        listSkuOld.append(row[rowHead.index("ID")].strip(SPECIAL_ID_HEAD))  #对每一条记录，查找ID号，去掉'_'后写入旧记录
        
    #原子操作，备份之前的数据文件，重命名当前的临时文件为正式数据文件
    if os.path.exists(TEMPFILE_DATA):
        if os.path.exists(BACKFILE_DATA):
            os.remove(BACKFILE_DATA)
        if os.path.exists(fData):
            os.rename(fData, BACKFILE_DATA)
        os.rename(TEMPFILE_DATA, fData)            
    
    #如果没有达到需要的数量，继续抓数据
    if len(listSkuOld) < count or len(listAdditional) > 0:
        #抓取所有sku的货号
        listsku, skupagelist = getList(keyword, url, count)
        listskuOriginal = listsku
        print("Available records: ", len(listsku))
        #print(listsku)
        #加入手动添加的sku货号
        listsku += listAdditional
        listskuAdd = sorted(set(listsku), key = listsku.index)
        print("Available records + additional: ", len(listskuAdd))
        #实际要抓取的sku货号
        listskuThis = sorted(list(set(listskuAdd) - set(listSkuOld)), key = listskuAdd.index)
        print("Excuting records: ", len(listskuThis))
        print()
        #准备记录抓取失败的sku
        listskuDrop = []

        #对每个sku，抓取价格和信息
        for cSku, sku in enumerate(listskuThis):
            progress = cSku/len(listskuThis)
            print("\rProgress: %.1f%%  " % float(100*progress) + "[" + "="*int(20*progress) + "-"*(20-int(20*progress)) + "]  " + "Working on Sku " + str(sku) + " "*10, end='')
            price_m, price_op, price_p = getPrice(sku)
            rankPage = getRankPage(sku, skupagelist)
            rankSku = getRankSku(sku, listskuOriginal)
            skuname, shop, goodshop, brand, listinfo, listtableindex, listtabledata = getInfo(sku)
            summary = getCommentRate(sku)
            #tags = getCommentTags(sku)
            
            if price_p == None or price_p == "" or skuname == None or skuname == "" or listinfo == None or len(listinfo) == 0 or summary[0] == 0:
                errorCode = 0
                if price_p == None or price_p == "":
                    errorCode |= 1 
                if skuname == None or skuname == "":
                    errorCode |= 2 
                if listinfo == None or len(listinfo) == 0:
                    errorCode |= 4 
                if summary[0] == 0:
                    errorCode |= 8 
                print("\r    == Miss info(ECode: " + str(errorCode) + "), drop sku " + str(sku) + " "*30)
                listskuDrop.append(sku)
                continue    #信息不全，跳过这一条不写入
            
            #信息准备好后开始一次性写入一行
            row = [time.strftime("%Y", time.localtime()), time.strftime("%m", time.localtime()), time.strftime("%d", time.localtime()), time.strftime("%A", time.localtime()), time.strftime("%H:%M", time.localtime()), SPECIAL_ID_HEAD+str(sku), 'https://item.jd.com/'+str(sku)+'.html']
            row.extend([rankPage, rankSku, skuname, price_m, price_op, price_p, shop, goodshop, brand, SPECIAL_SPLIT])
            listinfoindex = [x.split("：")[0] for x in listinfo if '：' in x]
            listinfodata = [x.split("：")[1] for x in listinfo if '：' in x]
            for index in listIndex:
                if index in listinfoindex:
                    row.append(listinfodata[listinfoindex.index(index)])
                else:
                    row.append("")
            row.append(SPECIAL_SPLIT)          
            for index in listDetail:
                if index in listtableindex:
                    row.append(listtabledata[listtableindex.index(index)])
                else:
                    row.append("")   
            row.append(SPECIAL_SPLIT)                    
            for item in summary:
                row.append(item)
            #for item in tags:
            #    row.append(item)
            appendCsv(fData, row) #写入
        
            time.sleep(1)   #慢一点……
        progress = 1
        print("\rProgress: %.1f%%  " % float(100*progress) + "[" + "="*int(20*progress) + "-"*(20-int(20*progress)) + "]  " + " "*40, end='')
        
        
        listskuDropInAdd = [x for x in listskuDrop if x in listAdditional]
        print("")
        print("-" * 20)
        print("Target records: ", len(listskuThis))
        print("Actual records: ", len(listskuThis) - len(listskuDrop))
        print("Droped records: ", len(listskuDrop))
        print("-" * 20)
        print("Target records from additional list: ", len(listAdditional))
        print("Actual records from additional list: ", len(listAdditional) - len(listskuDropInAdd))
        print("Droped records from additional list: ", len(listskuDropInAdd))
        print("-" * 20)
        for sku in listskuDropInAdd: 
            print(str(sku))
        print("-" * 20)

def extractTable(fInput, fOutput, extractList): 
    #读取input文件，提取首行内容，然后逐行处理
    if os.path.exists(fInput):
        #删除旧的output文件（离线功能，不需要备份）
        if os.path.exists(fOutput):
            os.remove(fOutput)
        #读取input文件内容
        rowListInput = parseCsv(fInput)
        rowConfigInput = rowListInput[0]  #第一行，老的配置
        rowConfigOutput = rowConfigInput
        rowConfigOutput.append(SPECIAL_SPLIT) #加上分隔符
        rowConfigOutput.extend(extractList) #加上本次需要清洗的内容作为表头
        #print(rowConfigOutput)
        appendCsv(fOutput, rowConfigOutput)
        #开始处理每一行数据
        for rowInput in rowListInput[1:]:
            rowOutput = rowInput
            rowOutput.append(SPECIAL_SPLIT) #加上分隔符
            for extract in extractList: 
                dataExtracted = None
                # ++++ 添加新的清洗参数以及对应函数，在这里“注册” ++++ --------------------------------------------
                if extract == "Weight": 
                    dataExtracted = _exWeight(rowConfigInput, rowInput)
                if extract == "Length": 
                    dataExtracted = _exLength(rowConfigInput, rowInput)
                if extract == "Width": 
                    dataExtracted = _exWidth(rowConfigInput, rowInput)    
                if extract == "Height": 
                    dataExtracted = _exHeight(rowConfigInput, rowInput)    
                if extract == "PanelSize": 
                    dataExtracted = _exPanelSize(rowConfigInput, rowInput)
                if extract == "ResX": 
                    dataExtracted = _exResX(rowConfigInput, rowInput)
                if extract == "ResY": 
                    dataExtracted = _exResY(rowConfigInput, rowInput) 
                if extract == "PPI": 
                    dataExtracted = _exPPI(rowConfigInput, rowInput)    
                # ---- 添加新的清洗参数以及对应函数，在这里“注册” ---- --------------------------------------------
                if dataExtracted == None: 
                    rowOutput.append("")
                else:
                    rowOutput.append(str(dataExtracted))
            #print(rowOutput)
            appendCsv(fOutput, rowOutput)
            

# ======== Extract Sub-functions ========
#从已有表格清洗数据生成新的表格，每一个清洗项单独定义子函数，根据需要来调用并将结果写入生成表格
def _exWeight(rowConfigInput, rowInput):
    dataOrigin = rowInput[rowConfigInput.index("产品净重（kg）")]
    dataSearch = re.search("\d+\.?\d*", dataOrigin) #抽取整数或小数
    dataExtracted = dataSearch.group() if dataSearch != None else None
    return dataExtracted

def _exLength(rowConfigInput, rowInput):
    dataOrigin = rowInput[rowConfigInput.index("产品尺寸")]
    dataFilter = re.search("长(.*?)mm", dataOrigin) #匹配关键字段
    dataSearch = re.search("\d+\.?\d*", dataFilter.group()) if dataFilter != None else None #抽取整数或小数
    dataExtracted = dataSearch.group() if dataSearch != None else None
    return dataExtracted

def _exWidth(rowConfigInput, rowInput):
    dataOrigin = rowInput[rowConfigInput.index("产品尺寸")]
    dataFilter = re.search("宽(.*?)mm", dataOrigin) #匹配关键字段
    dataSearch = re.search("\d+\.?\d*", dataFilter.group()) if dataFilter != None else None #抽取整数或小数
    dataExtracted = dataSearch.group() if dataSearch != None else None
    return dataExtracted

def _exHeight(rowConfigInput, rowInput):
    dataOrigin = rowInput[rowConfigInput.index("产品尺寸")]
    dataFilter = re.search("高(.*?)mm", dataOrigin) #匹配关键字段
    dataSearch = re.search("\d+\.?\d*", dataFilter.group()) if dataFilter != None else None #抽取整数或小数
    dataExtracted = dataSearch.group() if dataSearch != None else None
    return dataExtracted

def _exPanelSize(rowConfigInput, rowInput):
    dataOrigin = rowInput[rowConfigInput.index("屏幕尺寸")]
    dataSearch = re.search("\d+\.?\d*", dataOrigin)
    dataExtracted = dataSearch.group() if dataSearch != None else None #抽取整数或小数
    return dataExtracted

def _exResX(rowConfigInput, rowInput):
    dataOrigin = rowInput[rowConfigInput.index("屏幕分辨率")]
    dataFilter = dataOrigin.split('*') #匹配关键字段
    dataSearch = re.search("\d+\.?\d*", dataFilter[0]) if len(dataFilter) > 1 else None #抽取整数或小数
    dataExtracted = dataSearch.group() if dataSearch != None else None
    return dataExtracted
    
def _exResY(rowConfigInput, rowInput):
    dataOrigin = rowInput[rowConfigInput.index("屏幕分辨率")]
    dataFilter = dataOrigin.split('*') #匹配关键字段
    dataSearch = re.search("\d+\.?\d*", dataFilter[-1]) if len(dataFilter) > 1 else None #抽取整数或小数
    dataExtracted = dataSearch.group() if dataSearch != None else None
    return dataExtracted  

def _exPPI(rowConfigInput, rowInput):
    dataPanelSize = _exPanelSize(rowConfigInput, rowInput)      
    dataPanelSize = float(dataPanelSize) if dataPanelSize != None else None #提取屏幕尺寸
    dataResX = _exResX(rowConfigInput, rowInput)                
    dataResX = float(dataResX) if dataResX != None else None #提取分辨率X
    dataResY = _exResY(rowConfigInput, rowInput)                
    dataResY = float(dataResY) if dataResY != None else None #提取分辨率Y
    if dataPanelSize != None and dataPanelSize != 0 and dataResX != None and dataResY != None:
        dataExtracted = int(pow((pow(dataResX, 2) + pow(dataResY, 2)), 0.5) / dataPanelSize) #计算PPI = sqrt(ResX^ + ResY^) / PanelSize
    else: 
        dataExtracted = None
    return dataExtracted

# ======== MAIN ========
#定义参数列表
def getArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("--search", type=int, default=0)
    parser.add_argument("--filter", type=int, default=-1)
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--setup", type=int, default=0)
    parser.add_argument("--extract", type=int, default=0)
    parser.add_argument("--profile", type=int, default=0)
    parser.add_argument("--inputfile", type=str, default="")
    parser.add_argument("--outputfile", type=str, default="")
    parser.add_argument("--comment", type=int, default=0)
    parser.add_argument("--text", type=int, default=0)
    parser.add_argument("--sku", type=int, default=0)
    parser.add_argument("--index", type=str, default="")
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    #获取参数，search取得待搜索的字符串例如“游戏本”“显卡”，COUNT希望抓取的sku数量
    args = getArgs()
    SEARCH = args.search
    FILTER = args.filter
    COUNT = args.count
    SETUP = args.setup
    EXTRACT = args.extract
    PROFILE = args.profile
    INPUTFILE = args.inputfile
    OUTPUTFILE = args.outputfile
    COMMENT = args.comment
    TEXT = args.text
    SKU = args.sku
    INDEX = args.index
    
    print(HELP)
    
    if COMMENT == 1:
        if INDEX != "":
            cateList = getCommentCategoryList(INDEX)
            for cate in cateList:
                print("Get comments for index: " + cate[0] + " - " + cate[1])
                skuList = cate[2]
                commentPool = {'good':[], 'middle':[], 'bad':[]}
                for sku in skuList:
                    sku = sku.strip(SPECIAL_ID_HEAD)
                    print("Get comments for sku: " + str(sku))
                    commentCurrent = getCommentDetails(sku)
                    for level in ['good', 'middle', 'bad']:
                    #for level in ['good', 'bad']:
                        commentPool[level].extend(commentCurrent[level])
                #for level in ['good', 'middle', 'bad']:
                for level in ['good', 'bad']:
                    path = saveComment(sku, level, commentPool, cate[1], TEXT)  
                    addFootprint(path, path+'  '+level, str(skuList[0]), len(skuList), len(commentPool[level]), len(commentPool['good'])+len(commentPool['middle'])+len(commentPool['bad']))
        elif SKU != 0:
            print("Get comments for sku: " + str(SKU))
            commentPool = getCommentDetails(SKU)
            #for level in ['good', 'middle', 'bad']:
            for level in ['good', 'bad']:
                path = saveComment(SKU, level, commentPool, "", TEXT) 
                addFootprint(path, path+'  '+level, str(SKU), len(str(SKU)), len(commentPool[level]), len(commentPool['good'])+len(commentPool['middle'])+len(commentPool['bad']))               
        else:
            print("Please input a valid index or sku for comment capture!")
    elif EXTRACT == 1:
        if os.path.exists(INPUTFILE):
            print("Extract data from input file: ", INPUTFILE)
            profileExtractList = parseCsv(FILE_CONFIG_EXTRACT)
            if PROFILE < len(profileExtractList):
                extractList = profileExtractList[PROFILE]
                print("Extract data for: ", end='')
                for extract in extractList:
                    print(extract+', ', end='')
                print()
                extractTable(INPUTFILE, OUTPUTFILE, extractList)
                print("Extract data to output file: ", OUTPUTFILE)
            else: 
                print("Please input a valid profile!")
        else: 
            print("Please input a correct path for input file!")
    else:
        #转换序号为关键字
        #searchList = ["游戏本", "轻薄本", "设计本", "显卡", "EVO笔记本"]#定义关键字列表，注意该关键字会在config文件中对应相关配置
        rowsSearchList = parseCsv(FILE_CONFIG_MASTER)
        searchList = rowsSearchList[0]
        if FILTER != -1: 
            rowsFilterList = parseCsv(FILE_CONFIG_FILTER)

        #print(searchList)
        if SEARCH in range(len(searchList)):
            keywordSearch = searchList[SEARCH]
            print("Get data for segment: " + keywordSearch)
            
            urlFilter = None
            if FILTER != -1: 
                if FILTER in range(len(rowsFilterList)):
                    urlFilter = rowsFilterList[FILTER][0]
                    print("Get data with filter: " + urlFilter)
                else:
                    print("Please input a valid index for filter. ")
            
            if SETUP == 1:
                #对新的搜索关键字，生成config参数，后期也可以自行修改
                generateConfig(keywordSearch)
            else:
                #定义保存数据的表格文件名
                if urlFilter == None: 
                    fData = "DATA_"+str(keywordSearch)+"_"+time.strftime("%Y_%m", time.localtime())+".csv"
                else: 
                    fData = "DATA_"+str(keywordSearch)+"_"+str(FILTER)+"_"+time.strftime("%Y_%m", time.localtime())+".csv"
                
                #生成表格
                generateTable(fData, keywordSearch, urlFilter, COUNT)
        else:
            print("Please input a valid index for search!")

    print("")
    print("Finished. ")