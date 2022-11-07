from __future__ import annotations  # because of ConfirmGenerator circular dependency

from typing import Callable
from pathlib import Path

import click
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap

from ..backends.confirm import ConfirmBackend


def user_input(*args, **kwargs):
    choice_map = kwargs.pop("choice_map", None)

    def outer(fn: Callable):
        key = fn.__name__.removeprefix("gen_")

        def inner(self: ConfirmGenerator):
            if self.config[key]:
                if not self.update_all:
                    return
                else:
                    kwargs["default"] = self.config[key]
            if choice_map and "default" not in kwargs:
                kwargs["show_choices"] = True
                kwargs["type"] = click.Choice(list(choice_map.keys()))
                self.config[key] = choice_map[click.prompt(*args, **kwargs)]
            else:
                self.config[key] = click.prompt(*args, **kwargs)

        return inner

    return outer


class ConfirmGenerator:
    cfg_path: Path
    yaml: YAML
    config: CommentedMap
    update_all = False

    def __init__(self, cfg_path: Path, update_all: bool):
        self.cfg_path = cfg_path
        self.update_all = update_all

    def run(self):
        self.yaml = YAML()
        with self.cfg_path.open() as f:
            self.config = self.yaml.load(f)

        for key in self.config:
            fn = f"gen_{key}"
            if hasattr(self, fn):
                getattr(self, fn)()

        with self.cfg_path.open("w") as f:
            self.yaml.dump(self.config, f)

    @user_input("Password")
    def gen_password(self):
        pass

    @user_input("Username")
    def gen_username(self):
        pass

    @user_input("Tenant/database ID")
    def gen_tenant_id(self):
        pass

    @user_input("Server timezone")
    def gen_server_timezone(self):
        pass

    @user_input(
        "Confirm environment",
        choice_map={
            "development": "https://development-webservices.ondemand.confirm.co.uk/confirm/connector/confirmconnector.asmx",
            "production": "https://production-webservices.ondemand.confirm.co.uk/confirm/connector/confirmconnector.asmx",
        },
    )
    def gen_endpoint_url(self):
        pass
