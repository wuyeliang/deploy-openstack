The current version supports the installation of OpenStack's Antelope version on a single machine. The deployment script is written in Python 3. The operating system is based on Ubuntu 22.04.2 LTS.
Number | Category | Specification
---|---| ---
1 | CPU | 32 cores
2 | Memory | 128GB
3 | Network Port | eno1 mgmt
4 | Network Port | eno2 vm net
5 | Disk | sda System Disk
6 | Disk | sdb Cinder Volume

**1. Basic Configuration**

1. Install the operating system. After installation, no additional steps are required other than being able to access the internet.
```
# lsb_release  -a
No LSB modules are available.
Distributor ID: Ubuntu
Description:    Ubuntu 22.04.2 LTS
Release:        22.04
Codename:       jammy
```
2. Update the package resources.
```
# apt update
# apt install python3-pymysql -y
```

**2. Modify Configuration Files**

1. Download and install the code.
```
git clone https://github.com/wuyeliang/deploy-openstack.git
```

2. Modify the hosts file at /root/deploy-openstack/config/hosts.
```
127.0.0.1   localhost localhost.localdomain localhost4 localhost4.localdomain4
::1         localhost localhost.localdomain localhost6 localhost6.localdomain6
172.16.8.81   node1
```

3. Modify the configuration file at /root/deploy-openstack/config/config.ini.
```
[CONTROLLER]
# Hostname of the current node
HOST_NAME=node1
# Management IP address of the current node
MANAGER_IP=172.16.8.81
# Password for all accounts
ALL_PASSWORD=Changeme_123
# Network device for virtual machines (default: flat network)
NET_DEVICE_NAME=eno2

# Business network segment for virtual machines
[FLOATING_METWORK_ADDR]
NEUTRON_PUBLIC_NET=10.16.10.0/24
PUBLIC_NET_GW=10.16.10.1
NEUTRON_DNS=114.114.114.114

# For Cinder
[VOLUME]
# Disk list for Cinder volumes
CINDER_DISK=/dev/sdb

[LOG]
# Log directory for installation path
LOG_DIR=/var/log/openstack.log
```

**3. Perform the Installation**

1. Execute the installation.
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
        
Please enter a number:
```
Note:
- The system environment configuration in the first step will automatically restart to apply the new kernel version.
- If there is an error during the installation of Keystone, manually execute `source /root/keystonerc` and repeat the Keystone installation.
- After the installation is complete, you can log in through `http://<management IP address>/horizon` using the admin account and the password configured in the above configuration file.