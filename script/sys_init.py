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
    for line in ret.stdout:
        print(line, end='')    
    if ret.returncode == 0:
        print("\033[32m %s success \033[0m" % command)
        logging.info("%s success" % command)
    else:
        print("\033[41;37m %s failed \033[0m" % command)
        logging.error("%s failed" % command)
        sys.exit(1)

#function_base_init
def function_base_init():

    if os.path.exists("/etc/openstack_tag/system.tag"):
        print("/etc/openstack_tag/system.tag file exist.")
        logging.error("/etc/openstack_tag/system.tag file exist.")
        sys.exit()
    else:
        logging.info("/etc/openstack_tag/system.tag file does not exist.")

    if os.path.exists("/etc/openstack_tag"):
        logging.info("/etc/openstack_tag dir exist, continue executing the program ")
    else:
        runcmd("mkdir -p /etc/openstack_tag ")

    current_time=time.strftime('%Y%m%d%H%M%S')
    runcmd("mv  /etc/apt/sources.list /etc/apt/sources.list_bak_%s" % current_time)

    with open("/etc/apt/sources.list", "w") as file:
        # 多行文本
        text = """deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ jammy main restricted universe multiverse
    # deb-src https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ jammy main restricted universe multiverse
    deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ jammy-updates main restricted universe multiverse
    # deb-src https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ jammy-updates main restricted universe multiverse
    deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ jammy-backports main restricted universe multiverse
    # deb-src https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ jammy-backports main restricted universe multiverse

    # deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ jammy-security main restricted universe multiverse
    # # deb-src https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ jammy-security main restricted universe multiverse

    deb http://security.ubuntu.com/ubuntu/ jammy-security main restricted universe multiverse
    # deb-src http://security.ubuntu.com/ubuntu/ jammy-security main restricted universe multiverse"""

        # 写入文件
        file.write(text)
        logging.info("create /etc/apt/sources.list")
    #获取配置文件中定义的本机名，并修改主机名
    cf = configparser.ConfigParser()
    cf.read("config/config.ini")  # 读取配置文件，如果写文件的绝对路径，就可以不用os模块
    #获取日志目录
    LOCAL_HOSTNAME = cf.get("CONTROLLER", "HOST_NAME")  
    runcmd("hostnamectl set-hostname %s" % LOCAL_HOSTNAME )
    runcmd("apt update && apt upgrade -y" )
    runcmd("apt install python3-pymysql -y")
    runcmd("apt -y install mariadb-server" )
    runcmd('echo "source ~/keystonerc " >> ~/.bashrc')
    runcmd("cat ./config/hosts > /etc/hosts")
    runcmd("echo `date` > /etc/openstack_tag/system.tag")
    print("\033[41;37m begin to reboot system to enforce kernel \033[0m")
    runcmd("reboot" )
