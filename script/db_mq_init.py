#!/usr/bin/python3
# -*- coding: utf-8 -*-
# vi: set autoindent ts=4 expandtab :
import os
import subprocess
import sys

from script.lib.runtime import get_config
from script.lib.runtime import get_logger
from script.lib.runtime import run_command


cf = get_config()
logger = get_logger(__name__)

def function_base_init():

    if os.path.exists("/etc/openstack_tag/db_mq.tag"):
        print("/etc/openstack_tag/db_mq.tag file  exist.")
        logger.error("/etc/openstack_tag/db_mq.tag file exist.")
        sys.exit()
    else:
        logger.info("/etc/openstack_tag/db_mq.tag file does not exist.")



#function_base_init
def function_db_mq_init():
    function_base_init()
    # 指定配置文件的路径
    config_file = '/etc/my.cnf.d/openstack.cnf'

    # 检查配置文件是否存在
    if os.path.exists(config_file):
        # 删除配置文件
        os.remove(config_file)
        logger.info("delete /etc/my.cnf.d/openstack.cnf")
    else:
        run_command("cat config/openstack.cnf >/etc/mysql/mariadb.conf.d/50-server.cnf ", logger=logger)
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
    run_command("apt -y install software-properties-common", logger=logger)
    run_command("add-apt-repository cloud-archive:Epoxy", logger=logger)
    run_command("apt update", logger=logger)
    run_command("apt -y upgrade", logger=logger)
#安装mq
    run_command("apt -y install rabbitmq-server memcached python3-pymysql nginx libnginx-mod-stream", logger=logger)


    command = "rabbitmqctl list_users"
    output = subprocess.check_output(command, shell=True).decode()
    username = "openstack"
    user_exists = username in output
    root_password = cf.get("CONTROLLER", "ALL_PASSWORD") 
    mgmt_ip= cf.get("CONTROLLER", "MANAGER_IP") 
    if not user_exists:
        run_command(f"rabbitmqctl add_user {username} {root_password}", logger=logger)
        run_command('rabbitmqctl set_permissions openstack ".*" ".*" ".*"', logger=logger)
    run_command('sed -i "s/127.0.0.1/%s/g" /etc/memcached.conf'% mgmt_ip, logger=logger) 

    run_command("unlink /etc/nginx/sites-enabled/default || echo 1", logger=logger) 
    run_command("systemctl restart mariadb rabbitmq-server memcached nginx", logger=logger) 

    run_command("echo `date` > /etc/openstack_tag/db_mq.tag", logger=logger)
    print("\033[32m Database and message queue installation completed. \033[0m")
    logger.info("Database and message queue installation completed.")
    print("\033[32m ################################################### \033[0m")
    print("\033[32m Database and message queue installation completed. \033[0m")
    print("\033[32m ################################################### \033[0m")
