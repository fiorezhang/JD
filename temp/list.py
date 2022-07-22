import requests
from lxml import etree
import time
import csv
#定义函数抓取每页前30条商品信息
def crow_first(n):
    #构造每一页的url变化
    url='https://search.jd.com/Search?keyword=游戏本&enc=utf-8&page='+str(2*n-1)
    head = {'authority': 'search.jd.com',
            'method': 'GET',
            'scheme': 'https',
            'user-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36',
            }
    r = requests.get(url, headers=head)
    #指定编码方式，不然会出现乱码
    r.encoding='utf-8'
    html1 = etree.HTML(r.text)
    #定位到每一个商品标签li
    datas=html1.xpath('//li[contains(@class,"gl-item")]')
    #将抓取的结果保存到本地CSV文件中
    with open('JD_Phone.csv','a',newline='',encoding='utf-8')as f:
        write=csv.writer(f)
        for data in datas:
            p_sku = data.xpath('@data-sku')
            write.writerow(p_sku)
    f.close()
#定义函数抓取每页后30条商品信息
def crow_last(n):
    #获取当前的Unix时间戳，并且保留小数点后5位
    a=time.time()
    b='%.5f'%a
    url='https://search.jd.com/s_new.php?keyword=游戏本&enc=utf-8&page='+str(2*n)+'&s='+str(48*n-20)+'&scrolling=y&log_id='+str(b)
    head = {'authority': 'search.jd.com',
            'method': 'GET',
            'scheme':'https',
            'referer': 'https://search.jd.com/Search?keyword=%E6%89%8B%E6%9C%BA&enc=utf-8',
            'user-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36',
            'x-requested-with': 'XMLHttpRequest',
    }
    r = requests.get(url, headers=head)
    r.encoding = 'utf-8'
    html1 = etree.HTML(r.text)
    datas = html1.xpath('//li[contains(@class,"gl-item")]')
    with open('JD_Phone.csv','a',newline='',encoding='utf-8')as f:
        write=csv.writer(f)
        for data in datas:
            p_sku = data.xpath('@data-sku')
            write.writerow(p_sku)
    f.close()
 
 
if __name__=='__main__':
    for i in range(1,11):
        #下面的print函数主要是为了方便查看当前抓到第几页了
        print('***************************************************')
        try:
            print('   First_Page:   ' + str(i))
            crow_first(i)
            print('   Finish')
        except Exception as e:
            print(e)
        print('------------------')
        try:
            print('   Last_Page:   ' + str(i))
            crow_last(i)
            print('   Finish')
        except Exception as e:
            print(e)