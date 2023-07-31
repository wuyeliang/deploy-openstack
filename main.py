#!/usr/bin/python3
# -*- coding: utf-8 -*-
# vi: set autoindent ts=4 expandtab :
import time
import subprocess
import logging
#获取配置文件
import configparser
#获取当前用户模块
import getpass
import sys
import os
'''
# 添加 main.py 的父目录到模块搜索路径中
root_directory = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(root_directory))

# 导入目标模块
import script.sys_init
'''
from script import sys_init
from script import db_mq_init
from script import keystone_init
from script import glance_init
from script import nova_init
from script import cinder_init
from script import neutron_init
from script import horizon_init

cf = configparser.ConfigParser()
cf.read("config/config.ini")  # 读取配置文件，如果写文件的绝对路径，就可以不用os模块
#获取日志目录
log_dir = cf.get("LOG", "LOG_DIR")  

#定义日志打印
logging.basicConfig(level=logging.DEBUG,  
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',  
                    datefmt='%a-%d-%b %Y %H:%M:%S',  
                    filename=log_dir,  
                    filemode='a')  

#定义执行函数，执行成功打日志，失败打error。
def runcmd(command):
    ret = subprocess.run(command,shell=True,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,encoding="utf-8")
    #ret =  subprocess.getoutput('command')
    for line in ret.stdout:
        print(line, end='')    
    if ret.returncode == 0:
        print("\033[32m %s success \033[0m" % command)
        logging.info("%s success" % command)
    else:
        print("\033[41;37m %s failed \033[0m" % command)
        logging.error("%s failed" % command)
        sys.exit(1)
#样例



def function_print_main():
    print('''
    1) Configure System Environment.
    2) Install Mariadb and Rabbitmq-server.
    3) Install Keystone.
    4) Install Glance.
    5) Install Nova.
    6) Install Cinder.
    7) Install Neutron.
    8) Install Dashboard.
    0) Quit
        ''')
    num = float(input("请输入一个数字："))

    # 比较数字的大小
    if num == 1:
        sys_init.function_base_init() 
    elif num == 2:
        db_mq_init.function_db_mq_init()
        function_print_main()
    elif num == 0:
        sys.exit(0)
    elif num == 3:
        keystone_init.function_keystone_init()
        function_print_main()
    elif num == 4:
        glance_init.function_glance_init()
        function_print_main()
    elif num == 5:
        nova_init.function_nova_init()
        function_print_main()
    elif num == 6:
        cinder_init.function_cinder_init()
        function_print_main()
    elif num == 7:
        neutron_init.function_neutron_init()
        function_print_main()
    elif num == 8:
        horizon_init.function_horizon_init()
        function_print_main()
    else:
        print("请输入正确的数字!")
        function_print_main()

if __name__ == "__main__":
    function_print_main()