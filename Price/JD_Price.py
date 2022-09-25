#-*- coding: utf-8 -*-

# ================================================================  #
#                                                                   #
#                    INTERNAL STUDY ONLY !                          #
#                        VERSION 5.0                                #
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

# ======== COOKIE FOR WEB REQUEST ========
#cookie需要timely更新，否则影响抓取comment等等功能（页面刷新，控制台-网络-请求标头-cookie）
COOKIE = "__jdu=1597106510361611076602; shshshfpa=e8c04075-2ed8-8c17-9a2e-5eb000215962-1597106511; pinId=lSwRbMKd-74tBDbKmwsL1w; shshshfpb=hYFEa8t4oszf5zty/aI7r1Q==; __jdv=76161171|direct|-|none|-|1661733370418; areaId=2; PCSYCityID=CN_310000_310100_0; shshshfp=594ba833ebdab9d6da8fd55a42246383; jsavif=0; __jda=122270672.1597106510361611076602.1597106510.1661733370.1661736699.64; __jdc=122270672; jsavif=0; ip_cityCode=2817; ipLoc-djd=2-2817-51973-0; wlfstk_smdl=uxj1ama95l44k3iy0vuzux861ko3ksre; TrackID=1wwh5dQPUO3-Jbsv7ZQp-mwhJOa6xjtAp-tnFZwG6FpF5hPQ-r3I9S4SXj2Ya_pHPmQx7PdSiEHoTQZZ5ZBbyqavSPq2KgqFGelWysuN0-PeE3W36-tVqiGuXke-tiibd; thor=C415B3C186C7F2E97A4AA78C1DB6835F123CCE19BAEDBD11C09CB538253C92B5800AB7FBD76057178E0BB5983DA0B64443D8A41C00B37F0CEEC32C59159E9418239FAA77892C866A27D21B442C00D79E51EDA0A9C646F1FB52ECFEAA2446880B43D5B2D714AB46B458FABB5C2E43EB120D0AC5C9B849FB847BC57310072DE35B25A5E005DACEA42980DE890E2DA670A1; pin=FioreZhang; unick=FioreZhang; ceshi3.com=201; _tp=IcTvqSKCNvN8JKtp2uhsOg==; _pst=FioreZhang; token=0d7dff58c81d855eab7f01712cca54d7,3,923187; __tk=sgPgdEvwrUrDJaAxstYxlonwJSYvqDbcsorRqEvwsUb1JcMEdrY1ebnprgnDqEbFdtPBIoBg,3,923187; __jdb=122270672.10.1597106510361611076602|64.1661736699; shshshsID=2258eb014a57d0c24fe40a8ae3255634_7_1661736877825; 3AB9D23F7A4B3C9B=IABYFHSAZ5YE4JK67BOOHWXZM3E3Q6LHRDFAOMFFBNIQYMWUZOXRA33UAIVOJD5FAGMHAXRKCCL2HARJ4LAJGRSQHE"


# ======== MACROS ========
TIMEOUT = 5
RETRY = 5
NUMTAGS = 12
FILE_CONFIG_DETAIL = "configDetail.csv"
FILE_CONFIG_MASTER = "configMaster.csv"
SPECIAL_SPLIT = "█"
SPECIAL_ID_HEAD = "_"

#表头
# "年", "月", "日", "星期", "时间", "ID", "LINK", "商品全名", "价格", "店铺", "品牌", SPECIAL_SPLIT, =INDEX=, SPECIAL_SPLIT, =DETAIL=, SPECIAL_SPLIT, "好评率", "中评率", "差评率", "好评数", "中评数", "差评数"


# ======== CAPTURE LIST OF SKU ========
#JD页面每一页默认刷新30个物品，下拉后再刷新30个。所以需要对于每一页分上下部分分别处理。
#抓取上半页的物品sku number
def getListPageUp(keyword, page):
    #对上半页，简单的构建header即可
    head = {'authority': 'search.jd.com',
            'method': 'GET',
            'scheme': 'https',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:105.0) Gecko/20100101 Firefox/105.0',
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
#旧的接口，通过p.3.cn托管价格数据，2022年9月开始疑似废弃
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
    #print(price)
    return price
    
#新的接口，通过fts.jd.com查询价格信息
def getPrice_2(sku):
    head = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.131 Safari/537.36', 
            'Cookie': COOKIE, 
            'Referer': 'https://item.jd.com'}  
    url = 'https://fts.jd.com/prices/mgets?callback=jQuery&skuIds=J_'+str(sku)+'&source=pc-item'
    
    price = None
    retry = RETRY
    while retry > 0:
        try:
            request = urllib.request.Request(url, headers=head)
            response = urllib.request.urlopen(request, timeout=TIMEOUT)
            content = response.read().decode()
            pattern = re.compile('"p":"(.*?)"')
            price = re.search(pattern, content).group(1)
        except:
            pass
        else:
            break
        retry -= 1
        print("== Retry getPrice_2(), can fix occational network lag")
        time.sleep(2)
    #print(price)
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
            'Cookie': COOKIE, 
            'Referer': 'https://item.jd.com'}  
    url = 'https://club.jd.com/comment/skuProductPageComments.action?&productId=' + str(sku) + '&score=0&sortType=5&page=0&pageSize=10&isShadowSku=0&fold=1'
    
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
    #print(commentSummary)
    
    commentTags = []
    for i in range(numTags):
        if len(tags) > i:
            commentTags.append(tags[i]['name'])
        else:
            commentTags.append("")
    #print(commentTags)    
    return commentSummary, commentTags
    
