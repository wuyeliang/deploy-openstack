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

def function_glance_init():
    if os.path.exists("/etc/openstack_tag/glance.tag"):
        print("/etc/openstack_tag/glance.tag file  exist.")
        logging.error("/etc/openstack_tag/glance.tag file  exist.")
        sys.exit()
    else:
        logging.info("/etc/openstack_tag/glance.tag file does not exist.")
    cf = configparser.ConfigParser()

    cf.read("config/config.ini")  # 读取配置文件，如果写文件的绝对路径，就可以不用os模块
    #获取日志目录
    root_password = cf.get("CONTROLLER", "ALL_PASSWORD") 
    mgmt_ip= cf.get("CONTROLLER", "MANAGER_IP") 
    #创建用户
    libfunc.create_or_check_user("glance", root_password)
    #赋予权限
    runcmd("openstack role add --project service --user glance admin")
    #创建service
    libfunc.check_and_create_service('glance', 'OpenStack Image service', 'image')
    #创建endpoint
    libfunc.check_and_create_endpoint('image', '9292', mgmt_ip,'admin')
    libfunc.check_and_create_endpoint('image', '9292', mgmt_ip, 'internal')
    libfunc.check_and_create_endpoint('image', '9292', mgmt_ip,'public')
    #创建数据库
    connection = pymysql.connect(
        host='localhost',
        user='root',
        passwd=root_password
    )

    try:
        # 创建数据库的游标对象
        cursor = connection.cursor()
        # 执行创建数据库的 SQL 命令
        cursor.execute("CREATE DATABASE IF NOT EXISTS glance")
        logging.info("CREATE DATABASE IF NOT EXISTS glance")
        cursor.execute(f"GRANT ALL PRIVILEGES ON glance.* TO 'glance'@'localhost' IDENTIFIED BY \"{root_password}\";")
        logging.info(f"GRANT ALL PRIVILEGES ON glance.* TO 'glance'@'localhost' IDENTIFIED BY \"{root_password}\";")

        cursor.execute(f"grant all privileges on glance.* to glance@'%' identified by \"{root_password}\";")
        logging.info(f"GRANT ALL PRIVILEGES ON glance.* TO 'glance'@'localhost' IDENTIFIED BY \"{root_password}\";")

    # 刷新权限
        cursor.execute("FLUSH PRIVILEGES")
        # 提交事务
        connection.commit()
        # 输出成功信息
        logging.info("成功创建数据库 glance")
    except pymysql.Error as error:
        # 输出错误信息
        logging.error("创建数据库时出错：", error)
        sys.exit(1)
    finally:
        # 关闭游标和数据库连接
        cursor.close()
        connection.close()
    runcmd("apt -y install glance")
    with open("/etc/glance/glance-api.conf", "w") as file:
        # 多行文本
        text = """[DEFAULT]
bind_host = 127.0.0.1
transport_url = rabbit://openstack:Changeme_123@179.20.3.81

[glance_store]
stores = file,http
default_store = file
filesystem_store_datadir = /var/lib/glance/images/

[database]
connection = mysql+pymysql://glance:Changeme_123@179.20.3.81/glance

[keystone_authtoken]
www_authenticate_uri = http://179.20.3.81:5000
auth_url = http://179.20.3.81:5000
memcached_servers = 179.20.3.81:11211
auth_type = password
project_domain_name = default
user_domain_name = default
project_name = service
username = glance
password = Changeme_123
insecure = true

[paste_deploy]
flavor = keystone

[oslo_policy]
enforce_new_defaults = true"""


        # 写入文件
        file.write(text)
        logging.info("create /etc/glance/glance-api.conf")
    runcmd('sed -i "s/179.20.3.81/%s/g" /etc/glance/glance-api.conf' % mgmt_ip) 
    runcmd('sed -i "s/Changeme_123/%s/g" /etc/glance/glance-api.conf' % root_password)   

    runcmd('su -s /bin/bash glance -c "glance-manage db_sync"')
    runcmd("systemctl restart glance-api")
    runcmd("systemctl enable glance-api")
    with open("/etc/nginx/nginx.conf", "w") as file:
        # 多行文本
        text = """user www-data;
worker_processes auto;
pid /run/nginx.pid;
include /etc/nginx/modules-enabled/*.conf;
events {
        worker_connections 768;
}
http {
        sendfile on;
        tcp_nopush on;
        types_hash_max_size 2048;
        include /etc/nginx/mime.types;
        default_type application/octet-stream;
        ssl_prefer_server_ciphers on;
        access_log /var/log/nginx/access.log;
        error_log /var/log/nginx/error.log;
        gzip on;
        include /etc/nginx/conf.d/*.conf;
        include /etc/nginx/sites-enabled/*;
}
stream {
    upstream glance-api {
        server 127.0.0.1:9292;
    }
    server {
        listen 179.20.3.81:9292 ;
        proxy_pass glance-api;
    }
    upstream nova-api {
        server 127.0.0.1:8774;
    }
    server {
        listen 179.20.3.81:8774 ;
        proxy_pass nova-api;
    }
    upstream nova-metadata-api {
        server 127.0.0.1:8775;
    }
    server {
        listen 179.20.3.81:8775 ;
        proxy_pass nova-metadata-api;
    }
    upstream placement-api {
        server 127.0.0.1:8778;
    }
    server {
        listen 179.20.3.81:8778 ;
        proxy_pass placement-api;
    }
    upstream novncproxy {
        server 127.0.0.1:6080;
    }
    server {
        listen 179.20.3.81:6080 ;
        proxy_pass novncproxy;
    }
        upstream neutron-api {
        server 127.0.0.1:9696;
    }
    server {
        listen 179.20.3.81:9696 ;
        proxy_pass neutron-api;
    }
        upstream cinder-api {
        server 127.0.0.1:8776;
    }
    server {
        listen 179.20.3.81:8776 ;
        proxy_pass cinder-api;
    }
}"""


        # 写入文件
        file.write(text)
        logging.info("create /etc/nginx/nginx.conf")
    runcmd('sed -i "s/179.20.3.81/%s/g" /etc/nginx/nginx.conf' % mgmt_ip) 
    runcmd('sed -i "s/Changeme_123/%s/g" /etc/nginx/nginx.conf' % root_password)  
    runcmd('systemctl restart nginx')
    runcmd('openstack image list')
    runcmd("echo `date` > /etc/openstack_tag/glance.tag")
    print("\033[32m ############################### \033[0m")
    print("\033[32m glance installation completed. \033[0m")
    print("\033[32m ############################### \033[0m")
    logging.info("glance installation completed.")
