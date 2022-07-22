#-*- coding: utf-8 -*-
import urllib.request
import re
import json
import sys
import requests
from lxml import etree
 
COOKIE = "__jdu=1597106510361611076602; shshshfpa=e8c04075-2ed8-8c17-9a2e-5eb000215962-1597106511; shshshfpb=hYFEa8t4oszf5zty/aI7r1Q==; __jdv=76161171|direct|-|none|-|1638343313368; PCSYCityID=CN_310000_310100_310115; areaId=2; pinId=lSwRbMKd-74tBDbKmwsL1w; pin=FioreZhang; unick=FioreZhang; _tp=IcTvqSKCNvN8JKtp2uhsOg==; _pst=FioreZhang; ipLoc-djd=2-2830-51803-0; shshshfp=1a5e708b76fe26c8443f300d10b6b119; __jdc=122270672; TrackID=1texs4UqbtSbga2lScwdKjyLU1dxI-DB0NDp4q-ecux3z05dNnD-GBuEqiKGI76Yahe2TyZuA9haOhmfryZoVObMVU5Blw2OGuodJPOTZI55Rg3ppuZFIZRJp4zXhTK9Z; ceshi3.com=201; token=d0bf370435bc5fdd1c4f0060845b90ec,3,910290; __tk=16101e1ef5c5c67686e452e544f92431,3,910290; __jda=122270672.1597106510361611076602.1597106510.1638519922.1638522072.28; wlfstk_smdl=3wsa372k6pi0qybgr9d6jik4x36tuyey; thor=C415B3C186C7F2E97A4AA78C1DB6835F00E6CC47BD365631899C49AF02D279F7D1B6355EBCA57C5EB2D804361F59F9FB130C3B5BAFFC0E60CF3D3E188C6F8070506E5655721308965D80B714DA9E74A333E85A90096D24486526F62BE36DDAECDA26E9A7827F47C1C8C295F580CBB7D0C966573D7A7763355B538E7781804595D649B12AAB2A8FF5FEE1B50382879E8D; __jdb=122270672.4.1597106510361611076602|28.1638522072; shshshsID=bf5b86abc43adfacda49721ea63f70cd_2_1638522376662; 3AB9D23F7A4B3C9B=IABYFHSAZ5YE4JK67BOOHWXZM3E3Q6LHRDFAOMFFBNIQYMWUZOXRA33UAIVOJD5FAGMHAXRKCCL2HARJ4LAJGRSQHE" 
 
HEADER={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36',  
        'cookie': COOKIE
        }  


#商品编号
code='100017048040'
#请求地址
url='https://item.jd.com/'+str(code)+'.html'
print(url)

r = requests.get(url, headers=HEADER)
#指定编码方式，不然会出现乱码
r.encoding='utf-8'
html1 = etree.HTML(r.text)
#print(etree.tostring(html1).decode('utf-8'))


#定位到每一个商品标签li
datas=html1.xpath('//ul[@class="parameter2 p-parameter-list"]/li/text()')
print(datas)

brand=html1.xpath('//ul[@id="parameter-brand"]/li/@title')
print(brand)

shop=html1.xpath('//div[@class="J-hove-wrap EDropdown fr"]/div/div/a/text()')
print(shop)