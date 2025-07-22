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

def function_base_init():

    if os.path.exists("/etc/openstack_tag/db_mq.tag"):
        print("/etc/openstack_tag/db_mq.tag file  exist.")
        logging.error("/etc/openstack_tag/db_mq.tag file exist.")
        sys.exit()
    else:
        logging.info("/etc/openstack_tag/db_mq.tag file does not exist.")



#function_base_init
def function_db_mq_init():
    function_base_init()
    # 指定配置文件的路径
    config_file = '/etc/my.cnf.d/openstack.cnf'

    # 检查配置文件是否存在
    if os.path.exists(config_file):
        # 删除配置文件
        os.remove(config_file)
        logging.info("delete /etc/my.cnf.d/openstack.cnf")
    else:
        runcmd("cat config/openstack.cnf >/etc/mysql/mariadb.conf.d/50-server.cnf ")
    cf = configparser.ConfigParser()

    cf.read("config/config.ini")
    root_password = cf.get("CONTROLLER", "ALL_PASSWORD") 
    # 配置 `mysql_secure_installation` 的命令
    command = f"mysql_secure_installation << EOF\n" \
              f"\n" \
              f"n\n" \
              f"y\n" \
              f"{root_password}\n" \
              f"{root_password}\n" \
              f"y\n" \
              f"n\n" \
              f"y\n" \
              f"EOF"

    # 运行命令并捕获输出和错误信息
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error = process.communicate()

    if process.returncode == 0:
        print("MySQL 安全配置已完成。")
    else:
        print(f"安全配置失败：{error.decode('utf-8')}")




#设置源
    runcmd("apt -y install software-properties-common")
    runcmd("add-apt-repository cloud-archive:Epoxy")
    runcmd("apt update")
    runcmd("apt -y upgrade")
#安装mq
    runcmd("apt -y install rabbitmq-server memcached python3-pymysql nginx libnginx-mod-stream")


    command = "rabbitmqctl list_users"
    output = subprocess.check_output(command, shell=True).decode()
    username = "openstack"
    user_exists = username in output
    cf = configparser.ConfigParser()

    cf.read("config/config.ini")
    root_password = cf.get("CONTROLLER", "ALL_PASSWORD") 
    mgmt_ip= cf.get("CONTROLLER", "MANAGER_IP") 
    if not user_exists:
        runcmd(f"rabbitmqctl add_user {username} {root_password}")
        runcmd('rabbitmqctl set_permissions openstack ".*" ".*" ".*"')
    runcmd('sed -i "s/127.0.0.1/%s/g" /etc/memcached.conf'% mgmt_ip) 

    runcmd("unlink /etc/nginx/sites-enabled/default || echo 1") 
    runcmd("systemctl restart mariadb rabbitmq-server memcached nginx") 

    runcmd("echo `date` > /etc/openstack_tag/db_mq.tag")
    print("\033[32m Database and message queue installation completed. \033[0m")
    logging.info("Database and message queue installation completed.")
    print("\033[32m ################################################### \033[0m")
    print("\033[32m Database and message queue installation completed. \033[0m")
    print("\033[32m ################################################### \033[0m")
