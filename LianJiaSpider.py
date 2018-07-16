# -*- coding: utf-8 -*-
import re
import os
import json
import urllib2  
import sqlite3
import random
import threading
from bs4 import BeautifulSoup

import sys
reload(sys)
sys.setdefaultencoding("utf-8")

#登录，不登录不能爬取三个月之内的数据
import LianJiaLogIn


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
    

regions=["heping", "nankai", "hexi", "hebei", "hedong", "hongqiao", "xiqing", "beichen", "dongli", "jinnan", "tanggu", "kaifaqu", "wuqing", "binhaixinqu"]


lock = threading.Lock()


class SQLiteWraper(object):
    """
    数据库的一个小封装，更好的处理多线程写入
    """
    def __init__(self,path,command='',*args,**kwargs):  
        self.lock = threading.RLock() #锁  
        self.path = path #数据库连接参数  
        
        if command!='':
            conn=self.get_conn()
            cu=conn.cursor()
            cu.execute(command)
    
    def get_conn(self):  
        conn = sqlite3.connect(self.path)#,check_same_thread=False)  
        conn.text_factory=str
        return conn   
      
    def conn_close(self,conn=None):  
        conn.close()  
    
    def conn_trans(func):  
        def connection(self,*args,**kwargs):  
            self.lock.acquire()  
            conn = self.get_conn()  
            kwargs['conn'] = conn  
            rs = func(self,*args,**kwargs)  
            self.conn_close(conn)  
            self.lock.release()  
            return rs  
        return connection  
    
    @conn_trans    
    def execute(self,command,method_flag=0,conn=None):  
        cu = conn.cursor()
        try:
            if not method_flag:
                cu.execute(command)
            else:
                cu.execute(command[0],command[1])
            conn.commit()
        except sqlite3.IntegrityError,e:
            #print e
            return -1
        except Exception, e:
            print e
            return -2
        return 0
    
    @conn_trans
    def fetchall(self,command="select * from chengjiao",conn=None):
        cu=conn.cursor()
        lists=[]
        try:
            cu.execute(command)
            lists=cu.fetchall()
        except Exception,e:
            print e
            pass
        return lists


def gen_chengjiao_insert_command(info_dict):
    """
    生成成交记录数据库插入命令
    """
    info_list=['url','xq_name','sold_in_90_days','to_be_rent','house_num','mean_price','selling','address']
    t=[]
    for il in info_list:
        if il in info_dict:
            t.append(info_dict[il])
        else:
            t.append('')
    t=tuple(t)
    command=(r"insert into chengjiao values(?,?,?,?,?,?,?,?)",t)
    return command


