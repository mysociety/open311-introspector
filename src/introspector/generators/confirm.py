from __future__ import annotations  # because of ConfirmGenerator circular dependency

from typing import Callable
from pathlib import Path

import click
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap
from ruamel.yaml.tokens import CommentToken

from ..backends.confirm import ConfirmBackend, ConfirmError


def user_input(*args, **kwargs):
    choice_map = kwargs.pop("choice_map", None)

    def outer(fn: Callable):
        key = fn.__name__.removeprefix("gen_")

        def inner(self: ConfirmGenerator):
            val = self.config[key]
            if val:
                if not self.update_all:
                    return
                elif val:
                    kwargs["default"] = val
            if comment := self._comment_for_key(key):
                click.echo(f"\n{comment}")
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
    backend: ConfirmBackend
    update_all = False

    def __init__(self, cfg_path: Path, update_all: bool):
        self.cfg_path = cfg_path
        self.update_all = update_all

    def run(self):
        self.yaml = YAML()
        with self.cfg_path.open() as f:
            self.config = self.yaml.load(f)

        self.backend = ConfirmBackend(self.config)

        for key in self.config:
            fn = f"gen_{key}"
            if hasattr(self, fn):
                getattr(self, fn)()

        with self.cfg_path.open("w") as f:
            self.yaml.dump(self.config, f)
        click.echo(
            f"All done. Copy the following file to your open311-adapter installation and check it works:\n\n\t{self.cfg_path}"
        )

    def _comment_for_key(self, key):
        if not hasattr(self.config, "ca"):
            return
        if key in self.config.ca.items:
            lines = []
            for token in (t for t in self.config.ca.items[key] if t):
                if isinstance(token, CommentToken):
                    lines.append(token.value.strip())
                else:
                    lines.extend(t.value.strip() for t in token)
            return "\n".join(lines).strip()

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

    @user_input("Default site code", default="")
    def gen_default_site_code(self):
        pass

    def gen_reverse_status_mapping(self):
        mapping = self.config["reverse_status_mapping"]
        if mapping and not self.update_all:
            return

        if codes := self.config["reverse_status_mapping"].keys():
            default = ",".join(sorted(codes))
        else:
            default = ""

        allowed = click.prompt(
            "\nIf you only want to allow certain status codes,"
            " enter them as a comma-separated (no spaces between) list now",
            value_proc=lambda i: set(v.upper() for v in i.split(",")) if i else set(),
            default=default,
        )

        for code, name, outstanding, _ in self.backend.get_status_codes():
            if allowed and code not in allowed:
                continue
            if code not in mapping:  # don't clobber any manual edits
                mapping[code] = "open" if outstanding else "closed"
            mapping.yaml_add_eol_comment(name, code, column=0)

    def gen_enquiry_method_code(self):
        if self.config["enquiry_method_code"] and not self.update_all:
            return
        methods = self.backend.get_enquiry_methods()
        if comment := self._comment_for_key("enquiry_method_code"):
            click.echo(f"\n{comment}")
        click.echo("\n".join([f"{code}: {name}" for code, name in methods]))
        self.config["enquiry_method_code"] = click.prompt(
            "Enquiry method code",
            type=click.Choice([code for code, _ in methods] + [""]),
            default=self.config.get("enquiry_method_code", ""),
        )

    def gen_customer_type_code(self):
        if self.config["customer_type_code"] and not self.update_all:
            return
        methods = self.backend.get_customer_types()
        if comment := self._comment_for_key("customer_type_code"):
            click.echo(f"\n{comment}")
        click.echo("\n".join([f"{code}: {name}" for code, name in methods]))
        self.config["customer_type_code"] = click.prompt(
            "Customer type code",
            type=click.Choice([code for code, _ in methods] + [""]),
            default=self.config.get("customer_type_code", ""),
        )

    def gen_point_of_contact_code(self):
        if self.config["point_of_contact_code"] and not self.update_all:
            return
        methods = self.backend.get_point_of_contact_codes()
        if comment := self._comment_for_key("point_of_contact_code"):
            click.echo(f"\n{comment}")
        click.echo("\n".join([f"{code}: {name}" for code, name in methods]))
        self.config["point_of_contact_code"] = click.prompt(
            "Point of contact code",
            type=click.Choice([code for code, _ in methods] + [""]),
            default=self.config.get("point_of_contact_code", ""),
        )

    def gen_service_whitelist(self):
        if self.config["service_whitelist"] and not self.update_all:
            return

        try:
            backend_service_subject_codes = self.backend.get_service_subject_codes()
            click.echo("\nConfirm credentials are OK, connected to API successfully.\n")
        except ConfirmError as e:
            raise click.ClickException(str(e))

        if groups := self.config["service_whitelist"].values():
            subject_codes = {v.split("_")[1] for g in groups for v in g.keys()}
            default = ",".join(sorted(subject_codes))
        else:
            default = ""

        allowed = click.prompt(
            "\nIf you only want to allow certain subject codes,"
            " enter them as a comma-separated (no spaces between) list now",
            value_proc=lambda i: set(v.upper() for v in i.split(",")) if i else set(),
            default=default,
        )

        services = {}

        for code, name, scode, sname in backend_service_subject_codes:
            if allowed and scode not in allowed:
                continue
            o311_code = f"{code}_{scode}"
            services.setdefault(name, {})[o311_code] = sname

        self.config["service_whitelist"] = services
