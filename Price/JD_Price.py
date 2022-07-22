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

COOKIE = "__jdu=1597106510361611076602; shshshfpa=e8c04075-2ed8-8c17-9a2e-5eb000215962-1597106511; shshshfpb=hYFEa8t4oszf5zty/aI7r1Q==; __jdv=76161171|direct|-|none|-|1638343313368; PCSYCityID=CN_310000_310100_310115; areaId=2; pinId=lSwRbMKd-74tBDbKmwsL1w; pin=FioreZhang; unick=FioreZhang; _tp=IcTvqSKCNvN8JKtp2uhsOg==; _pst=FioreZhang; ipLoc-djd=2-2830-51803-0; shshshfp=1a5e708b76fe26c8443f300d10b6b119; __jdc=122270672; TrackID=1texs4UqbtSbga2lScwdKjyLU1dxI-DB0NDp4q-ecux3z05dNnD-GBuEqiKGI76Yahe2TyZuA9haOhmfryZoVObMVU5Blw2OGuodJPOTZI55Rg3ppuZFIZRJp4zXhTK9Z; ceshi3.com=201; token=d0bf370435bc5fdd1c4f0060845b90ec,3,910290; __tk=16101e1ef5c5c67686e452e544f92431,3,910290; __jda=122270672.1597106510361611076602.1597106510.1638519922.1638522072.28; wlfstk_smdl=3wsa372k6pi0qybgr9d6jik4x36tuyey; thor=C415B3C186C7F2E97A4AA78C1DB6835F00E6CC47BD365631899C49AF02D279F7D1B6355EBCA57C5EB2D804361F59F9FB130C3B5BAFFC0E60CF3D3E188C6F8070506E5655721308965D80B714DA9E74A333E85A90096D24486526F62BE36DDAECDA26E9A7827F47C1C8C295F580CBB7D0C966573D7A7763355B538E7781804595D649B12AAB2A8FF5FEE1B50382879E8D; __jdb=122270672.4.1597106510361611076602|28.1638522072; shshshsID=bf5b86abc43adfacda49721ea63f70cd_2_1638522376662; 3AB9D23F7A4B3C9B=IABYFHSAZ5YE4JK67BOOHWXZM3E3Q6LHRDFAOMFFBNIQYMWUZOXRA33UAIVOJD5FAGMHAXRKCCL2HARJ4LAJGRSQHE" 

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
        skulist += getListPageUp(keyword, page)
        skulist += getListPageDown(keyword, page)
        skulist = list(set(skulist)) #去重
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
        except Exception as ex:
            print(ex)
            pass
        
        #if listskuname != [] and shop != [] and brand != [] and listinfo != []:
        if listskuname != [] and listinfo != []:
            break
        retry -= 1
        print("== Retry getInfo(), can fix occational network lag")
        time.sleep(1)
    
    skuname = getSkuname(listskuname)
    if listshop != [] and listhshop != None:
        shop = listshop[0]
    else:
        shop = ''
    if listbrand != [] and listbrand != None:
        brand = listbrand[0]
    else:
        brand = ''
    
    print(skuname)
    print(shop)
    print(brand)
    print(listinfo)
    return skuname, shop, brand, listinfo

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

# ======== MISC ========
#定义参数列表
def getArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("--search", type=int, default=0)
    parser.add_argument("--count", type=int, default=100)
    args = parser.parse_args()
    return args

KeywordList = ["游戏本", "笔记本", "轻薄本", "全能本", "创意本"]

# ======== MAIN ========
if __name__ == "__main__":
    #获取参数，search取得待搜索的字符串例如“游戏本”“显卡”，COUNT希望抓取的sku数量
    args = getArgs()
    SEARCH = args.search
    COUNT = args.count
    
    KEYWORD = KeywordList[SEARCH]
    
    #getInfo(100025263673)
    #while(True):
    #    pass
    
    #取得待抓取信息列表，要求同目录下有相关配置文件例如“游戏本.txt”“显卡.txt”
    listIndex = []
    with open(KEYWORD+".txt", 'r', encoding='utf-8') as f:
        listIndex = list(f)
        f.close()
        listIndex = [x.strip() for x in listIndex if x.strip != '']
    print(listIndex)
    
    fData ="DATA_"+str(SEARCH)+"_"+time.strftime("%Y_%m", time.localtime())+".csv"
    
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
            row = ["商品全名", "价格", "店铺", "品牌"]
            for index in listIndex:
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
           
            skuname, shop, brand, listinfo = getInfo(sku)
            summary, tags = getComment(sku)
            
            if price == None or price == "" or skuname == None or skuname == "" or listinfo == None or len(listinfo) == 0 or summary[0] == 0:
                time.sleep(3)
                continue    #信息不全，跳过这一条不写入
            
            row = [skuname, price, shop, brand]
            listinfoindex = [x.split("：")[0] for x in listinfo]
            listinfodata = [x.split("：")[1] for x in listinfo]
            for index in listIndex:
                if index in listinfoindex:
                    row.append(listinfodata[listinfoindex.index(index)])
                else:
                    row.append("")
            for item in summary:
                row.append(item)
            for item in tags:
                row.append(item)
            appendCsv(fData, row) #写入
        
            time.sleep(2)   #慢一点……
