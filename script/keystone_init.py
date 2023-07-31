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

def function_keystone_init():
    if os.path.exists("/etc/openstack_tag/keystone.tag"):
        print("/etc/openstack_tag/keystone.tag file  exist.")
        logging.error("/etc/openstack_tag/keystone.tag file  exist.")
        sys.exit()
    else:
        logging.info("/etc/openstack_tag/keystone.tag file does not exist.")

    cf = configparser.ConfigParser()

    cf.read("config/config.ini")  # 读取配置文件，如果写文件的绝对路径，就可以不用os模块
    #获取日志目录
    root_password = cf.get("CONTROLLER", "ALL_PASSWORD") 
    mgmt_ip= cf.get("CONTROLLER", "MANAGER_IP") 
    connection = pymysql.connect(
        host='localhost',
        user='root',
        passwd=root_password
    )

    try:
        # 创建数据库的游标对象
        cursor = connection.cursor()
        # 执行创建数据库的 SQL 命令
        cursor.execute("CREATE DATABASE IF NOT EXISTS keystone")
        logging.info("CREATE DATABASE IF NOT EXISTS keystone")
        cursor.execute(f"GRANT ALL PRIVILEGES ON keystone.* TO 'keystone'@'localhost' IDENTIFIED BY \"{root_password}\";")
        logging.info(f"GRANT ALL PRIVILEGES ON keystone.* TO 'keystone'@'localhost' IDENTIFIED BY \"{root_password}\";")

        cursor.execute(f"grant all privileges on keystone.* to keystone@'%' identified by \"{root_password}\";")
        logging.info(f"GRANT ALL PRIVILEGES ON keystone.* TO 'keystone'@'localhost' IDENTIFIED BY \"{root_password}\";")

    # 刷新权限
        cursor.execute("FLUSH PRIVILEGES")
        # 提交事务
        connection.commit()
        # 输出成功信息
        logging.info("成功创建数据库 keystone")
    except pymysql.Error as error:
        # 输出错误信息
        logging.error("创建数据库时出错：", error)
        sys.exit(1)
    finally:
        # 关闭游标和数据库连接
        cursor.close()
        connection.close()
    runcmd("apt -y install keystone python3-openstackclient apache2 libapache2-mod-wsgi-py3 python3-oauth2client")
    with open("/etc/keystone/keystone.conf", "w") as file:
        # 多行文本
        text = """[DEFAULT]
log_dir = /var/log/keystone
[application_credential]
[assignment]
[auth]
[cache]
memcache_servers = 179.20.3.81:11211
[catalog]
[cors]
[credential]
[database]
connection = sqlite:////var/lib/keystone/keystone.db
connection = mysql+pymysql://keystone:Changeme_123@179.20.3.81/keystone
[domain_config]
[endpoint_filter]
[endpoint_policy]
[eventlet_server]
[extra_headers]
Distribution = Ubuntu
[federation]
[fernet_receipts]
[fernet_tokens]
[healthcheck]
[identity]
[identity_mapping]
[jwt_tokens]
[ldap]
[memcache]
[oauth1]
[oauth2]
[oslo_messaging_amqp]
[oslo_messaging_kafka]
[oslo_messaging_notifications]
[oslo_messaging_rabbit]
[oslo_middleware]
[oslo_policy]
[policy]
[profiler]
[receipt]
provider = fernet
[resource]
[revoke]
[role]
[saml]
[security_compliance]
[shadow_users]
[token]
[tokenless_auth]
[totp]
[trust]
[unified_limit]
[wsgi]"""


        # 写入文件
        file.write(text)
        logging.info("create /etc/keystone/keystone.conf")
    runcmd('sed -i "s/179.20.3.81/%s/g" /etc/keystone/keystone.conf' % mgmt_ip) 
    runcmd('sed -i "s/Changeme_123/%s/g" /etc/keystone/keystone.conf' % root_password)    
    runcmd('su -s /bin/bash keystone -c "keystone-manage db_sync"')
    runcmd('keystone-manage fernet_setup --keystone-user keystone --keystone-group keystone')
    runcmd('keystone-manage credential_setup --keystone-user keystone --keystone-group keystone')
    runcmd("keystone-manage bootstrap --bootstrap-password %s \
    --bootstrap-admin-url http://%s:5000/v3/ \
    --bootstrap-internal-url http://%s:5000/v3/ \
    --bootstrap-public-url http://%s:5000/v3/ \
    --bootstrap-region-id RegionOne" % (root_password,mgmt_ip,mgmt_ip,mgmt_ip))
    #创建环境变量
    with open("/root/keystonerc", "w") as file:
        # 多行文本
        text = f"""export OS_PROJECT_DOMAIN_NAME=default
    export OS_USER_DOMAIN_NAME=default
    export OS_PROJECT_NAME=admin
    export OS_USERNAME=admin
    export OS_PASSWORD={root_password}
    export OS_AUTH_URL=http://{mgmt_ip}:5000/v3
    export OS_IDENTITY_API_VERSION=3
    export OS_IMAGE_API_VERSION=2
    export OS_VOLUME_API_VERSION=3"""

        # 写入文件
        file.write(text)
        logging.info("create /root/keystonerc")

    runcmd("bash /etc/profile")
    #创建service项目
    project_name = "service"
    description = "Service Project"
    libfunc.check_or_create_project(project_name, description)
    runcmd("openstack project list")
    runcmd("echo `date` > /etc/openstack_tag/keystone.tag")
    print("\033[32m ############################### \033[0m")
    print("\033[32m keystone installation completed. \033[0m")
    print("\033[32m ############################### \033[0m")
    logging.info("Keystone installation completed.")