def getComment_2(sku):
    head = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.131 Safari/537.36', 
            'Cookie': COOKIE, 
            'Referer': 'https://item.jd.com'}  
    url = 'https://club.jd.com/comment/productCommentSummaries.action?referenceIds=' + str(sku) + '&categoryIds='
    
    #html = requests.get(url)
    #print(html.status_code)
    
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
            summary = result['CommentsCount'][0]
            #print(summary)
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
        commentSummary = [summary['GoodRate'], summary['GeneralRate'], summary['PoorRate'], normalizeCountStr(summary['GoodCountStr']), normalizeCountStr(summary['GeneralCountStr']), normalizeCountStr(summary['PoorCountStr'])]
    except:
        pass
    #print(commentSummary)

    return commentSummary
    
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
    
    #print(skuname)
    #print(shop)
    #print(brand)
    #print(listinfo)
    #print(listtableindex)
    #print(listtabledata)
    return skuname, shop, brand, listinfo, listtableindex, listtabledata

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

# ======== Wrok Flow  ========
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
    listsku = getList(keyword, 50)
    listinfoindexpool = []
    listtableindexpool = []
    
    #对首页list，获取每个sku的商品介绍目录和详细信息目录
    for sku in listsku:
        skuname, shop, brand, listinfo, listtableindex, listtabledata = getInfo(sku)
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
    if os.path.exists(FILE_CONFIG_DETAIL) and os.path.exists(TEMPFILE_CONFIG_DETAIL): 
        if os.path.exists(BACKFILE_CONFIG_DETAIL):
            os.remove(BACKFILE_CONFIG_DETAIL)
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
                for index in ["年", "月", "日", "星期", "时间", "ID", "LINK", "商品全名", "价格", "店铺", "品牌"]: 
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
def generateTable(fData, keyword, count):
    TEMPFILE_DATA = "_data_" + str(KEYWORD) + ".csv"
    BACKFILE_DATA = "_data_" + str(KEYWORD) + ".backup.csv"

    #读取config文件
    listIndex, listDetail, listAdditional = getConfig(keyword)
    

    #生成临时数据文件的表头
    row = ["年", "月", "日", "星期", "时间", "ID", "LINK", "商品全名", "价格", "店铺", "品牌", SPECIAL_SPLIT]
    for index in listIndex:
        row.append(index)
    row.append(SPECIAL_SPLIT)   
    for index in listDetail:
        row.append(index) 
    row.append(SPECIAL_SPLIT)
    row.extend(["好评率", "中评率", "差评率", "好评数", "中评数", "差评数"])
    #for i in range(NUMTAGS):
    #    row.append("标签")                
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
        listsku = getList(keyword, count)
        print("Available records: ", len(listsku))
        #print(listsku)
        #加入手动添加的sku货号
        listsku += listAdditional
        listsku = set(listsku)
        print("Available records + additional: ", len(listsku))
        #实际要抓取的sku货号
        listskuThis = list(set(listsku) - set(listSkuOld))
        print("Excuting records: ", len(listskuThis))

        #对每个sku，抓取价格和信息
        for sku in listskuThis:
            print("Getting Price and Information for Sku "+str(sku))
            price = getPrice_2(sku)
           
            skuname, shop, brand, listinfo, listtableindex, listtabledata = getInfo(sku)
            summary = getComment_2(sku)
            
            if price == None or price == "" or skuname == None or skuname == "" or listinfo == None or len(listinfo) == 0 or summary[0] == 0:
                time.sleep(3)
                continue    #信息不全，跳过这一条不写入
            
            #信息准备好后开始一次性写入一行
            row = [time.strftime("%Y", time.localtime()), time.strftime("%m", time.localtime()), time.strftime("%d", time.localtime()), time.strftime("%A", time.localtime()), time.strftime("%H:%M", time.localtime()), SPECIAL_ID_HEAD+str(sku), 'https://item.jd.com/'+str(sku)+'.html', skuname, price, shop, brand, SPECIAL_SPLIT]
            listinfoindex = [x.split("：")[0] for x in listinfo]
            listinfodata = [x.split("：")[1] for x in listinfo]
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


# ======== MAIN ========
#定义参数列表
def getArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("--search", type=int, default=0)
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--setup", type=int, default=0)
    args = parser.parse_args()
    return args



if __name__ == "__main__":
    #获取参数，search取得待搜索的字符串例如“游戏本”“显卡”，COUNT希望抓取的sku数量
    args = getArgs()
    SEARCH = args.search
    COUNT = args.count
    SETUP = args.setup
    
    #转换序号为关键字
    #KeywordList = ["游戏本", "轻薄本", "设计本", "显卡", "EVO笔记本"]#定义关键字列表，注意该关键字会在config文件中对应相关配置
    rowsKeywordList = parseCsv(FILE_CONFIG_MASTER)
    KeywordList = rowsKeywordList[0]
    #print(KeywordList)
    KEYWORD = KeywordList[SEARCH]
    print("Get data for segment: " + KEYWORD)
    
    if SETUP == 1:
        #对新的搜索关键字，生成config参数，后期也可以自行修改
        generateConfig(KEYWORD)
    else:
        #定义保存数据的表格文件名
        fData ="DATA_"+str(KEYWORD)+"_"+time.strftime("%Y_%m", time.localtime())+".csv"
        
        #生成表格
        generateTable(fData, KEYWORD, COUNT)

    print("Finished. ")