#!/usr/bin/python3
# -*- coding: utf-8 -*-

import subprocess
import sys


def _run_openstack_command(args, check=False):
    return subprocess.run(
        ["openstack", *args],
        capture_output=True,
        text=True,
        check=check,
    )


def check_project_exist(project_name):
    result = _run_openstack_command(["project", "show", project_name])
    return result.returncode == 0


def create_project(project_name, description="Service Project", domain="default"):
    _run_openstack_command(
        [
            "project",
            "create",
            "--domain",
            domain,
            "--description",
            description,
            project_name,
        ],
        check=True,
    )


def check_or_create_project(project_name, description="Service Project"):
    if check_project_exist(project_name):
        print(f"Project '{project_name}' already exists")
        return

    print(f"Project '{project_name}' does not exist, creating it...")
    create_project(project_name, description)
    print(f"Project '{project_name}' created successfully")


def check_user(username):
    result = _run_openstack_command(["user", "show", username])
    return result.returncode == 0


def create_user(username, password, domain="default", project="service"):
    result = _run_openstack_command(
        [
            "user",
            "create",
            "--domain",
            domain,
            "--project",
            project,
            "--password",
            password,
            username,
        ]
    )
    return result.returncode == 0


def create_or_check_user(username, password):
    if check_user(username):
        print(f"User '{username}' already exists")
        return

    if create_user(username, password):
        print(f"User '{username}' created successfully")
    else:
        print(f"Failed to create user '{username}'")
        sys.exit(1)


def check_and_create_service(service_name, description, service_type):
    services = _run_openstack_command(["service", "list"], check=True).stdout
    if service_name in services:
        print(f"{service_name} service already exists")
        return

    print(f"{service_name} service does not exist, creating it...")
    result = _run_openstack_command(
        [
            "service",
            "create",
            "--name",
            service_name,
            "--description",
            description,
            service_type,
        ]
    )
    if result.returncode != 0:
        print(f"{service_name} service creation failed: {result.stderr}")
        sys.exit(1)
    print(f"{service_name} service created successfully")


def endpoint_exists(service_type, endpoint_type, port, controller):
    result = _run_openstack_command(["endpoint", "list"], check=True).stdout
    expected_url = f"http://{controller}:{port}"
    return (
        service_type in result
        and endpoint_type in result
        and expected_url in result
    )


def _create_endpoint(service_type, endpoint_type, url):
    result = _run_openstack_command(
        [
            "endpoint",
            "create",
            "--region",
            "RegionOne",
            service_type,
            endpoint_type,
            url,
        ]
    )
    if result.returncode != 0:
        print("Failed to create endpoint.")
        sys.exit(1)
    print("Endpoint created successfully.")


def check_and_create_endpoint(service_type, port, controller, endpoint_type):
    if endpoint_exists(service_type, endpoint_type, port, controller):
        print("Endpoint already exists.")
        return
    _create_endpoint(service_type, endpoint_type, f"http://{controller}:{port}")


def check_and_create_endpoint_v2(service_type, port, controller, endpoint_type):
    if endpoint_exists(service_type, endpoint_type, port, controller):
        print("Endpoint already exists.")
        return
    _create_endpoint(
        service_type,
        endpoint_type,
        f"http://{controller}:{port}/v2.1/%(tenant_id)s",
    )


def check_and_create_endpoint_v3(service_type, port, controller, endpoint_type):
    if endpoint_exists(service_type, endpoint_type, port, controller):
        print("Endpoint already exists.")
        return
    _create_endpoint(
        service_type,
        endpoint_type,
        f"http://{controller}:{port}/v3/%(tenant_id)s",
    )
