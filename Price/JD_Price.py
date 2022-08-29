#-*- coding: utf-8 -*-

# ================================================================  #
#                                                                   #
#                    INTERNAL STUDY ONLY !                          #
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

#cookie需要timely更新，否则影响抓取comment等等功能（页面刷新，控制台-网络-请求标头-cookie）
COOKIE = "__jdu=1597106510361611076602; shshshfpa=e8c04075-2ed8-8c17-9a2e-5eb000215962-1597106511; pinId=lSwRbMKd-74tBDbKmwsL1w; shshshfpb=hYFEa8t4oszf5zty/aI7r1Q==; __jdv=76161171|direct|-|none|-|1661733370418; areaId=2; PCSYCityID=CN_310000_310100_0; shshshfp=594ba833ebdab9d6da8fd55a42246383; jsavif=0; __jda=122270672.1597106510361611076602.1597106510.1661733370.1661736699.64; __jdc=122270672; jsavif=0; ip_cityCode=2817; ipLoc-djd=2-2817-51973-0; wlfstk_smdl=uxj1ama95l44k3iy0vuzux861ko3ksre; TrackID=1wwh5dQPUO3-Jbsv7ZQp-mwhJOa6xjtAp-tnFZwG6FpF5hPQ-r3I9S4SXj2Ya_pHPmQx7PdSiEHoTQZZ5ZBbyqavSPq2KgqFGelWysuN0-PeE3W36-tVqiGuXke-tiibd; thor=C415B3C186C7F2E97A4AA78C1DB6835F123CCE19BAEDBD11C09CB538253C92B5800AB7FBD76057178E0BB5983DA0B64443D8A41C00B37F0CEEC32C59159E9418239FAA77892C866A27D21B442C00D79E51EDA0A9C646F1FB52ECFEAA2446880B43D5B2D714AB46B458FABB5C2E43EB120D0AC5C9B849FB847BC57310072DE35B25A5E005DACEA42980DE890E2DA670A1; pin=FioreZhang; unick=FioreZhang; ceshi3.com=201; _tp=IcTvqSKCNvN8JKtp2uhsOg==; _pst=FioreZhang; token=0d7dff58c81d855eab7f01712cca54d7,3,923187; __tk=sgPgdEvwrUrDJaAxstYxlonwJSYvqDbcsorRqEvwsUb1JcMEdrY1ebnprgnDqEbFdtPBIoBg,3,923187; __jdb=122270672.10.1597106510361611076602|64.1661736699; shshshsID=2258eb014a57d0c24fe40a8ae3255634_7_1661736877825; 3AB9D23F7A4B3C9B=IABYFHSAZ5YE4JK67BOOHWXZM3E3Q6LHRDFAOMFFBNIQYMWUZOXRA33UAIVOJD5FAGMHAXRKCCL2HARJ4LAJGRSQHE"

TIMEOUT = 2
RETRY = 5
NUMTAGS = 12

# ======== CAPTURE LIST OF SKU ========
#JD页面每一页默认刷新30个物品，下拉后再刷新30个。所以需要对于每一页分上下部分分别处理。
#抓取上半页的物品sku number
def getListPageUp(keyword, page):
    #对上半页，简单的构建header即可
    head = {'authority': 'search.jd.com',
            'method': 'GET',
            'scheme': 'https',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.131 Safari/537.36',
            }
    #对上半页，构造请求的页面
    url = 'https://search.jd.com/Search?keyword='+str(keyword)+'&enc=utf-8&page='+str(2*page-1)

    #获得页面HTML
    response = requests.get(url, headers=head)
    response.encoding = 'utf-8'
    htmltree = etree.HTML(response.text)
    
    #定位每一个sku的标签，在class=gl-item的li中
    skus = htmltree.xpath('//li[contains(@class,"gl-item")]')
    
    #获取所有sku的sku number
    skulist = [sku.xpath('@data-sku')[0] for sku in skus]
    if len(skulist) == 0:
        print("== Error getting new page(1st half), or No more item for this search", page)

    return skulist

#抓取上半页的物品sku number
def getListPageDown(keyword, page): 
    #对下半页，构建header时需要包入referer等元素
    head = {'authority': 'search.jd.com',
            'method': 'GET',
            'scheme':'https',
            'referer': 'https://search.jd.com/Search?keyword=PC&enc=utf-8',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.131 Safari/537.36',
            'x-requested-with': 'XMLHttpRequest',
    }
    #对下半页，构造请求的页面
    timestp = '%.5f'%time.time() #获取当前的Unix时间戳，并且保留小数点后5位
    url = 'https://search.jd.com/s_new.php?keyword='+str(keyword)+'&enc=utf-8&page='+str(2*page)+'&s='+str(48*page-20)+'&scrolling=y&log_id='+str(timestp)

    #获得页面HTML
    response = requests.get(url, headers=head)
    response.encoding = 'utf-8'
    htmltree = etree.HTML(response.text)
    
    #定位每一个sku的标签，在class=gl-item的li中
    skus = htmltree.xpath('//li[contains(@class,"gl-item")]')
    
    #获取所有sku的sku number
    skulist = [sku.xpath('@data-sku')[0] for sku in skus]
    if len(skulist) == 0:
        print("== Error getting new page(2nd half), or No more item for this search", page)
 
    return skulist

