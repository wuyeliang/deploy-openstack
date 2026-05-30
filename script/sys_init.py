#!/usr/bin/python3
# -*- coding: utf-8 -*-
# vi: set autoindent ts=4 expandtab :
import os
import subprocess
import sys
import time

from script.lib.runtime import get_config
from script.lib.runtime import get_logger
from script.lib.runtime import run_command


cf = get_config()
logger = get_logger(__name__)


def get_os_codename():
    result = subprocess.run(
        "source /etc/os-release && echo ${VERSION_CODENAME}",
        shell=True,
        capture_output=True,
        text=True,
        executable="/bin/bash",
    )
    codename = result.stdout.strip()
    return codename or "noble"

#function_base_init
def function_base_init():

    if os.path.exists("/etc/openstack_tag/system.tag"):
        print("/etc/openstack_tag/system.tag file exist.")
        logger.error("/etc/openstack_tag/system.tag file exist.")
        sys.exit()
    else:
        logger.info("/etc/openstack_tag/system.tag file does not exist.")

    if os.path.exists("/etc/openstack_tag"):
        logger.info("/etc/openstack_tag dir exist, continue executing the program ")
    else:
        run_command("mkdir -p /etc/openstack_tag ", logger=logger)

    current_time=time.strftime('%Y%m%d%H%M%S')
    run_command("mv  /etc/apt/sources.list /etc/apt/sources.list_bak_%s" % current_time, logger=logger)

    with open("/etc/apt/sources.list", "w") as file:
        codename = get_os_codename()
        # 多行文本
        mirror = "http://mirrors.aliyun.com/ubuntu/"
        text = f"""deb {mirror} {codename} main restricted universe multiverse
    # deb-src {mirror} {codename} main restricted universe multiverse
    deb {mirror} {codename}-updates main restricted universe multiverse
    # deb-src {mirror} {codename}-updates main restricted universe multiverse
    deb {mirror} {codename}-backports main restricted universe multiverse
    # deb-src {mirror} {codename}-backports main restricted universe multiverse

    deb {mirror} {codename}-security main restricted universe multiverse
    # deb-src {mirror} {codename}-security main restricted universe multiverse"""

        # 写入文件
        file.write(text)
        logger.info("create /etc/apt/sources.list")
    #获取配置文件中定义的本机名，并修改主机名
    LOCAL_HOSTNAME = cf.get("CONTROLLER", "HOST_NAME")  
    run_command("hostnamectl set-hostname %s" % LOCAL_HOSTNAME, logger=logger)
    run_command("apt update", logger=logger)
    run_command("apt install python3-pymysql -y", logger=logger)
    run_command("apt -y install mariadb-server", logger=logger)
    run_command('echo "source ~/keystonerc " >> ~/.bashrc', logger=logger)
    run_command("cat ./config/hosts > /etc/hosts", logger=logger)
    run_command("echo `date` > /etc/openstack_tag/system.tag", logger=logger)
    if os.path.exists("/var/run/reboot-required"):
        print("\033[41;37m begin to reboot system to enforce kernel \033[0m")
        run_command("reboot", logger=logger)
