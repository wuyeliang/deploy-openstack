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

def function_cinder_init():
    if os.path.exists("/etc/openstack_tag/cinder.tag"):
        print("/etc/openstack_tag/cinder.tag file  exist.")
        logging.error("/etc/openstack_tag/cinder.tag file  exist.")
        sys.exit()
    else:
        logging.info("/etc/openstack_tag/cinder.tag file does not exist.")
    cf = configparser.ConfigParser()

    cf.read("config/config.ini")  # 读取配置文件，如果写文件的绝对路径，就可以不用os模块
    #获取日志目录
    root_password = cf.get("CONTROLLER", "ALL_PASSWORD") 
    mgmt_ip= cf.get("CONTROLLER", "MANAGER_IP") 
    cinder_disk= cf.get("VOLUME", "CINDER_DISK")

    #创建用户
    libfunc.create_or_check_user("cinder", root_password)
    #赋予权限
    runcmd("openstack role add --project service --user cinder admin")

 
    #创建service
    libfunc.check_and_create_service('cinderv3', 'OpenStack Block Storage', 'volumev3')


    #创建endpoint
    libfunc.check_and_create_endpoint_v3('volumev3', '8776', mgmt_ip, 'admin')
    libfunc.check_and_create_endpoint_v3('volumev3', '8776', mgmt_ip, 'internal')
    libfunc.check_and_create_endpoint_v3('volumev3', '8776', mgmt_ip, 'public')


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
        cursor.execute("CREATE DATABASE IF NOT EXISTS cinder")
        logging.info("CREATE DATABASE IF NOT EXISTS cinder")


        cursor.execute(f"GRANT ALL PRIVILEGES ON cinder.* TO 'cinder'@'localhost' IDENTIFIED BY \"{root_password}\";")
        logging.info(f"GRANT ALL PRIVILEGES ON cinder.* TO 'cinder'@'localhost' IDENTIFIED BY \"{root_password}\";")
        cursor.execute(f"grant all privileges on cinder.* to cinder@'%' identified by \"{root_password}\";")
        logging.info(f"GRANT ALL PRIVILEGES ON cinder.* TO 'cinder'@'localhost' IDENTIFIED BY \"{root_password}\";")

        
    # 刷新权限
        cursor.execute("FLUSH PRIVILEGES")
        # 提交事务
        connection.commit()
        # 输出成功信息
        logging.info("成功创建数据库 neutron_ml2")
    except pymysql.Error as error:
        # 输出错误信息
        logging.error("创建数据库时出错：", error)
        sys.exit(1)
    finally:
        # 关闭游标和数据库连接
        cursor.close()
        connection.close()
    runcmd("apt -y install cinder-api cinder-scheduler python3-cinderclient cinder-volume python3-mysqldb")
    with open("/etc/cinder/cinder.conf", "w") as file:
        # 多行文本
        text = """[DEFAULT]
my_ip = 179.20.3.81
glance_api_servers = http://179.20.3.81:9292
enabled_backends = lvm
rootwrap_config = /etc/cinder/rootwrap.conf
api_paste_confg = /etc/cinder/api-paste.ini
state_path = /var/lib/cinder
auth_strategy = keystone
transport_url = rabbit://openstack:Changeme_123@179.20.3.81
enable_v3_api = True

# MariaDB connection info
[database]
connection = mysql+pymysql://cinder:Changeme_123@179.20.3.81/cinder

# Keystone auth info
[keystone_authtoken]
www_authenticate_uri = http://179.20.3.81:5000
auth_url = http://179.20.3.81:5000
memcached_servers = 179.20.3.81:11211
auth_type = password
project_domain_name = default
user_domain_name = default
project_name = service
username = cinder
password = Changeme_123
insecure = true

[oslo_concurrency]
lock_path = $state_path/tmp

[oslo_policy]
enforce_new_defaults = true
[lvm]
target_helper = lioadm
target_protocol = iscsi
target_ip_address = $my_ip
volume_group = vg_volume01
volume_driver = cinder.volume.drivers.lvm.LVMVolumeDriver
volumes_dir = $state_path/volumes"""


        # 写入文件
        file.write(text)
        logging.info("create /etc/cinder/cinder.conf")

    runcmd("cat config/cinder-wsgi.conf >/etc/apache2/conf-available/cinder-wsgi.conf")
    runcmd('sed -i "s/179.20.3.81/%s/g" /etc/cinder/cinder.conf' % mgmt_ip) 
    runcmd('sed -i "s/Changeme_123/%s/g" /etc/cinder/cinder.conf' % root_password) 
    query_command = "vgs  | grep vg_volume01 >/dev/null"
    result = subprocess.run(query_command, shell=True)
    # 判断查询结果
    if result.returncode == 0:
        logging.info("vg_volume01 already exists.")
    else:
        # 获取service项目ID
        runcmd(f"vgcreate vg_volume01 {cinder_disk}")
    runcmd('su -s /bin/bash cinder -c "cinder-manage db sync"')
    runcmd("systemctl restart cinder-scheduler apache2 nginx cinder-volume  ")
    runcmd("systemctl enable cinder-scheduler cinder-volume")
    runcmd("openstack volume service list")
    runcmd("echo `date` > /etc/openstack_tag/cinder.tag")
    print("\033[32m ############################### \033[0m")
    print("\033[32m cinder installation completed. \033[0m")
    print("\033[32m ############################### \033[0m")
    logging.info("cinder installation completed.")