#根据指定的关键字以及sku数，返回所有满足条件的sku number（已经去重）
def getList(keyword, countnum):
    MAXPAGE = 20
    skulist = []
    for page in range(1, MAXPAGE):
        print("Getting sku list for Page "+str(page))
        #获得每页上半页，如果没有新的sku就跳出循环
        skulistUpdate = getListPageUp(keyword, page)
        if len(skulistUpdate) == 0:
            break
        skulist += skulistUpdate
        #获得每页下半页，如果没有新的sku就跳出循环
        skulistUpdate = getListPageDown(keyword, page)
        if len(skulistUpdate) == 0:
            break
        skulist += skulistUpdate
        #去重
        skulist = list(set(skulist)) 
        #如果超过希望抓取的sku数量就跳出循环
        if len(skulist) >= countnum:
            break
        time.sleep(3)   #慢一点……
    
    return [str(x) for x in skulist]

# ======== CAPTURE PRICE ========
def getPrice(sku):
    head = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.131 Safari/537.36', 
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
        print("== Retry getPrice(), can fix occational network lag")
        time.sleep(2)
    print(price)
    return price

def normalizeCountStr(countStr):
    countStr_1 = countStr.rstrip('+')
    countStr_2 = countStr_1.rstrip('万')
    if countStr_2 == countStr_1:
        count = int(countStr_2)
    else:
        count = int(10000 * float(countStr_2))
    return count

# ======== CAPTURE COMMENTS ========    
def getComment(sku):
    head = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.131 Safari/537.36', 
            'Cookie': COOKIE}  
    url = 'https://sclub.jd.com/comment/skuProductPageComments.action?&productId=' + str(sku) + '&score=0&sortType=5&page=0&pageSize=10&isShadowSku=0&fold=1'
    
    #html = requests.get(url)
    #print(html.status_code)
    
    #提取最多多少条标签，电脑页面大部分tag数量是11个及以内
    numTags = 12
    
    #获得原始评论页面的数据，提取总结部分与标签部分的数据
    tags = []
    retry = RETRY
    while retry > 0:
        try:
            request = urllib.request.Request(url, headers=head)
            response = urllib.request.urlopen(request, timeout=TIMEOUT)
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
        print("== Retry getComment(), can fix occational network lag")
        time.sleep(2)
    
    #提取好评率，中评率，差评率
    commentSummary = [0, 0, 0, 0, 0, 0]
    try:
        commentSummary = [summary['goodRate'], summary['generalRate'], summary['poorRate'], normalizeCountStr(summary['goodCountStr']), normalizeCountStr(summary['generalCountStr']), normalizeCountStr(summary['poorCountStr'])]
    except:
        pass
    print(commentSummary)
    
    commentTags = []
    for i in range(numTags):
        if len(tags) > i:
            commentTags.append(tags[i]['name'])
        else:
            commentTags.append("")
    print(commentTags)    
    return commentSummary, commentTags
    
# ======== CAPTURE OTHER INFO ========
def getInfo(sku):
    head = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.131 Safari/537.36', 
            'Cookie': COOKIE}  
    url = 'https://item.jd.com/'+str(sku)+'.html'

    listskuname = []
    listshop = []
    listbrand = []
    listinfo = []
    listtableindex = []
    listtabledata = []
    retry = RETRY
    while retry > 0:
        try:
            response = requests.get(url, headers=head, timeout=(TIMEOUT, TIMEOUT)) #timeout=(a, b) a 请求超时 b 读取超时
            response.encoding = 'utf-8'
            htmltree = etree.HTML(response.text)

            listskuname = htmltree.xpath('//div[@class="sku-name"]/text()')
            listshop = htmltree.xpath('//div[@class="J-hove-wrap EDropdown fr"]/div/div/a/text()')
            listbrand = htmltree.xpath('//ul[@id="parameter-brand"]/li/@title')
            listinfo = htmltree.xpath('//ul[@class="parameter2 p-parameter-list"]/li/text()')
            listtableindex = htmltree.xpath('//div[@class="Ptable"]/div/dl/dl/dt/text()')
            listtabledata = htmltree.xpath('//div[@class="Ptable"]/div/dl/dl/dd[not(contains(@class,"Ptable-tips"))]/text()')
        except Exception as ex:
            print(ex)
            pass
        
        #if listskuname != [] and shop != [] and brand != [] and listinfo != []:
        if listskuname != [] and listinfo != []:
            break
        retry -= 1
        print("== Retry getInfo(), can fix occational network lag")
        time.sleep(1)
    
    #处理名字
    skuname = getSkuname(listskuname)
    #处理店铺信息
    if listshop != [] and listshop != None:
        shop = listshop[0]
    else:
        shop = ''
    #处理品牌信息    
    if listbrand != [] and listbrand != None:
        brand = listbrand[0]
    else:
        brand = ''
    
    print(skuname)
    print(shop)
    print(brand)
    print(listinfo)
    print(listtableindex)
    print(listtabledata)
    return skuname, shop, brand, listinfo, listtableindex, listtabledata

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

