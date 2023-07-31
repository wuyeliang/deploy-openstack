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
import pymysql


#导入项目创建模块
from script.lib import libfunc
#定义日志打印
cf = configparser.ConfigParser()

cf.read("config/config.ini")  # 读取配置文件，如果写文件的绝对路径，就可以不用os模块
#获取日志目录
log_dir = cf.get("LOG", "LOG_DIR") 
logging.basicConfig(level=logging.DEBUG,  
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',  
                    datefmt='%a-%d-%b %Y %H:%M:%S',  
                    filename=log_dir,  
                    filemode='a')  

#定义执行函数，执行成功打日志，失败打error。
def runcmd(command):
    ret = subprocess.run(command,shell=True,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,encoding="utf-8")
    #ret =  subprocess.getoutput('command')
    # 逐行读取输出并打印
    for line in ret.stdout:
        print(line, end='')

    if ret.returncode == 0:
        print("\033[32m %s success \033[0m" % command)
        logging.info("%s success" % command)
    else:
        print("\033[41;37m %s failed \033[0m" % command)
        logging.error("%s failed" % command)
        sys.exit(1)

def function_horizon_init():
    if os.path.exists("/etc/openstack_tag/horizon.tag"):
        print("/etc/openstack_tag/horizon.tag file  exist.")
        logging.error("/etc/openstack_tag/horizon.tag file  exist.")
        sys.exit()
    else:
        logging.info("/etc/openstack_tag/horizon.tag file does not exist.")
    cf = configparser.ConfigParser()

    cf.read("config/config.ini")  # 读取配置文件，如果写文件的绝对路径，就可以不用os模块
    #获取日志目录
    root_password = cf.get("CONTROLLER", "ALL_PASSWORD") 
    mgmt_ip= cf.get("CONTROLLER", "MANAGER_IP") 
    runcmd("apt -y install openstack-dashboard")
    runcmd("cat config/local_settings.py > /etc/openstack-dashboard/local_settings.py")
    runcmd('sed -i "s/179.20.3.81/%s/g" /etc/openstack-dashboard/local_settings.py' % mgmt_ip) 
    runcmd('sed -i "s/Changeme_123/%s/g" /etc/openstack-dashboard/local_settings.py' % root_password)  
    runcmd("systemctl restart apache2 nova-api")
    runcmd('su -s /bin/bash nova -c "nova-manage cell_v2 discover_hosts"')
    runcmd("echo `date` > /etc/openstack_tag/horizon.tag")

    print("\033[32m ############################### \033[0m")
    print("\033[32m horizon installation completed. \033[0m")
    print("\033[32m ############################### \033[0m")
    logging.info("horizon installation completed.")