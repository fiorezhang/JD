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

RETRY = 5
TIMEOUT = 2
NUMTAGS = 12

# ======== CAPTURE PRICE ========
def getPrice(sku):
    head = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.131 Safari/537.36', 
            'Cookie': COOKIE}  
    url = 'https://p.3.cn/prices/mgets?skuIds=J_'+str(sku)
    
    price = None
    retry = RETRY
    while retry > 0:
        request = urllib.request.Request(url, headers=head)
        response = urllib.request.urlopen(request)
        content = response.read()
        try:
            result = json.loads(content)
            price = result[0]['p']
        except:
            pass
        else:
            break
        retry -= 1
        print("== RETRYING ==")
        time.sleep(2)
    print(price)
    return price
    
    
getPrice(100033822492)    