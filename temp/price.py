#-*- coding: utf-8 -*-
import urllib.request
import re
import json
import sys
 
HEADER={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.131 Safari/537.36'}  
 

#商品编号
code='10037796156060'
#请求地址
url='https://p.3.cn/prices/mgets?skuIds=J_'+code
 
 
#获取地址
request=urllib.request.Request(url, headers=HEADER)
#打开连接
response=urllib.request.urlopen(request)
 
content=response.read()
print(content)
 
result=json.loads(content)
 
json=result[0]
print('价格:'+json['p'])