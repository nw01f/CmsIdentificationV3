#!/usr/bin/env python
# -*- coding:utf-8 -*-

#引入基类
import os
import re
import json
import time
import thread
import gevent
import hashlib
import sqlite3
import requests

from colorama import init,Fore
from gevent.queue import Queue
from gevent import monkey;monkey.patch_all()
from openpyxl import Workbook

### 引入自定义类
from lib.URL import URL
from lib.ARGS import Args

class CmsInfo(object):
    """
    CMS识别主体类函数
    """
    def __init__(self, desurl, thread, filename=None, report=False):
        self.desurl   = desurl      #目标地址
        self.thread   = thread      #线程数量
        self.filename = filename    #url列表文件
        self.report   = report.split('.')[0]+'.xlsx' if report else None      #报告文件
        self.Result   = {}          #单个地址扫描结果
        self.Res      = Queue()     #扫描结果队列
        self.Url      = Queue()     #扫描目标队列
        self.Finger   = Queue()     #指纹队列
        self.Msg      = Queue()     #消息队列
        self.header1     = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:56.0) Gecko/20100101 Firefox/56.0',
                            'Referer':'http://whatweb.bugscaner.com/look/'}
        self.header2     = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:56.0) Gecko/20100101 Firefox/56.0'}

    @property
    def SqliteHandle(self):
        """
        连接SQLite数据库
        """
        Db = './base/CmsFingerPrint.db'
        if not os.path.exists(Db) :
             print(Fore.RED+u'[-] 数据库链接失败,请检查数据库文件以及数据库文件地址')
             exit()
        conn = sqlite3.connect(Db)
        return conn,conn.cursor()

    def UrlMakeQueue(self):
        """
        将目标URL放入队列
        """
        if self.desurl is not None :
            U  = URL(self.desurl)
            Us = U.get_url_string()
            Us = Us.rstrip('/')
            self.Url.put(Us)
            return True
        elif self.filename is not None:
            if not os.path.exists(self.filename) :
                print(Fore.RED + u'[-] 文件不存在，请输入正确的文件名')
                exit()
            else:
                try:
                    Fn = open(self.filename,'r')
                except BaseException as e:
                    print(Fore.RED + u'[-] 文件打开失败，请检查文件权限'+str(e.message))
                    exit()
                lines = Fn.readlines()
                for t in lines :
                    U = URL(t.strip())
                    Us = U.get_url_string()
                    self.Url.put(Us)
                Fn.close()
                return True

    def FingerMakeQueue(self):
        """
        将本地指纹放入队列
        """
        conn,handle = self.SqliteHandle
        sql = "SELECT Uri,Method,Re,MD5,CmsName,ID FROM CmsInfo ORDER BY Hits DESC"
        rows = handle.execute(sql)
        for row in rows:
            # 返回元组 (Uri,Method,Re,MD5,CmsName,ID)
            self.Finger.put(row)
        conn.close()
    
    def UpdateHits(self,ID):
        """
        更新指纹命中数
        """
        conn,handle = self.SqliteHandle
        sql= "UPDATE CmsInfo SET Hits = Hits + 1 WHERE ID=%d" %ID
        handle.execute(sql)
        conn.commit()
        conn.close()

    def ClearQueue(self):
        """
        将指纹信息队列清空
        """
        while not self.Finger.empty():
            self.Finger.get()
    
    def MakeLog(self):
        """
        生成错误日志文件
        """
        if not self.Msg.empty() :
            with open('error.log','a+') as target:
                while not self.Msg.empty() :
                    message = self.Msg.get()
                    for k,v in message.items():
                        target.write('[%s]:%s\n' %(k,v.encode('utf8','ignore')) )
            target.close()
        print(Fore.GREEN +'[+] [Message]:'+ u'错误日志生成完毕...')

    def GetMd5(self, html):
        """
        获取文件的MD5值
        """
        md5 = hashlib.md5()
        md5.update(html)
        return md5.hexdigest()
    
    def GetHtHandle(self,url):
        """
        获取网页请求句柄
        """
        try:
            HtHandle = requests.get(url, headers=self.header2, timeout=3 )
        except requests.exceptions.HTTPError as e :
            msg = {'Error':u'HTTP请求错误:'+url+' '+str(e.message)}
            self.Msg.put(msg)
            msg.clear()
            return False
        except requests.exceptions.Timeout as e:
            msg = {'Error':u'请求超时:'+url+' '+str(e.message)}
            self.Msg.put(msg)
            msg.clear()
            return False
        except requests.exceptions.ConnectionError as e :
            msg = {'Error':u'拒绝连接:'+url+' '+str(e.message)}
            self.Msg.put(msg)
            msg.clear()
            return False
        except requests.exceptions.InvalidURL as e:
            msg = {'Error':u'无效的URL:'+url+' '+str(e.message)}
            self.Msg.put(msg)
            return False
        return HtHandle

    def GetCharSet(self,HtHandle):
        """
        获取网站编码
        """
        html = HtHandle.content
        pattern = r'.*charset="?(.*?)"'
        SearchObl = re.search(pattern,html)
        if SearchObl :
            return SearchObl.group(1)
        else:
            return False

    def GetServer(self,HtHandle):
        """
        通过HTTP响应头获取服务器版本
        """
        header = HtHandle.headers
        header = dict(header)
        if header.has_key('Server') :
            if header['Server'].find(' ') != -1 :
                info = header['Server'].split(' ')
                # [服务器，操作系统，中间件，编程语言]
                # [服务器，操作系统，编程语言]
                # 只考虑普通情况，特殊情况需要人工干预
                if len(info) == 4 :
                    res = {'server':info[0]+' '+info[2],'os':info[1],'lan':info[3]}
                    return res
                elif len(info) == 3:
                    res = {'server':info[0],'os':info[1],'lan':info[2]}
                    return res
                elif len(info) == 2:
                    res = {'server':info[0],'os':info[1]}
                    return res
                else :
                    res={'server':header['Server']}
                    return res
            else:
                res={'server':header['Server']}
                return res
        else:
            return False

    def GetLanguage(self,HtHandle):
        """
        通过HTTP响应头获取网站编程语言
        """
        header = HtHandle.headers
        header = dict(header)
        if header.has_key('X-Powered-By') :
            # 此处特殊情况下会出现cms名称，留下if判断，发现新的字段可以进行添加。
            if header['X-Powered-By'].find('ThinkPHP') != -1 :
                res = {'lan':'PHP','CmsName':'ThinkPHP'}
                return res
            else:
                res = {'lan':header['X-Powered-By']}
                return res
        else:
            return False

    def GetFinger(self,url):
        """
        使用本地指纹进行指纹识别
        """
        while not self.Finger.empty():
            CmsFinger = self.Finger.get()
            #CmsFinger元组格式 (Uri,Method,Re,MD5,CmsName,ID)
            #(0,1,2,3,4,5)
            FinalUrl  = url + CmsFinger[0]
            HtHandle  = self.GetHtHandle(FinalUrl)
            if not HtHandle :
                continue
            # Method分两值(1:通过正则识别;2:通过MD5识别)
            Method    = CmsFinger[1]
            if Method == 1 :
                Re = CmsFinger[2]
                Html = HtHandle.text
                flag = re.search(Re,Html)
                if flag:
                    self.Result['CmsName'] = CmsFinger[4]
                    ID = CmsFinger[5]
                    self.UpdateHits(ID)
                    self.ClearQueue()
                    return True
            if Method == 2 :
                MD5 = CmsFinger[3]
                Html = HtHandle.content
                HMd5 = self.GetMd5(Html)
                if HMd5 == MD5:
                    self.Result['CmsName'] = CmsFinger[4]
                    ID = CmsFinger[5]
                    self.UpdateHits(ID)
                    self.ClearQueue()
                    return True

    def GetFingerFromInternet(self, url):
        """
        通过whatweb获取CMS指纹信息
        http://whatweb.bugscaner.com/look/
        每次只能查询100次
        """
        whatweb = 'http://whatweb.bugscaner.com/what/'
        HtHandle = self.GetHtHandle(whatweb)
        if not HtHandle :
            print(Fore.RED+u"[-] WhatWeb无法访问,请检查网络环境")
            return False
        data = {'url':url}
        try:
            HtHandle = requests.post(whatweb,data=data,headers=self.header1,timeout=5)
        except BaseException as e:
            print(Fore.RED+u'[-] 向WhatWeb发送数据异常.'+url+' '+str(e.message) )
            return False
        info = json.loads(HtHandle.text)
        if info['error'] == 'no' :
            try:
                self.Result['CmsName'] = info['CMS']
            except:
                return False
            return True
        else:
            # 返回错误
            if info['error'] == '1' :
                msg = {'Message':'Domain cannot be accessed.Url: %s'%(url)}
                self.Msg.put(msg)
                msg.clear()
                return False
            if info['error'] == '2' :
                msg = {'Message':'More than 100 queries. Url: %s' %(url)}
                self.Msg.put(msg)
                msg.clear()
                return False
            if info['error'] == '3' :
                msg = {'Message':'Not recognized.Url: %s' %(url)}
                self.Msg.put(msg)
                msg.clear()
                return False
            if info['error'] == '4' :
                msg = {'Message':'Server debugging. Url: %s' %(url)}
                self.Msg.put(msg)
                msg.clear()
                return False
            if info['error'] == '5' :
                msg = {'Message':'Access too fast. Url: %s' %(url)}
                self.Msg.put(msg)
                msg.clear()
                return False

    def OutputHead(self):
        """
        输出头样式
        """
        print('-'*91)
        Hs = '|{:^7}|{:^9}|{:^9}|{:^10}|{:^25}|{:^25}|'.format('Os','CharSet','Server','Language','CmsName','Url')
        print(Hs)
        print('-'*91)

    def OutputResult(self):
        """
        格式化向控制台输出扫描结果
        """
        if self.report:
            filename = self.report
            wb = Workbook()
            ws = wb.create_sheet(u'扫描结果',index=0)
            ws.append(['Os','CharSet','Server','CmsName','Url'])
        self.OutputHead()
        dv = []
        while not self.Res.empty():
            Result = self.Res.get()
            s = '|{:<7}|{:<9}|{:<9}|{:<10}|{:<25}|{:<25}|'.format(Result['Os'],Result['CharSet'],Result['Server'],Result['Language'],Result['CmsName'].encode('gbk','ignore'),Result['Url'])
            print(s)
            print('-'*91)
            if self.report:
                dv = [Result['Os'],Result['CharSet'],Result['Server'],Result['Language'],Result['CmsName'],Result['Url']]
                ws.append(dv)
                dv =[]
        if self.report:
            wb.save(filename)

    def RunIt(self):
        """
        入口函数
        """
        self.UrlMakeQueue()
        while not self.Url.empty() :
            self.Result.clear()
            url = self.Url.get()
            self.Result['Url'] = url
            print(Fore.GREEN+'[-] ['+url+']'+u'准备开始扫描...')
            HtHandle = self.GetHtHandle(url)
            if not HtHandle :
                self.Result.clear()
                continue
            # 获取网页编码
            CharSet = self.GetCharSet(HtHandle)
            # 如果获取不到网站编码,默认设置为'utf8'编码,可按需更改
            self.Result['CharSet'] = CharSet if CharSet and CharSet else 'utf-8'
            # 获取服务器类型
            Server = self.GetServer(HtHandle)
            self.Result['Server']   = Server['server']    if Server and Server.has_key('server')       else 'Null'
            self.Result['Os']       = Server['os']        if Server and Server.has_key('os')           else 'Null'
            self.Result['Language'] = Server['lan']       if Server and Server.has_key('lan')          else 'Null'
            # 获取网站编程语言
            Language = self.GetLanguage(HtHandle)
            self.Result['Language'] = Language['lan']     if Language and Language.has_key('lan')      else 'Null'
            self.Result['CmsName']  = Language['CmsName'] if Language and  Language.has_key('CmsName') else False
            if not self.Result['CmsName'] :
                # 在前面的步骤中不存在CMSName,进行指纹扫描。
                self.FingerMakeQueue()
                corlist = [gevent.spawn(self.GetFinger,url) for i in range(self.thread)]
                gevent.joinall(corlist)
                # self.GetFinger(url)
                if not self.Result['CmsName'] :
                    # 本地指纹识别失败，调用网络接口
                    flag = self.GetFingerFromInternet(url)
                    # flag = False
                    if not flag:
                        self.Result['CmsName'] = 'WebCms'
            # 如果获取不到cms框架名称，默认设置为'WebCms',可按需更改
            self.Res.put({'Os':self.Result['Os'],'CharSet':self.Result['CharSet'],'Server':self.Result['Server'],'Language':self.Result['Language'],'CmsName':self.Result['CmsName'],'Url':self.Result['Url']})
            print( Fore.YELLOW +'[+] ['+url+']'+u'识别完成。')
        self.OutputResult()
        self.MakeLog()

if __name__ == "__main__":
    init(autoreset=True)
    arg = Args()
    CMS = CmsInfo(arg.url, arg.thread, filename=arg.file, report=arg.report)
    CMS.RunIt()
    pass
