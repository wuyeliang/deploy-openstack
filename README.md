# deploy-openstack

English | [简体中文](./README-ZH.md)

`deploy-openstack` is a Python 3 automation project for deploying a single-node OpenStack Epoxy environment on Ubuntu 24.04 LTS. The repository focuses on a simple step-by-step installation flow for controller services in a lab, PoC, or internal test environment.

This branch has been optimized around three goals:

- clearer entrypoint behavior with step IDs and CLI arguments
- reusable runtime utilities for config validation and command execution
- more complete bilingual documentation for installation, operation, and troubleshooting

## 1. Scope

Supported deployment model:

- single-node OpenStack Epoxy
- Ubuntu 24.04.x LTS
- Python 3
- local MariaDB, RabbitMQ, Memcached, Nginx, Apache2
- controller-side setup for Keystone, Glance, Nova, Cinder, Neutron, and Horizon

Recommended host profile:

| Item | Recommendation |
| --- | --- |
| CPU | 32 cores |
| Memory | 128 GB |
| Management NIC | `eno1` |
| Provider / VM NIC | `eno2` |
| System disk | `sda` |
| Cinder disk | `sdb` |

## 2. Repository Layout

| Path | Description |
| --- | --- |
| `main.py` | Main entrypoint with interactive mode and CLI mode |
| `script/sys_init.py` | Base OS preparation |
| `script/db_mq_init.py` | MariaDB, RabbitMQ, Memcached, Nginx |
| `script/keystone_init.py` | Keystone installation |
| `script/glance_init.py` | Glance installation |
| `script/nova_init.py` | Nova and Placement installation |
| `script/cinder_init.py` | Cinder installation |
| `script/neutron_init.py` | Neutron installation |
| `script/horizon_init.py` | Horizon installation |
| `script/lib/libfunc.py` | OpenStack resource helper functions |
| `script/lib/runtime.py` | Shared runtime helpers for config, logging, validation, and shell execution |
| `config/config.ini` | Main deployment configuration |
| `config/hosts` | Hosts file template |

## 3. Quick Start

### 3.1 Prepare the host

Install Ubuntu 24.04 LTS and ensure the node can access package mirrors and the internet.

```bash
lsb_release -a
apt update
apt install -y python3 python3-pymysql git
```

### 3.2 Clone the repository

```bash
git clone https://github.com/wuyeliang/deploy-openstack.git
cd deploy-openstack
git switch Epoxy
```

### 3.3 Update configuration

Edit `config/hosts`:

```text
127.0.0.1   localhost localhost.localdomain localhost4 localhost4.localdomain4
::1         localhost localhost.localdomain localhost6 localhost6.localdomain6
172.16.8.81 node1
```

Edit `config/config.ini`:

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

### 3.4 Validate before deployment

```bash
sudo python3 main.py --validate-config
sudo python3 main.py --list-steps
```

### 3.5 Run deployment

Interactive mode:

```bash
sudo python3 main.py
```

Run one specific step:

```bash
sudo python3 main.py --step keystone
sudo python3 main.py --step 3
```

Run all steps:

```bash
sudo python3 main.py --all
```

## 4. Deployment Steps

| Step | ID | Description |
| --- | --- | --- |
| 1 | `system` | Prepare Ubuntu, hostname, package source, base packages, hosts |
| 2 | `db-mq` | Install MariaDB, RabbitMQ, Memcached, Nginx |
| 3 | `keystone` | Create Keystone DB and bootstrap identity |
| 4 | `glance` | Install image service |
| 5 | `nova` | Install compute and placement services |
| 6 | `cinder` | Install block storage service |
| 7 | `neutron` | Install networking service |
| 8 | `horizon` | Install dashboard |

## 5. Operational Notes

- Step 1 reboots the machine to activate the updated kernel and base environment.
- The scripts are designed to be run as `root`.
- A marker file is written under `/etc/openstack_tag/` after each completed module to avoid accidental repeated execution.
- Many service configuration files are written directly to `/etc`, so review the templates before running in a shared environment.
- The scripts are intended for lab or controlled environments, not hardened production deployment.

## 6. Logging and Validation

- Main log file: path defined by `LOG_DIR` in `config/config.ini`
- Config validation checks required sections, required keys, and the presence of `config/hosts`
- Command failures now surface more clearly through the shared runtime helper

## 7. Troubleshooting

### Keystone fails after bootstrap

Try loading the admin environment and rerun the Keystone step:

```bash
source /root/keystonerc
sudo python3 main.py --step keystone
```

### A step says a tag file already exists

That means the module was previously completed. Review the corresponding file under `/etc/openstack_tag/` before rerunning manually.

### Horizon is installed but login fails

Check:

- `MANAGER_IP` in `config/config.ini`
- Horizon config at `/etc/openstack-dashboard/local_settings.py`
- Keystone admin credentials in `/root/keystonerc`

### Services do not start

Review:

- `/var/log/openstack.log`
- `systemctl status <service>`
- database connectivity and host IP replacement in generated config files

## 8. Access After Deployment

Once deployment succeeds, Horizon should be available at:

```text
http://<MANAGER_IP>/horizon
```

Default admin account:

- username: `admin`
- password: the value of `ALL_PASSWORD`

## 9. Safety Reminder

These scripts modify system packages, network services, host identity, and OpenStack service configs directly. Use a fresh or dedicated test machine whenever possible.
