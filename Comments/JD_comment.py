#-*- coding: utf-8 -*-

# ================================================================  #
#                                                                   #
#                    INTERNAL STUDY ONLY !                          #
#                                                                   #
# ================================================================  #

import requests
import urllib.request
from lxml import etree
import re
import json
import csv
import argparse
import time
import sys
import os

import matplotlib.pyplot as plt
from wordcloud import WordCloud, STOPWORDS
import jieba
import imageio
from collections import Counter

COOKIE = "__jdu=1597106510361611076602; shshshfpa=e8c04075-2ed8-8c17-9a2e-5eb000215962-1597106511; shshshfpb=hYFEa8t4oszf5zty/aI7r1Q==; __jdv=76161171|direct|-|none|-|1638343313368; PCSYCityID=CN_310000_310100_310115; areaId=2; pinId=lSwRbMKd-74tBDbKmwsL1w; pin=FioreZhang; unick=FioreZhang; _tp=IcTvqSKCNvN8JKtp2uhsOg==; _pst=FioreZhang; ipLoc-djd=2-2830-51803-0; shshshfp=1a5e708b76fe26c8443f300d10b6b119; __jdc=122270672; TrackID=1texs4UqbtSbga2lScwdKjyLU1dxI-DB0NDp4q-ecux3z05dNnD-GBuEqiKGI76Yahe2TyZuA9haOhmfryZoVObMVU5Blw2OGuodJPOTZI55Rg3ppuZFIZRJp4zXhTK9Z; ceshi3.com=201; token=d0bf370435bc5fdd1c4f0060845b90ec,3,910290; __tk=16101e1ef5c5c67686e452e544f92431,3,910290; __jda=122270672.1597106510361611076602.1597106510.1638519922.1638522072.28; wlfstk_smdl=3wsa372k6pi0qybgr9d6jik4x36tuyey; thor=C415B3C186C7F2E97A4AA78C1DB6835F00E6CC47BD365631899C49AF02D279F7D1B6355EBCA57C5EB2D804361F59F9FB130C3B5BAFFC0E60CF3D3E188C6F8070506E5655721308965D80B714DA9E74A333E85A90096D24486526F62BE36DDAECDA26E9A7827F47C1C8C295F580CBB7D0C966573D7A7763355B538E7781804595D649B12AAB2A8FF5FEE1B50382879E8D; __jdb=122270672.4.1597106510361611076602|28.1638522072; shshshsID=bf5b86abc43adfacda49721ea63f70cd_2_1638522376662; 3AB9D23F7A4B3C9B=IABYFHSAZ5YE4JK67BOOHWXZM3E3Q6LHRDFAOMFFBNIQYMWUZOXRA33UAIVOJD5FAGMHAXRKCCL2HARJ4LAJGRSQHE" 

RETRY = 3

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

def getComment(sku):
    head = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.131 Safari/537.36'}  
    url = 'https://sclub.jd.com/comment/skuProductPageComments.action?&productId=' + str(sku) + '&score=0&sortType=5&page=0&pageSize=10&isShadowSku=0&fold=1'
    print(url)
    #html = requests.get(url)
    #print(html.status_code)
    
    #提取最多多少条标签，电脑页面大部分tag数量是11个及以内
    numTags = 12
    
    #获得原始评论页面的数据，提取总结部分与标签部分的数据
    tags = []
    retry = RETRY
    while retry > 0:
        request = urllib.request.Request(url, headers=head)
        response = urllib.request.urlopen(request)
        content = response.read().decode('gbk')
        #print(content)
        try:
            result = json.loads(content)
            summary = result['productCommentSummary']
            tags = result['hotCommentTagStatistics']
            if summary != "" and summary != None:
                break
        except Exception as ex:
            pass            
        retry -= 1
        print("== RETRYING ==")
        time.sleep(2)
    
    #提取好评率，中评率，差评率
    commentSummary = [0, 0, 0]
    try:
        commentSummary = [summary['goodRate'], summary['generalRate'], summary['poorRate']]
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
    
def getCommentDetails(sku):
    head = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.131 Safari/537.36'}  
    
    commentPool = {'good':[], 'middle':[], 'bad':[]}
    score = {'good':3, 'middle':2, 'bad':1} #0 all, 1 bad, 2 middle, 3 good
    pagenum = {'good':100, 'middle':10, 'bad':10}
    
    for level in ['good', 'middle', 'bad']:
        for page in range(pagenum[level]):
            #url = 'https://sclub.jd.com/comment/productPageComments.action?&productId=' + str(sku) + '&score=0&sortType=5&page='+ str(page) +'&pageSize=10&isShadowSku=0&fold=1'
            url = 'https://sclub.jd.com/comment/skuProductPageComments.action?&productId=' + str(sku) + '&score=' + str(score[level]) + '&sortType=5&page='+ str(page) +'&pageSize=10&isShadowSku=0&fold=1'
            print(url)
            html = requests.get(url)
            print(html.status_code)
        
            #获得原始评论页面的数据，提取总结部分与标签部分的数据
            retry = RETRY
            while retry > 0:
                request = urllib.request.Request(url, headers=head)
                response = urllib.request.urlopen(request)
                content = response.read().decode('gbk')
                print(content)
                try:
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
                
        print(commentPool[level])
    return commentPool    
    
def saveComment(sku, level, commentPool, path): 
    commentList = commentPool[level]
    if path is None or path == "":
        path = str(sku)
    if (len(commentList) > 0):
        mkdir(path)
        #保存所有评论文本
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
        # - 生成词频
        c = Counter()
        for x in commentAllWordSplit.split(' '):
            if len(x) > 1 and x not in stopwords:
                c[x] += 1
        with open(path+os.sep+path+'_'+level+'.csv', 'w', encoding='utf-8-sig') as f:
            for (k,v)in c.most_common(50):
                f.write(k+','+str(v)+'\n')
            f.close()
        # - 生成词云
        contentWordCloud = WordCloud(background_color = 'white', mask = imageio.imread('comment'+os.sep+level+'.jpg'), width = 400, height = 200, max_font_size= 60, min_font_size = 10, font_path = 'comment/fonts/sthupo.ttf', stopwords= stopwords).generate(commentAllWordSplit)
        # - 生成图片并保存
        plt.imshow(contentWordCloud)
        plt.axis("off")
        plt.savefig(path+os.sep+path+'_'+level+'.png')
        #plt.show()

# ======== MISC ========
#定义参数列表
def getArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sku", type=int, default=0)
    parser.add_argument("--list", type=str, default='')
    args = parser.parse_args()
    return args
    
# ======== MAIN ========
if __name__ == "__main__":
    args = getArgs()
    sku = args.sku
    list = args.list

    if list != '':
        with open(list+'.txt', 'r') as f:
            commentPool = {'good':[], 'middle':[], 'bad':[]}
            while True:
                line = f.readline()
                print(line)
                if line != '':
                    sku = int(line)
                    commentCurrent = getCommentDetails(sku)
                    for level in ['good', 'middle', 'bad']:
                        commentPool[level].extend(commentCurrent[level])
                else:
                    break
            for level in ['good', 'middle', 'bad']:
                saveComment(sku, level, commentPool, list)        
    else:
        commentPool = getCommentDetails(sku)
        for level in ['good', 'middle', 'bad']:
            saveComment(sku, level, commentPool, "")