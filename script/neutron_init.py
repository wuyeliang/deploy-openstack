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

def function_neutron_init():
    if os.path.exists("/etc/openstack_tag/neutron.tag"):
        logging.error("/etc/openstack_tag/neutron.tag file  exist.")
        print("/etc/openstack_tag/neutron.tag file  exist.")
        sys.exit()
    else:
        logging.info("/etc/openstack_tag/neutron.tag file does not exist.")
    cf = configparser.ConfigParser()

    cf.read("config/config.ini")  # 读取配置文件，如果写文件的绝对路径，就可以不用os模块
    #获取日志目录
    root_password = cf.get("CONTROLLER", "ALL_PASSWORD") 
    mgmt_ip= cf.get("CONTROLLER", "MANAGER_IP") 
    NIC_NAME= cf.get("CONTROLLER", "NET_DEVICE_NAME") 
    subnet= cf.get("FLOATING_METWORK_ADDR", "NEUTRON_PUBLIC_NET")
    subgw= cf.get("FLOATING_METWORK_ADDR", "PUBLIC_NET_GW")
    subdns= cf.get("FLOATING_METWORK_ADDR", "NEUTRON_DNS")

    #创建用户
    libfunc.create_or_check_user("neutron", root_password)
    #赋予权限
    runcmd("openstack role add --project service --user neutron admin")

 
    #创建service
    libfunc.check_and_create_service('neutron', 'OpenStack Networking service', 'network')


    #创建endpoint
    libfunc.check_and_create_endpoint('network', '9696', mgmt_ip, 'admin')
    libfunc.check_and_create_endpoint('network', '9696', mgmt_ip, 'internal')
    libfunc.check_and_create_endpoint('network', '9696', mgmt_ip, 'public')


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
        cursor.execute("CREATE DATABASE IF NOT EXISTS neutron_ml2")
        logging.info("CREATE DATABASE IF NOT EXISTS neutron_ml2")


        cursor.execute(f"GRANT ALL PRIVILEGES ON neutron_ml2.* TO 'neutron'@'localhost' IDENTIFIED BY \"{root_password}\";")
        logging.info(f"GRANT ALL PRIVILEGES ON neutron_ml2.* TO 'neutron'@'localhost' IDENTIFIED BY \"{root_password}\";")
        cursor.execute(f"grant all privileges on neutron_ml2.* to neutron@'%' identified by \"{root_password}\";")
        logging.info(f"GRANT ALL PRIVILEGES ON neutron_ml2.* TO 'neutron'@'localhost' IDENTIFIED BY \"{root_password}\";")

        
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
    runcmd("apt -y install neutron-server neutron-metadata-agent neutron-plugin-ml2 python3-neutronclient")
    with open("/etc/neutron/neutron.conf", "w") as file:
        # 多行文本
        text = """[DEFAULT]
api_workers = 2
rpc_workers = 2
rpc_thread_pool_size = 1000
bind_host = 127.0.0.1
bind_port = 9696
core_plugin = ml2
service_plugins = router
auth_strategy = keystone
state_path = /var/lib/neutron
dhcp_agent_notification = True
allow_overlapping_ips = True
notify_nova_on_port_status_changes = True
notify_nova_on_port_data_changes = True
# RabbitMQ connection info
transport_url = rabbit://openstack:Changeme_123@179.20.3.81

[agent]
root_helper = sudo /usr/bin/neutron-rootwrap /etc/neutron/rootwrap.conf

# Keystone auth info
[keystone_authtoken]
www_authenticate_uri = http://179.20.3.81:5000
auth_url = http://179.20.3.81:5000
memcached_servers = 179.20.3.81:11211
auth_type = password
project_domain_name = default
user_domain_name = default
project_name = service
username = neutron
password = Changeme_123
# if using self-signed certs on Apache2 Keystone, turn to [true]
insecure = false

# MariaDB connection info
[database]
connection = mysql+pymysql://neutron:Changeme_123@179.20.3.81/neutron_ml2

# Nova auth info
[nova]
auth_url = http://179.20.3.81:5000
auth_type = password
project_domain_name = default
user_domain_name = default
region_name = RegionOne
project_name = service
username = nova
password = Changeme_123
# if using self-signed certs on Apache2 Keystone, turn to [true]
insecure = true

[oslo_concurrency]
lock_path = $state_path/tmp

[oslo_policy]
enforce_new_defaults = true"""


        # 写入文件
        file.write(text)
        logging.info("create /etc/neutron/neutron.conf")
    runcmd("rm -f /etc/neutron/fwaas_driver.ini")
    runcmd("touch /etc/neutron/fwaas_driver.ini")
    runcmd("chmod 640 /etc/neutron/fwaas_driver.ini")

    with open("/etc/neutron/plugins/ml2/ml2_conf.ini", "w") as file:
        # 多行文本
        text = """[DEFAULT]
[ml2]
type_drivers = flat,vlan,vxlan
tenant_network_types =
mechanism_drivers = openvswitch
extension_drivers = port_security
[ml2_type_flat]
flat_networks = physnet1
[ml2_type_geneve]
[ml2_type_gre]
[ml2_type_vlan]
[ml2_type_vxlan]
[ovs_driver]
[securitygroup]
[sriov_driver]"""


        # 写入文件
        file.write(text)
        logging.info("create /etc/neutron/plugins/ml2/ml2_conf.ini")

    with open("/etc/neutron/metadata_agent.ini", "w") as file:
        # 多行文本
        text = """[DEFAULT]
nova_metadata_host = 179.20.3.81
metadata_proxy_shared_secret =Changeme_123
nova_metadata_protocol = http
[agent]
[cache]
memcache_servers = 179.20.3.81:11211"""


        # 写入文件
        file.write(text)
        logging.info("create /etc/neutron/metadata_agent.ini")


    #替换变量
    runcmd('sed -i "s/179.20.3.81/%s/g" /etc/neutron/neutron.conf' % mgmt_ip) 
    runcmd('sed -i "s/Changeme_123/%s/g" /etc/neutron/neutron.conf' % root_password)   
    runcmd('sed -i "s/179.20.3.81/%s/g" /etc/neutron/plugins/ml2/ml2_conf.ini' % mgmt_ip) 
    runcmd('sed -i "s/Changeme_123/%s/g" /etc/neutron/plugins/ml2/ml2_conf.ini' % root_password)  
    runcmd('sed -i "s/179.20.3.81/%s/g" /etc/neutron/metadata_agent.ini' % mgmt_ip) 
    runcmd('sed -i "s/Changeme_123/%s/g" /etc/neutron/metadata_agent.ini' % root_password)  






    runcmd('rm -f /etc/neutron/plugin.ini')
    runcmd('ln -s /etc/neutron/plugins/ml2/ml2_conf.ini /etc/neutron/plugin.ini')
    runcmd('su -s /bin/bash neutron -c "neutron-db-manage --config-file /etc/neutron/neutron.conf --config-file /etc/neutron/plugin.ini upgrade head"')
    runcmd('systemctl restart neutron-server neutron-metadata-agent nova-api nginx')
    ####以上是控制节点安装
    runcmd("apt -y install neutron-plugin-ml2 neutron-openvswitch-agent neutron-l3-agent neutron-dhcp-agent neutron-metadata-agent openvswitch-switch python3-neutronclient")
    with open("/etc/neutron/l3_agent.ini", "w") as file:
        # 多行文本
        text = """[DEFAULT]
interface_driver = openvswitch
[agent]
[network_log]
[ovs]"""
        # 写入文件
        file.write(text)
        logging.info("create /etc/neutron/l3_agent.ini")
    with open("/etc/neutron/dhcp_agent.ini", "w") as file:
        # 多行文本
        text = """[DEFAULT]
interface_driver = openvswitch
dhcp_driver = neutron.agent.linux.dhcp.Dnsmasq
enable_isolated_metadata = true
[agent]
[ovs]"""
        # 写入文件
        file.write(text)
        logging.info("create /etc/neutron/dhcp_agent.ini")

    with open("/etc/neutron/plugins/ml2/openvswitch_agent.ini", "w") as file:
        # 多行文本
        text = """[DEFAULT]
[agent]
[dhcp]
[network_log]
[ovs]
bridge_mappings = physnet1:br-eth1
[securitygroup]
firewall_driver = openvswitch
enable_security_group = true
enable_ipset = true"""
        # 写入文件
        file.write(text)
        logging.info("create /etc/neutron/plugins/ml2/openvswitch_agent.ini") 

    query_command = "ovs-vsctl show  | grep br-eth1"
    result = subprocess.run(query_command, shell=True)
    # 判断查询结果
    if result.returncode == 0:
        logging.info("br-eth1 already exists.")
    else:
        runcmd("ovs-vsctl add-br br-eth1")
        runcmd(f"ovs-vsctl add-port br-eth1 {NIC_NAME}")

    runcmd("systemctl restart neutron-l3-agent neutron-dhcp-agent neutron-metadata-agent neutron-openvswitch-agent")
    runcmd("systemctl enable neutron-l3-agent neutron-dhcp-agent neutron-metadata-agent neutron-openvswitch-agent")

    query_command = "openstack network list  | grep sharednet1"
    result = subprocess.run(query_command, shell=True)
    # 判断查询结果
    if result.returncode == 0:
        logging.info("sharednet1 Network already exists.")
    else:
        # 获取service项目ID
        project_id_command = "openstack project list | grep service | awk '{print $2}'"
        project_id_output = subprocess.check_output(project_id_command, shell=True).decode("utf-8")
        project_id = project_id_output.strip()

        # 创建网络
        network_create_command = f"openstack network create --project {project_id} --share --provider-network-type flat --provider-physical-network physnet1 sharednet1"
        subprocess.call(network_create_command, shell=True)
        runcmd(f"openstack subnet create subnet1 --network sharednet1 --project {project_id} --subnet-range {subnet} --gateway {subgw} --dns-nameserver {subdns}")

    
    runcmd('openstack network agent list')
    runcmd("echo `date` > /etc/openstack_tag/neutron.tag")

    print("\033[32m ############################### \033[0m")
    print("\033[32m neutron installation completed. \033[0m")
    print("\033[32m ############################### \033[0m")
    logging.info("neutron installation completed.")


