#!/usr/bin/python3
# -*- coding: utf-8 -*-

import configparser
import logging
import os
import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT_DIR / "config" / "config.ini"

_CONFIG = None
_LOGGER_CACHE = {}


class CommandError(RuntimeError):
    """Raised when a shell command exits with a non-zero code."""


def get_config():
    global _CONFIG
    if _CONFIG is None:
        config = configparser.ConfigParser()
        read_files = config.read(CONFIG_PATH)
        if not read_files:
            raise FileNotFoundError(f"Config file not found: {CONFIG_PATH}")
        _CONFIG = config
    return _CONFIG


def get_log_path():
    return get_config().get("LOG", "LOG_DIR")


def load_openstack_env():
    env = os.environ.copy()
    rc_path = "/root/keystonerc"
    if not os.path.exists(rc_path):
        return env

    with open(rc_path, "r", encoding="utf-8") as rc_file:
        for raw_line in rc_file:
            line = raw_line.strip()
            if not line or line.startswith("#") or not line.startswith("export "):
                continue
            key, _, value = line[len("export "):].partition("=")
            env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def get_logger(name):
    if name in _LOGGER_CACHE:
        return _LOGGER_CACHE[name]

    logger = logging.getLogger(name)
    if logger.handlers:
        _LOGGER_CACHE[name] = logger
        return logger

    logger.setLevel(logging.DEBUG)
    log_path = get_log_path()
    log_dir = os.path.dirname(log_path)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    try:
        handler = logging.FileHandler(log_path)
    except PermissionError:
        fallback_path = ROOT_DIR / "openstack.log"
        handler = logging.FileHandler(fallback_path)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s",
            datefmt="%a-%d-%b %Y %H:%M:%S",
        )
    )
    logger.addHandler(handler)
    logger.propagate = False
    _LOGGER_CACHE[name] = logger
    return logger


def print_success(message):
    print(f"\033[32m {message} \033[0m")


def print_error(message):
    print(f"\033[41;37m {message} \033[0m")


def run_command(command, logger=None, exit_on_error=True, check=False):
    logger = logger or get_logger("deploy-openstack")
    result = subprocess.run(
        command,
        shell=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        env=load_openstack_env(),
    )

    if result.stdout:
        print(result.stdout, end="")
    if result.returncode == 0:
        print_success(f"{command} success")
        logger.info("%s success", command)
        return result

    if result.stderr:
        print(result.stderr, end="")
    print_error(f"{command} failed")
    logger.error("%s failed", command)
    if check or exit_on_error:
        raise CommandError(command)
    return result


def ensure_root():
    if os.geteuid() != 0:
        raise PermissionError("This script must be run as root.")


def validate_config():
    config = get_config()
    required_items = {
        "CONTROLLER": ["HOST_NAME", "MANAGER_IP", "ALL_PASSWORD", "NET_DEVICE_NAME"],
        "FLOATING_METWORK_ADDR": ["NEUTRON_PUBLIC_NET", "PUBLIC_NET_GW", "NEUTRON_DNS"],
        "VOLUME": ["CINDER_DISK"],
        "LOG": ["LOG_DIR"],
    }

    errors = []
    for section, keys in required_items.items():
        if not config.has_section(section):
            errors.append(f"Missing section [{section}]")
            continue
        for key in keys:
            value = config.get(section, key, fallback="").strip()
            if not value:
                errors.append(f"Missing value: [{section}] {key}")

    hosts_path = ROOT_DIR / "config" / "hosts"
    if not hosts_path.exists():
        errors.append(f"Missing file: {hosts_path}")

    if errors:
        raise ValueError("\n".join(errors))

    return {
        "config_path": str(CONFIG_PATH),
        "hosts_path": str(hosts_path),
        "log_path": get_log_path(),
    }


def safe_exit(message, code=1):
    print_error(message)
    sys.exit(code)
