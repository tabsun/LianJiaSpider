# -*- coding: utf-8 -*-
import re
import json
import urllib2  
import sqlite3
import random
import threading
from bs4 import BeautifulSoup

import sys
reload(sys)
sys.setdefaultencoding("utf-8")

regions=["heping", "nankai", "hexi", "hebei", "hedong", "hongqiao", "xiqing", "beichen", "dongli", "jinnan", "tanggu", "kaifaqu", "wuqing", "binhaixinqu"]


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

if __name__=="__main__":
    command="create table if not exists chengjiao (url TEXT primary key UNIQUE, xq_name TEXT, sold_in_90_days INT, to_be_rent INT, house_num INT, mean_price INT, selling INT, address TEXT)"
    db_cj=SQLiteWraper('lianjia-cj.db',command)
    
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