def chengjiao_page_spider(db_cj, region, page_id):
    """
    爬取页面链接中的小区信息
    """
    url_page = "https://tj.lianjia.com/xiaoqu/%s/pg%dcro11/" % (region, page_id)
    try:
        req = urllib2.Request(url_page,headers=hds[random.randint(0,len(hds)-1)])
        source_code = urllib2.urlopen(req,timeout=10).read()
        plain_text=unicode(source_code)#,errors='ignore')   
        soup = BeautifulSoup(plain_text)
    except (urllib2.HTTPError, urllib2.URLError), e:
        print e
        exit(-1)
    except Exception,e:
        print e
        exit(-1)
    
    xiaoqu_list=soup.findAll('li',{'class':'clear xiaoquListItem'})
    for xq in xiaoqu_list:
        info_dict={}
        xq_name = xq.find('div', {'class':'title'}).find('a').text
        xq_url = xq.find('div', {'class':'title'}).find('a').get('href')
        xq_90cj = xq.find('div', {'class':'houseInfo'}).find('a',{'title':'%s网签'%xq_name}).text.split('成交')[1].split('套')[0]
        xq_renting = xq.find('div', {'class':'houseInfo'}).find('a',{'title':'%s租房'%xq_name}).text.split('套')[0]
        xq_price = xq.find('div', {'class':'totalPrice'}).find('span').text
        xq_sellcount = xq.find('div', {'class':'xiaoquListItemSellCount'}).find('a').find('span').text


        # get xiaoqu info
        url = xq_url.decode('utf-8')
        try:
            req = urllib2.Request(url,headers=hds[random.randint(0,len(hds)-1)])
            source_code = urllib2.urlopen(req,timeout=10).read()
            plain_text=unicode(source_code)#,errors='ignore')   
            soup = BeautifulSoup(plain_text)
        except (urllib2.HTTPError, urllib2.URLError), e:
            print e
            exit(-1)
        except Exception,e:
            print e
            exit(-1)
        infos = soup.findAll('div', {'class':'xiaoquInfoItem'})    
        for info in infos:
            if info.find('span', {'class':'xiaoquInfoLabel'}).text.decode('utf-8') == '房屋总数':
                house_num = int(info.find('span', {'class':'xiaoquInfoContent'}).text.decode('utf-8').split('户')[0])
        address_node = soup.find('div', {'class':'detailDesc'})
        if address_node:
            address = address_node.text.decode('utf-8')
        else:
            address = "天津市" + region + xq_name.decode('utf-8')
        print address

        info_dict.update({'house_num':house_num})
        info_dict.update({'xq_name':xq_name.decode('utf-8')})
        info_dict.update({'sold_in_90_days':int(xq_90cj)})
        info_dict.update({'url':xq_url.decode('utf-8')})
        info_dict.update({'to_be_rent':int(xq_renting)})
        info_dict.update({'address':address})
        if(xq_price == '暂无'):
            return
        info_dict.update({'mean_price':int(xq_price)})
        info_dict.update({'selling':int(xq_sellcount)})

        
        command=gen_chengjiao_insert_command(info_dict)
        db_cj.execute(command,1)

    
def chengjiao_region_spider(db_cj, region):
    """
    爬取大区域中的所有小区信息
    """
    url_region = "https://tj.lianjia.com/xiaoqu/%s/cro11/" % region
    try:
        req = urllib2.Request(url_region,headers=hds[random.randint(0,len(hds)-1)])
        source_code = urllib2.urlopen(req,timeout=5).read()
        plain_text=unicode(source_code)#,errors='ignore')   
        soup = BeautifulSoup(plain_text)
    except (urllib2.HTTPError, urllib2.URLError), e:
        print e
        return
    except Exception,e:
        print e
        return
    d="d="+soup.find('div',{'class':'page-box house-lst-page-box'}).get('page-data')
    exec(d)
    total_pages=d['totalPage']
    
    threads=[]
    for page_id in range(1, total_pages+1):
        t=threading.Thread(target=chengjiao_page_spider,args=(db_cj, region, page_id))
        threads.append(t)
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print "爬下了 %s 区全部的小区信息" % region


if __name__=="__main__":
    if os.path.exists("./lianjia-cj.db"):
        os.remove("./lianjia-cj.db")

    command="create table if not exists chengjiao (url TEXT primary key UNIQUE, xq_name TEXT, sold_in_90_days INT, to_be_rent INT, house_num INT, mean_price INT, selling INT, address TEXT)"
    db_cj=SQLiteWraper('lianjia-cj.db',command)
    
    #chengjiao_page_spider(db_cj, 'heping', 1)
    #爬下所有小区里的成交信息
    for region in regions:
        chengjiao_region_spider(db_cj, region)

    data = db_cj.fetchall()
    infos = []

    with open('./points.json','r') as points_f:
        points_list = json.load(points_f)
        points = dict()
        for point in points_list:
            points[point['name'].decode('utf-8')] = point

    for xq in data:
        name, sold, renting, house_num, price, selling, address = xq[1:]
        name = name.decode('utf-8')
        address = address.decode('utf-8')
        info = dict()
        info['name'] = name
        info['sold'] = sold
        info['renting'] = renting
        info['house_num'] = house_num
        info['price'] = price
        info['selling'] = selling
        info['address'] = address
        if name in points.keys():
            info['lng'] = points[name]['lng']
            info['lat'] = points[name]['lat']
        else:
            info['lng'] = -1.0
            info['lat'] = -1.0
        infos.append(info)

    with open('data.json', 'w') as f:
        content = json.dumps(infos)
        f.write("data = '%s';" % content)
