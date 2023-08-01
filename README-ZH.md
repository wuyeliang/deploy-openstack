当前版本的支持安装单机版Antelope版本的OpenStack。部署脚本基于python3写的。操作系统基于Ubuntu 22.04.2 LTS。
编号 | 类别 | 规格
---|---| ---
1 |CPU| 32 core
2 | 内存| 128G
3 | 网口| eno1 mgmt
4 | 网口| eno2 虚拟机外部网络
5 | 磁盘| sda 系统盘
6 | 磁盘| sdb cinder volume
**一、基础配置。**

1、安装操作系统，安装完成之后除了可上网，无需做任何事情。
```
# lsb_release  -a
No LSB modules are available.
Distributor ID: Ubuntu
Description:    Ubuntu 22.04.2 LTS
Release:        22.04
Codename:       jammy
```
2、更新源
```
# apt update
# apt install python3-pymysql -y
```

**二、修改配置文件**

1、下载安装代码

```
git clone https://github.com/wuyeliang/deploy-openstack.git
```


2、修改hosts文件/root/deploy-openstack/config/hosts
```
127.0.0.1   localhost localhost.localdomain localhost4 localhost4.localdomain4
::1         localhost localhost.localdomain localhost6 localhost6.localdomain6
172.16.8.81   node1
```

3、修改/root/deploy-openstack/config/config.ini
```
[CONTROLLER]
#当前节点的主机名
HOST_NAME=node1
#当前节点的管理网地址
MANAGER_IP=172.16.8.81
#所有账号的密码
ALL_PASSWORD=Changeme_123
#虚拟机业务网卡（默认flat网络）
NET_DEVICE_NAME=eno2

#虚拟机的业务网段
[FLOATING_METWORK_ADDR]
NEUTRON_PUBLIC_NET=10.16.10.0/24
PUBLIC_NET_GW=10.16.10.1
NEUTRON_DNS=114.114.114.114



#For cinder
[VOLUME]
#cinder卷的磁盘列表
CINDER_DISK=/dev/sdb


[LOG]
#安装路径的日志
LOG_DIR=/var/log/openstack.log
```

**三、执行安装**
1、执行安装
```
# python3 main.py 

    1) Configure System Environment.
    2) Install Mariadb and Rabbitmq-server.
    3) Install Keystone.
    4) Install Glance.
    5) Install Nova.
    6) Install Cinder.
    7) Install Neutron.
    8) Install Dashboard.
    0) Quit
        
请输入一个数字：
```
注意：
- 第一步配置环境系统会自动重启的，目的为了使新版本的内核生效。
- 安装Keystone如果报错，手动执行下source /root/keystonerc,重复执行安装keystone即可。
- 安装完成后可通过http://<管理网地址>/horizon 登录，账号是admin，密码是上面配置文件中配置的密码。