#写入CSV文件
def appendCsv(file, row):
    with open(file, mode='a', newline='', encoding='utf-8-sig') as f:
        write=csv.writer(f)
        write.writerow(row)
        f.close

#读出CSV文件
def parseCsv(file):
    rows = []
    with open(file, mode='r') as f:
        read=csv.reader(f)
        rows = [row for row in read]
        f.close
    return rows

# ======== MISC ========
#定义参数列表
def getArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("--search", type=int, default=0)
    parser.add_argument("--count", type=int, default=100)
    args = parser.parse_args()
    return args

KeywordList = ["游戏本", "轻薄本", "设计本", "显卡", "EVO笔记本", "NVIDIA Studio创作本"]

# ======== MAIN ========
if __name__ == "__main__":
    #获取参数，search取得待搜索的字符串例如“游戏本”“显卡”，COUNT希望抓取的sku数量
    args = getArgs()
    SEARCH = args.search
    COUNT = args.count
    
    KEYWORD = KeywordList[SEARCH]
    
    #getInfo(100025263673)
    #while(True):
     #   pass
    
    #从CSV表格检索当前关键字的配置，包括“商品介绍”“更多参数”（CSV需以逗号分隔元素）
    listIndex = []
    listDetail = []
    rowsList = parseCsv("config.csv")
    #print(rowsList)
    for row in rowsList:
        if row[0] == "商品介绍" and row[1] == KEYWORD: 
            listIndex = row[2:]
            print(listIndex)
        if row[0] == "更多参数" and row[1] == KEYWORD:
            listDetail = row[2:]
            print(listDetail)
    
    '''
    #取得待抓取信息列表，要求同目录下有相关配置文件例如“游戏本.txt”“显卡.txt”
    listIndex = []
    with open(KEYWORD+".txt", 'r', encoding='utf-8') as f:
        listIndex = list(f)
        f.close()
        listIndex = [x.strip() for x in listIndex if x.strip != '']
    print(listIndex)
    
    #取得待抓取信息列表，要求同目录下有相关配置文件例如“游戏本.ini”“显卡.ini”
    listDetail = []
    with open(KEYWORD+".ini", 'r', encoding='utf-8') as f:
        listDetail = list(f)
        f.close()
        listDetail = [x.strip() for x in listDetail if x.strip != '']
    print(listDetail)    
    '''
    
    fData ="DATA_"+str(KEYWORD)+"_"+time.strftime("%Y_%m", time.localtime())+".csv"
    
    fDataExist = False
    listskuOld = []
    if os.path.exists(fData):
        fDataExist = True
        listskuOld = [str(x[0]) for x in pandas.read_csv(fData, usecols=['商品编号']).values]
        print("Found existing records: ", len(listskuOld))
        print(listskuOld)
    
    if len(listskuOld) < COUNT:
        #抓取所有sku的货号
        listsku = getList(KEYWORD, COUNT)
        print("Available records: ", len(listsku))
        #print(listsku)
        listskuThis = list(set(listsku) - set(listskuOld))
        print("Excuting records: ", len(listskuThis))
    
        #写第一行，如果是追加已经存在的同名文件则跳过
        if fDataExist == False:
            row = ["年", "月", "日", "星期", "时间"]
            row.extend(["商品全名", "价格", "店铺", "品牌"])
            for index in listIndex:
                row.append(index)
            for index in listDetail:
                row.append(index)    
            row.extend(["好评率", "中评率", "差评率", "好评数", "中评数", "差评数"])
            for i in range(NUMTAGS):
                row.append("标签")
            appendCsv(fData, row)  #写入
    

        #对每个sku，抓取价格和信息
        for sku in listskuThis:
            print("\r\n")
            print("Getting Price and Information for Sku "+str(sku))
            price = getPrice(sku)
           
            skuname, shop, brand, listinfo, listtableindex, listtabledata = getInfo(sku)
            summary, tags = getComment(sku)
            
            if price == None or price == "" or skuname == None or skuname == "" or listinfo == None or len(listinfo) == 0 or summary[0] == 0:
                time.sleep(3)
                continue    #信息不全，跳过这一条不写入
            
            #信息准备好后开始一次性写入一行
            row = [time.strftime("%Y", time.localtime()), time.strftime("%m", time.localtime()), time.strftime("%d", time.localtime()), time.strftime("%A", time.localtime()), time.strftime("%H:%M", time.localtime())]
            row.extend([skuname, price, shop, brand])
            listinfoindex = [x.split("：")[0] for x in listinfo]
            listinfodata = [x.split("：")[1] for x in listinfo]
            for index in listIndex:
                if index in listinfoindex:
                    row.append(listinfodata[listinfoindex.index(index)])
                else:
                    row.append("")
            for index in listDetail:
                if index in listtableindex:
                    row.append(listtabledata[listtableindex.index(index)])
                else:
                    row.append("")            
            for item in summary:
                row.append(item)
            for item in tags:
                row.append(item)
            appendCsv(fData, row) #写入
        
            time.sleep(2)   #慢一点……
