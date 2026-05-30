#!/usr/bin/python3
# -*- coding: utf-8 -*-

import argparse
import importlib
import sys

from script.lib.runtime import ensure_root
from script.lib.runtime import get_logger
from script.lib.runtime import print_error
from script.lib.runtime import print_success
from script.lib.runtime import validate_config


logger = get_logger("main")

STEP_REGISTRY = [
    ("system", "Configure System Environment", "script.sys_init", "function_base_init"),
    ("db-mq", "Install MariaDB and RabbitMQ", "script.db_mq_init", "function_db_mq_init"),
    ("keystone", "Install Keystone", "script.keystone_init", "function_keystone_init"),
    ("glance", "Install Glance", "script.glance_init", "function_glance_init"),
    ("nova", "Install Nova", "script.nova_init", "function_nova_init"),
    ("cinder", "Install Cinder", "script.cinder_init", "function_cinder_init"),
    ("neutron", "Install Neutron", "script.neutron_init", "function_neutron_init"),
    ("horizon", "Install Dashboard", "script.horizon_init", "function_horizon_init"),
]


def list_steps():
    for index, (step_id, description, _, _) in enumerate(STEP_REGISTRY, start=1):
        print(f"{index}. {step_id:<8} {description}")


def load_action(module_name, function_name):
    module = importlib.import_module(module_name)
    return getattr(module, function_name)


def run_step(step_ref):
    step_ref = str(step_ref).strip().lower()
    for index, (step_id, description, module_name, function_name) in enumerate(STEP_REGISTRY, start=1):
        if step_ref in {str(index), step_id}:
            print_success(f"Running step {index}: {description}")
            logger.info("Running step %s (%s)", index, step_id)
            action = load_action(module_name, function_name)
            action()
            return

    raise ValueError(f"Unknown step: {step_ref}")


def run_all_steps():
    for index, (step_id, description, module_name, function_name) in enumerate(STEP_REGISTRY, start=1):
        print_success(f"[{index}/{len(STEP_REGISTRY)}] {description}")
        logger.info("Running step %s (%s)", index, step_id)
        action = load_action(module_name, function_name)
        action()


def print_menu():
    print("\nOpenStack Deployment Menu")
    print("-------------------------")
    for index, (_, description, _, _) in enumerate(STEP_REGISTRY, start=1):
        print(f"{index}) {description}")
    print("9) Validate Configuration")
    print("a) Run All Steps")
    print("l) List Step IDs")
    print("0) Quit")


def interactive_menu():
    while True:
        print_menu()
        choice = input("Please choose a step: ").strip().lower()

        if choice == "0":
            return
        if choice == "9":
            details = validate_config()
            print_success(f"Configuration validation passed: {details['config_path']}")
            continue
        if choice == "a":
            run_all_steps()
            continue
        if choice == "l":
            list_steps()
            continue

        try:
            run_step(choice)
        except ValueError as exc:
            print_error(str(exc))


def build_parser():
    parser = argparse.ArgumentParser(
        description="Single-node OpenStack Antelope deployment helper."
    )
    parser.add_argument(
        "--step",
        help="Run a single step by number or ID, for example: 3 or keystone.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all deployment steps in order.",
    )
    parser.add_argument(
        "--list-steps",
        action="store_true",
        help="List available deployment step IDs.",
    )
    parser.add_argument(
        "--validate-config",
        action="store_true",
        help="Validate config/config.ini and related files before deployment.",
    )
    parser.add_argument(
        "--skip-root-check",
        action="store_true",
        help="Skip the root privilege check. Useful for dry runs like --list-steps.",
    )
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.skip_root_check and not args.list_steps:
        ensure_root()

    if args.list_steps:
        list_steps()
        return

    if args.validate_config:
        details = validate_config()
        print_success(f"Configuration validation passed: {details['config_path']}")
        if not args.step and not args.all:
            return

    if args.step:
        run_step(args.step)
        return

    if args.all:
        run_all_steps()
        return

    interactive_menu()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_error("Interrupted by user.")
        sys.exit(130)
    except Exception as exc:
        logger.exception("Deployment failed: %s", exc)
        print_error(f"Deployment failed: {exc}")
        sys.exit(1)
