#!/usr/bin/python3
# -*- coding: utf-8 -*-
# vi: set autoindent ts=4 expandtab :
import subprocess
def check_project_exist(project_name):
    try:
        # 检查项目是否存在
        subprocess.run(["openstack", "project", "show", project_name], capture_output=True, check=True, text=True)
        return True  # 如果没有发生异常，表示项目存在
    except subprocess.CalledProcessError:
        return False  # 如果发生异常，表示项目不存在

def create_project(project_name, description="Service Project", domain="default"):
    # 创建项目
    subprocess.run(["openstack", "project", "create", "--domain", domain, "--description", description, project_name], check=True)

def check_or_create_project(project_name, description="Service Project"):
    if check_project_exist(project_name):
        print(f"项目 '{project_name}' 已存在")
    else:
        print(f"项目 '{project_name}' 不存在，正在创建...")
        create_project(project_name, description)
        print(f"项目 '{project_name}' 创建成功")


#判断用户是否存在，并创建用户
def check_user(username):
    command = f"openstack user show {username}"
    result = subprocess.run(command, shell=True, capture_output=True, encoding="utf-8")
    
    if result.returncode == 0:
        return True  # 用户存在
    else:
        return False  # 用户不存在

def create_user(username, password):
    domain = "default"
    project = "service"
    command = f"openstack user create --domain {domain} --project {project} --password {password} {username}"
    result = subprocess.run(command, shell=True, capture_output=True, encoding="utf-8")
    
    if result.returncode == 0:
        return True  # 用户创建成功
    else:
        return False  # 用户创建失败

def create_or_check_user(username, password):
    if check_user(username):
        print(f"User '{username}' already exists")
    else:
        if create_user(username, password):
            print(f"User '{username}' created successfully")
        else:
            print(f"Failed to create user '{username}'")

# 示例用法
#create_or_check_user("glance", "servicepassword")

#判断service是否存在并创建service
def check_and_create_service(service_name, description, service_type):
    # 查询服务列表
    services = subprocess.check_output(['openstack', 'service', 'list'])
    
    # 检查服务是否存在
    if service_name not in services.decode():
        print(f"{service_name} 服务不存在，开始创建...")
        
        # 创建服务
        cmd = ['openstack', 'service', 'create', '--name', service_name, '--description', description, service_type]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # 检查创建结果
        if result.returncode == 0:
            print(f"{service_name} 服务创建成功！")
        else:
            print(f"{service_name} 服务创建失败：{result.stderr}")
            sys.exit(1)
    else:
        print(f"{service_name} 服务已存在！")

# 使用示例
#check_and_create_service('glance', 'OpenStack Image service', 'image')

#创建endpoint
def check_and_create_endpoint(image, port, controller, endpoint_type):
    # 查询命令
    query_command = f"openstack endpoint list | grep {port} | grep {endpoint_type} | grep {controller}"
    result = subprocess.run(query_command, shell=True)

    # 判断查询结果
    if result.returncode == 0:
        print("Endpoint already exists.")
    else:
        # 创建命令
        create_command = f"openstack endpoint create --region RegionOne {image} {endpoint_type} http://{controller}:{port}"
        try:
            subprocess.check_call(create_command, shell=True)
            print("Endpoint created successfully.")
        except subprocess.CalledProcessError:
            print("Failed to create endpoint.")
            sys.exit(1)

# 使用示例
#check_and_create_endpoint("image", "9292", "controller", "internal")




#创建endpoint v2
def check_and_create_endpoint_v2(image, port, controller, endpoint_type):
    # 查询命令
    query_command = f"openstack endpoint list | grep {port} | grep {endpoint_type} | grep {controller}"
    result = subprocess.run(query_command, shell=True)

    # 判断查询结果
    if result.returncode == 0:
        print("Endpoint already exists.")
    else:
        # 创建命令
        create_command = f"openstack endpoint create --region RegionOne {image} {endpoint_type} http://{controller}:{port}/v2.1/%\(tenant_id\)s"
        try:
            subprocess.check_call(create_command, shell=True)
            print("Endpoint created successfully.")
        except subprocess.CalledProcessError:
            print("Failed to create endpoint.")
            sys.exit(1)

# 使用示例
#check_and_create_endpoint("image", "9292", "controller", "internal")


#创建endpoint v3
def check_and_create_endpoint_v3(image, port, controller, endpoint_type):
    # 查询命令
    query_command = f"openstack endpoint list | grep {port} | grep {endpoint_type} | grep {controller}"
    result = subprocess.run(query_command, shell=True)

    # 判断查询结果
    if result.returncode == 0:
        print("Endpoint already exists.")
    else:
        # 创建命令
        create_command = f"openstack endpoint create --region RegionOne {image} {endpoint_type} http://{controller}:{port}/v3/%\(tenant_id\)s"
        try:
            subprocess.check_call(create_command, shell=True)
            print("Endpoint created successfully.")
        except subprocess.CalledProcessError:
            print("Failed to create endpoint.")
            sys.exit(1)

# 使用示例
#check_and_create_endpoint("image", "9292", "controller", "internal")