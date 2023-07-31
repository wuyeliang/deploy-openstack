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

def function_nova_init():
    if os.path.exists("/etc/openstack_tag/nova.tag"):
        logging.error("/etc/openstack_tag/nova.tag file  exist.")
        print("/etc/openstack_tag/nova.tag file  exist.")
        sys.exit()
    else:
        logging.info("/etc/openstack_tag/nova.tag file does not exist.")
    cf = configparser.ConfigParser()

    cf.read("config/config.ini")  # 读取配置文件，如果写文件的绝对路径，就可以不用os模块
    #获取日志目录
    root_password = cf.get("CONTROLLER", "ALL_PASSWORD") 
    mgmt_ip= cf.get("CONTROLLER", "MANAGER_IP") 
    #创建用户
    libfunc.create_or_check_user("nova", root_password)
    libfunc.create_or_check_user("placement", root_password)
    #赋予权限
    runcmd("openstack role add --project service --user nova admin")
    runcmd("openstack role add --project service --user placement admin")
 
    #创建service
    libfunc.check_and_create_service('nova', 'OpenStack Compute service', 'compute')
    libfunc.check_and_create_service('placement', 'OpenStack Compute Placement service', 'placement')

    #创建endpoint
    libfunc.check_and_create_endpoint_v2('compute', '8774', mgmt_ip, 'admin')
    libfunc.check_and_create_endpoint_v2('compute', '8774', mgmt_ip, 'internal')
    libfunc.check_and_create_endpoint_v2('compute', '8774', mgmt_ip, 'public')
    libfunc.check_and_create_endpoint('placement', '8778', mgmt_ip,'admin')
    libfunc.check_and_create_endpoint('placement', '8778', mgmt_ip, 'internal')
    libfunc.check_and_create_endpoint('placement', '8778', mgmt_ip,'public')

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
        cursor.execute("CREATE DATABASE IF NOT EXISTS nova")
        logging.info("CREATE DATABASE IF NOT EXISTS nova")

        cursor.execute("CREATE DATABASE IF NOT EXISTS nova_api")
        logging.info("CREATE DATABASE IF NOT EXISTS nova_api")

        cursor.execute("CREATE DATABASE IF NOT EXISTS placement")
        logging.info("CREATE DATABASE IF NOT EXISTS placement")

        cursor.execute("CREATE DATABASE IF NOT EXISTS nova_cell0")
        logging.info("CREATE DATABASE IF NOT EXISTS nova_cell0")


        cursor.execute(f"GRANT ALL PRIVILEGES ON nova.* TO 'nova'@'localhost' IDENTIFIED BY \"{root_password}\";")
        logging.info(f"GRANT ALL PRIVILEGES ON nova.* TO 'nova'@'localhost' IDENTIFIED BY \"{root_password}\";")
        cursor.execute(f"grant all privileges on nova.* to nova@'%' identified by \"{root_password}\";")
        logging.info(f"GRANT ALL PRIVILEGES ON nova.* TO 'nova'@'localhost' IDENTIFIED BY \"{root_password}\";")

        cursor.execute(f"GRANT ALL PRIVILEGES ON nova_api.* TO 'nova'@'localhost' IDENTIFIED BY \"{root_password}\";")
        logging.info(f"GRANT ALL PRIVILEGES ON nova_api.* TO 'nova'@'localhost' IDENTIFIED BY \"{root_password}\";")
        cursor.execute(f"grant all privileges on nova_api.* to nova@'%' identified by \"{root_password}\";")
        logging.info(f"GRANT ALL PRIVILEGES ON nova_api.* TO 'nova'@'localhost' IDENTIFIED BY \"{root_password}\";")

        cursor.execute(f"GRANT ALL PRIVILEGES ON placement.* TO 'placement'@'localhost' IDENTIFIED BY \"{root_password}\";")
        logging.info(f"GRANT ALL PRIVILEGES ON placement.* TO 'placement'@'localhost' IDENTIFIED BY \"{root_password}\";")
        cursor.execute(f"grant all privileges on placement.* to placement@'%' identified by \"{root_password}\";")
        logging.info(f"GRANT ALL PRIVILEGES ON placement.* TO 'placement'@'localhost' IDENTIFIED BY \"{root_password}\";")


        cursor.execute(f"GRANT ALL PRIVILEGES ON nova_cell0.* TO 'nova'@'localhost' IDENTIFIED BY \"{root_password}\";")
        logging.info(f"GRANT ALL PRIVILEGES ON nova_cell0.* TO 'nova'@'localhost' IDENTIFIED BY \"{root_password}\";")
        cursor.execute(f"grant all privileges on nova_cell0.* to nova@'%' identified by \"{root_password}\";")
        logging.info(f"GRANT ALL PRIVILEGES ON nova_cell0.* TO 'nova'@'localhost' IDENTIFIED BY \"{root_password}\";")

    # 刷新权限
        cursor.execute("FLUSH PRIVILEGES")
        # 提交事务
        connection.commit()
        # 输出成功信息
        logging.info("成功创建数据库 nova")
    except pymysql.Error as error:
        # 输出错误信息
        logging.error("创建数据库时出错：", error)
        sys.exit(1)
    finally:
        # 关闭游标和数据库连接
        cursor.close()
        connection.close()
    runcmd("apt -y install nova-api nova-conductor nova-scheduler nova-novncproxy placement-api python3-novaclient")
    with open("/etc/nova/nova.conf", "w") as file:
        # 多行文本
        text = """[DEFAULT]
allow_resize_to_same_host = true
ram_allocation_ratio = 3
cpu_allocation_ratio = 5
vif_plugging_is_fatal = True
block_device_allocate_retries=3600
vif_plugging_timeout = 300
osapi_compute_listen = 127.0.0.1
osapi_compute_listen_port = 8774
metadata_listen = 127.0.0.1
metadata_listen_port = 8775
state_path = /var/lib/nova
enabled_apis = osapi_compute,metadata
log_dir = /var/log/nova
transport_url = rabbit://openstack:Changeme_123@179.20.3.81
[api]
auth_strategy = keystone
[vnc]
server_listen = 179.20.3.81
server_proxyclient_address = 179.20.3.81
enabled = True
novncproxy_host = 127.0.0.1
novncproxy_port = 6080
novncproxy_base_url = http://179.20.3.81:6080/vnc_auto.html
[glance]
api_servers = http://179.20.3.81:9292
[oslo_concurrency]
lock_path = $state_path/tmp
[api_database]
connection = mysql+pymysql://nova:Changeme_123@179.20.3.81/nova_api
[database]
connection = mysql+pymysql://nova:Changeme_123@179.20.3.81/nova
[keystone_authtoken]
www_authenticate_uri = http://179.20.3.81:5000
auth_url = http://179.20.3.81:5000
memcached_servers = 179.20.3.81:11211
auth_type = password
project_domain_name = default
user_domain_name = default
project_name = service
username = nova
password = Changeme_123
insecure = true
[placement]
auth_url = http://179.20.3.81:5000
os_region_name = RegionOne
auth_type = password
project_domain_name = default
user_domain_name = default
project_name = service
username = placement
password = Changeme_123
insecure = true
[wsgi]
api_paste_config = /etc/nova/api-paste.ini
[oslo_policy]
enforce_new_defaults = true
[neutron]
auth_url = http://179.20.3.81:5000
auth_type = password
project_domain_name = default
user_domain_name = default
region_name = RegionOne
project_name = service
username = neutron
password = Changeme_123
service_metadata_proxy = True
metadata_proxy_shared_secret = Changeme_123
insecure = true
[cinder]
os_region_name = RegionOne
[conductor]
workers = 2
[scheduler]
workers = 2
[api]
workers = 2
[libvirt]
live_snapshot_support = True
cpu_mode = host-passthrough
wait_soft_reboot_seconds = 300
live_migration_downtime = 1500
live_migration_progress_timeout = 5000
l2_cache_enabled = True
virt_type = kvm
l2_cache_max_size = -1"""


        # 写入文件
        file.write(text)
        logging.info("create /etc/nova/nova.conf")



    with open("/etc/placement/placement.conf", "w") as file:
        # 多行文本
        text = """[DEFAULT]
debug = false
[api]
auth_strategy = keystone
[keystone_authtoken]
www_authenticate_uri = http://179.20.3.81:5000
auth_url = http://179.20.3.81:5000
memcached_servers = 179.20.3.81:11211
auth_type = password
project_domain_name = default
user_domain_name = default
project_name = service
username = placement
password = Changeme_123
insecure = true
[placement_database]
connection = mysql+pymysql://placement:Changeme_123@179.20.3.81/placement"""


        # 写入文件
        file.write(text)
        logging.info("create /etc/placement/placement.conf")

    #替换变量
    runcmd('sed -i "s/179.20.3.81/%s/g" /etc/placement/placement.conf' % mgmt_ip) 
    runcmd('sed -i "s/Changeme_123/%s/g" /etc/placement/placement.conf' % root_password)   
    runcmd('sed -i "s/179.20.3.81/%s/g" /etc/nova/nova.conf' % mgmt_ip) 
    runcmd('sed -i "s/Changeme_123/%s/g" /etc/nova/nova.conf' % root_password)  

    with open("/etc/apache2/sites-enabled/placement-api.conf", "w") as file:
        # 多行文本
        text = """Listen 127.0.0.1:8778

<VirtualHost *:8778>
    WSGIScriptAlias / /usr/bin/placement-api
    WSGIDaemonProcess placement-api processes=5 threads=1 user=placement group=placement display-name=%{GROUP}
    WSGIProcessGroup placement-api
    WSGIApplicationGroup %{GLOBAL}
    WSGIPassAuthorization On
    LimitRequestBody 114688

    <IfVersion >= 2.4>
      ErrorLogFormat "%{cu}t %M"
    </IfVersion>

    ErrorLog /var/log/apache2/placement_api_error.log
    CustomLog /var/log/apache2/placement_api_access.log combined

    <Directory /usr/bin>
        <IfVersion >= 2.4>
            Require all granted
        </IfVersion>
        <IfVersion < 2.4>
            Order allow,deny
            Allow from all
        </IfVersion>
    </Directory>
</VirtualHost>

Alias /placement /usr/bin/placement-api
<Location /placement>
  SetHandler wsgi-script
  Options +ExecCGI

  WSGIProcessGroup placement-api
  WSGIApplicationGroup %{GLOBAL}
  WSGIPassAuthorization On
</Location>"""


        # 写入文件
        file.write(text)
        logging.info("create /etc/apache2/sites-enabled/placement-api.conf")



    runcmd('su -s /bin/bash placement -c "placement-manage db sync"')
    runcmd('su -s /bin/bash nova -c "nova-manage api_db sync"')
    runcmd('su -s /bin/bash nova -c "nova-manage cell_v2 map_cell0"')
    runcmd('su -s /bin/bash nova -c "nova-manage db sync"')
    runcmd('su -s /bin/bash nova -c "nova-manage cell_v2 create_cell --name cell1" || echo 1')
    runcmd('systemctl restart nova-api nova-conductor nova-scheduler nova-novncproxy')
    runcmd('systemctl enable nova-api nova-conductor nova-scheduler nova-novncproxy')
    runcmd('systemctl restart apache2 nginx')
    runcmd('apt -y install nova-compute nova-compute-kvm')
    runcmd('systemctl restart nova-compute')
    runcmd('su -s /bin/bash nova -c "nova-manage cell_v2 discover_hosts"')
    runcmd('openstack compute service list')
    runcmd("echo `date` > /etc/openstack_tag/nova.tag")
    print("\033[32m ############################### \033[0m")
    print("\033[32m nova installation completed. \033[0m")
    print("\033[32m ############################### \033[0m")
    logging.info("nova installation completed.")
