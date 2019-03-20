#!/usr/bin/env python
# -*- coding:utf-8 -*-

import argparse

def Args():
    '''
    参数设置处理函数
    ARGS.py
    '''
    parse = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,add_help=False,description='''
    *===================================*
    |    Please set the parameters!     |
    |    Author:nw01f                   |
    |    Version:1.0                    |
    |    Time:2019/03/11                |
    *===================================*''')
    parse.add_argument('-f','--file',default=None,help=u'URL类表文件名')
    parse.add_argument('-u','--url',help=u"请设置URL地址")
    parse.add_argument('-t','--thread',default=100,help=u'请设置线程数，默认100',type=int)
    parse.add_argument('-r','--report',default=None,help=u'请设置结果报告文件名，报告为表格形式')
    args = parse.parse_args()
    if args.url is None and args.file is None :
        parse.print_help()
        print(u"△ URL和URL列表文件必须设置其一,请确认URL为网站根目录")
        print(U'''例如:
        python CmsIdentificationV3.py -u http://test.com/
        python CmsIdentificationV3.py -f URL.txt''')
        exit()
    else:
        return args
if __name__ == "__main__":
    arg = Args()
    print arg