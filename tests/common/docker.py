# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2022 Scitacean contributors (https://github.com/SciCatProject/scitacean)
# @author Jan-Lukas Wynen
# flake8: noqa
import subprocess
from contextlib import contextmanager
from pathlib import Path


def docker_compose_up(config_file: Path, *services: str):
    subprocess.check_call(
        [
            "docker",
            "compose",
            "--file",
            str(config_file),
            "up",
            "--detach",
            "--force-recreate",
            *services,
        ]
    )


def docker_compose_down(config_file: Path):
    subprocess.check_call(
        ["docker", "compose", "--file", str(config_file), "down", "--volumes"]
    )


@contextmanager
def docker_compose(config_file: Path, *services: str):
    docker_compose_up(config_file, *services)
    try:
        yield
    finally:
        docker_compose_down(config_file)
