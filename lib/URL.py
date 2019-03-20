#!/usr/bin/env python
# -*- coding:utf-8 -*-

import urlparse

DEFAULT_ENCODING = "utf8"

class URL():
    '''
    封装URL处理类
    URL.py
    '''
    def __init__(self, url,encoding=DEFAULT_ENCODING):
        self._unicode_url = None
        self._change      = False
        self._encoding    = encoding
        if not url.startswith('https://') and not url.startswith('http://') :
            # 默认设置为http协议
            url = 'http://' + url
        urlres = urlparse.urlparse(url)
        self.scheme = urlres.scheme
        if urlres.port is None  :
            self.port = 80
        else :
            self.port = urlres.port
        if urlres.netloc.find(':') > -1 :
            self.netloc = urlres.netloc
        else:
            self.netloc = urlres.netloc + ':' + str(self.port)
        self.path       = urlres.path
        self.params     = urlres.params
        self.qs         = urlres.query
        self.fragment   = urlres.fragment   ## 锚点

    def get_schema(self):
        """
        获取url中的协议
        """
        print self.scheme
        return self.scheme

    def get_domain(self):
        """
        # 获取url中的域名
        """
        return self.netloc.split(':')[0]

    def get_host(self):
        """
        获取url中的主机名
        """
        return self.netloc.split(':')[0]

    def get_port(self):
        """
        获取url中的端口
        """
        return self.port


    def get_path(self):
        """
        获取url中的路径
        """
        return self.path

    def get_filename(self):
        """
        获取url中的文件名
        """
        return self.path[self.path.rfind('/')+1:]

    def get_ext(self):
        """
        获取url中的扩展名
        """
        fname = self.get_filename()
        ext = fname[fname.rfind('.')+1:]
        if ext == fname :
            return ''
        else:
            return ext

    
    def get_query(self):
        """
        获取url中的参数
        """
        return self.qs

    def get_fragment(self):
        """
        获取url中的锚点
        """
        return self.fragment

    
    @property
    def url_string(self):
        """
        组合url_string 属性
        """
        data = (self.scheme,self.netloc,self.path,self.params,self.qs,self.fragment)
        dataurl = urlparse.urlunparse(data)
        # 解决url中出现特殊字符回显乱码的问题，如中文
        try:
            calc = unicode(dataurl)
        except UnicodeDecodeError :
            calc = unicode(dataurl,self._encoding,'replace')
        return calc

    def get_url_string(self):
        """
        获取url所对应的完整字符串
        """
        return self.url_string

    def is_ip_address(self, address):
        """
        判断是否是IP类域名
        """
        parts = address.split(".")
        if len(parts) != 4 :
            return False
        for i in parts:
            try:
                if not 0 <= int(i) <=255 :
                    return False
            except:
                return False
        return True

    def __str__(self):
        return "%s" %(self.url_string)
    
    def __repr__(self):
        return '<URL for "%s">' %(self.url_string)


if __name__ == "__main__":
    url1 = 'https://www.seebug.org/vuldb/ssvid-97825/'
    url = URL(url1)
    print url.get_url_string()