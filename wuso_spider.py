# -*- coding: utf-8 -*-
import socks
import socket
#socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, "127.0.0.1", 8080)
#socket.socket = socks.socksocket
import re
import urllib2  
import requests
import sqlite3
import random
import string
from time import gmtime, strftime
import threading
from bs4 import BeautifulSoup

import sys
reload(sys)
sys.setdefaultencoding("utf-8")

#Some User Agents
hds=[{'User-Agent':'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6'},\
    {'User-Agent':'Mozilla/5.0 (Windows NT 6.2) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.12 Safari/535.11'},\
    {'User-Agent':'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.2; Trident/6.0)'},\
    {'User-Agent':'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:34.0) Gecko/20100101 Firefox/34.0'},\
    {'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/44.0.2403.89 Chrome/44.0.2403.89 Safari/537.36'},\
    {'User-Agent':'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_8; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50'},\
    {'User-Agent':'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50'},\
    {'User-Agent':'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0'},\
    {'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:2.0.1) Gecko/20100101 Firefox/4.0.1'},\
    {'User-Agent':'Mozilla/5.0 (Windows NT 6.1; rv:2.0.1) Gecko/20100101 Firefox/4.0.1'},\
    {'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_0) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11'},\
    {'User-Agent':'Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; en) Presto/2.8.131 Version/11.11'},\
    {'User-Agent':'Opera/9.80 (Windows NT 6.1; U; en) Presto/2.8.131 Version/11.11'}]
    

lock = threading.Lock()
filenames_url = {}

def download_image(url):
    filename_time = strftime("%Y-%m-%d-%H-%M-%S", gmtime())
    filename_tag = ''.join(random.choice(string.ascii_uppercase+string.digits) for _ in range(8))
    filename = 'porn_images/%s_%s.jpg' % (filename_time, filename_tag)
    filenames_url[filename] = url
    try:
        with open(filename, 'wb') as f:
            req = urllib2.Request(url,headers=hds[random.randint(0,len(hds)-1)])
            f.write(urllib2.urlopen(req,timeout=10).read())

    except (urllib2.HTTPError, urllib2.URLError), e:
        print e
        exit(-1)
    except Exception,e:
        print e
        exit(-1)
 
def sample_spider(dst_url):
    try:
        req = urllib2.Request(dst_url,headers=hds[random.randint(0,len(hds)-1)])
        source_code = urllib2.urlopen(req,timeout=10).read()
        plain_text=unicode(source_code)#,errors='ignore')   
        soup = BeautifulSoup(plain_text)
    except (urllib2.HTTPError, urllib2.URLError), e:
        print e
        exit(-1)
    except Exception,e:
        print e
        exit(-1)
    
    img_list=soup.findAll('img',{'class':'zoom'})
    for img_sample in img_list:
        postfix = img_sample.get('zoomfile')
        if postfix:
            img_url = 'https://wuso.me/' + postfix
            download_image(img_url)        

    
def do_page_spider(page_id=1):
    url = "https://wuso.me/forum-photos-%d.html" % page_id
    try:
        req = urllib2.Request(url,headers=hds[random.randint(0,len(hds)-1)])
        source_code = urllib2.urlopen(req,timeout=500).read()
        plain_text=unicode(source_code)#,errors='ignore')   
        soup = BeautifulSoup(plain_text)
    except (urllib2.HTTPError, urllib2.URLError), e:
        print e
        return
    except Exception,e:
        print e
        return

    sample_urls = soup.find('ul', {'class':'ml waterfall cl'}).findAll('div', {'class':'c cl'})
    
    threads=[]
    for sample_url in sample_urls:
        dst_url = sample_url.find('a').get('href')
        t=threading.Thread(target=sample_spider,args=(dst_url,))
        threads.append(t)
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print "Got page_%d samples" % page_id

if __name__=="__main__":
    proxy = urllib2.ProxyHandler({'https': 'socks5://127.0.0.1:8123', 'http': '127.0.0.1:8123'})
    opener = urllib2.build_opener(proxy)
    urllib2.install_opener(opener)

    for page_id in range(17,235):
        do_page_spider(page_id)
        print "Doing %d pages" % page_id
    with open('urls.txt','w') as f:
        for filename in filenames_url.keys():
            f.write('%s @ %s\n' % (filename, filenames_url[filename]))
