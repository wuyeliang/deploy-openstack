# deploy-openstack

[English](./README.md) | 简体中文

`deploy-openstack` 是一个基于 Python 3 的单机 OpenStack Epoxy 自动化部署项目，目标环境为 Ubuntu 24.04 LTS，适合实验室、PoC、内部测试和学习场景。

这个分支的优化重点有三项：

- 改善入口脚本，支持步骤编号、步骤 ID 和命令行参数
- 抽取公共运行时能力，统一配置校验、日志和命令执行
- 补全中英文文档，便于交付、维护和二次修改

## 1. 项目范围

当前支持：

- 单机版 OpenStack Epoxy
- Ubuntu 24.04.x LTS
- Python 3
- 本地部署 MariaDB、RabbitMQ、Memcached、Nginx、Apache2
- Keystone、Glance、Nova、Cinder、Neutron、Horizon 控制节点安装流程

建议硬件配置：

| 项目 | 建议配置 |
| --- | --- |
| CPU | 32 核 |
| 内存 | 128 GB |
| 管理网卡 | `eno1` |
| 业务 / 外部网络网卡 | `eno2` |
| 系统盘 | `sda` |
| Cinder 磁盘 | `sdb` |

## 2. 目录说明

| 路径 | 说明 |
| --- | --- |
| `main.py` | 主入口，支持交互模式和命令行模式 |
| `script/sys_init.py` | 系统初始化 |
| `script/db_mq_init.py` | MariaDB、RabbitMQ、Memcached、Nginx |
| `script/keystone_init.py` | Keystone 安装 |
| `script/glance_init.py` | Glance 安装 |
| `script/nova_init.py` | Nova 与 Placement 安装 |
| `script/cinder_init.py` | Cinder 安装 |
| `script/neutron_init.py` | Neutron 安装 |
| `script/horizon_init.py` | Horizon 安装 |
| `script/lib/libfunc.py` | OpenStack 资源操作公共函数 |
| `script/lib/runtime.py` | 新增公共运行时模块，负责配置、日志、校验、命令执行 |
| `config/config.ini` | 主配置文件 |
| `config/hosts` | hosts 模板 |

## 3. 快速开始

### 3.1 准备系统

安装 Ubuntu 24.04 LTS，保证系统能联网并访问软件源。

```bash
lsb_release -a
apt update
apt install -y python3 python3-pymysql git
```

### 3.2 下载代码

```bash
git clone https://github.com/wuyeliang/deploy-openstack.git
cd deploy-openstack
git switch Epoxy
```

### 3.3 修改配置

编辑 `config/hosts`：

```text
127.0.0.1   localhost localhost.localdomain localhost4 localhost4.localdomain4
::1         localhost localhost.localdomain localhost6 localhost6.localdomain6
172.16.8.81 node1
```

编辑 `config/config.ini`：

```ini
[CONTROLLER]
HOST_NAME=node1
MANAGER_IP=172.16.8.81
ALL_PASSWORD=Changeme_123
NET_DEVICE_NAME=eno2

[FLOATING_METWORK_ADDR]
NEUTRON_PUBLIC_NET=10.16.10.0/24
PUBLIC_NET_GW=10.16.10.1
NEUTRON_DNS=114.114.114.114

[VOLUME]
CINDER_DISK=/dev/sdb

[LOG]
LOG_DIR=/var/log/openstack.log
```

### 3.4 部署前校验

```bash
sudo python3 main.py --validate-config
sudo python3 main.py --list-steps
```

### 3.5 执行部署

交互模式：

```bash
sudo python3 main.py
```

执行单个步骤：

```bash
sudo python3 main.py --step keystone
sudo python3 main.py --step 3
```

顺序执行全部步骤：

```bash
sudo python3 main.py --all
```

## 4. 部署步骤说明

| 步骤 | ID | 说明 |
| --- | --- | --- |
| 1 | `system` | 初始化 Ubuntu、主机名、源、基础依赖、hosts |
| 2 | `db-mq` | 安装 MariaDB、RabbitMQ、Memcached、Nginx |
| 3 | `keystone` | 创建 Keystone 数据库并完成引导 |
| 4 | `glance` | 安装镜像服务 |
| 5 | `nova` | 安装计算与 Placement 服务 |
| 6 | `cinder` | 安装块存储服务 |
| 7 | `neutron` | 安装网络服务 |
| 8 | `horizon` | 安装控制台 |

## 5. 运行注意事项

- 第一步会重启系统，用于让新的内核和基础环境生效。
- 推荐全程以 `root` 身份执行。
- 每个模块完成后，都会在 `/etc/openstack_tag/` 下写入标记文件，避免重复执行。
- 当前脚本会直接覆盖部分 `/etc` 下的服务配置文件，部署前建议先审阅模板内容。
- 项目更适合测试和实验环境，不是经过加固的生产级部署方案。

## 6. 日志与校验

- 主日志路径由 `config/config.ini` 中的 `LOG_DIR` 决定
- 新增的配置校验会检查必需 section、必需 key，以及 `config/hosts` 是否存在
- 公共命令执行逻辑已统一，失败信息会更明确

## 7. 常见问题

### Keystone 安装后报认证错误

先加载管理员环境，再重复执行 Keystone 步骤：

```bash
source /root/keystonerc
sudo python3 main.py --step keystone
```

### 提示某个 tag 文件已存在

说明对应模块之前已经执行过。请先检查 `/etc/openstack_tag/` 下的对应文件，再决定是否手动清理后重跑。

### Horizon 能打开但无法登录

请优先检查：

- `config/config.ini` 中的 `MANAGER_IP`
- `/etc/openstack-dashboard/local_settings.py`
- `/root/keystonerc` 中的管理员凭据

### 服务启动失败

重点排查：

- `/var/log/openstack.log`
- `systemctl status <服务名>`
- 生成后的服务配置文件里 IP 和密码替换是否正确

## 8. 部署完成后的访问方式

部署成功后，可通过以下地址访问 Horizon：

```text
http://<MANAGER_IP>/horizon
```

默认管理员信息：

- 用户名：`admin`
- 密码：`ALL_PASSWORD` 的配置值

## 9. 安全提醒

当前脚本会直接修改系统软件源、主机名、网络服务和 OpenStack 服务配置。建议在全新主机、专用测试机或可回滚环境中执行。
