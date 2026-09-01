"""Trailsign: resolves a declarative, self-describing config into plain
values.

Each value in the config declares its own source instead of the caller
assuming where to look -- a plain scalar, an environment variable, and a
vault secret are all just different `trailsign-resolve:` nodes resolved
the same way. `trailsign-resolve:` is a reserved, namespaced key --
never a bare word like `resolve` -- so it can never collide with a
consuming project's own field names. See docs/design.md for the full
design (data flow, diagrams, and why `trailsign-resolve:` has to be a
dedicated key rather than reusing a subsystem's own `type:`-style
discriminator).

A reference implementation in Python, packaged and tested. Extracted
2026-09-01 from a Telegram news-trend bot's settings work -- the design
turned out to be genuinely content-independent, so it lives here as its
own project now.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Protocol

import yaml

RESOLVE_KEY = "trailsign-resolve"


class SettingsError(Exception):
    """A setting couldn't be resolved -- missing path, a
    `trailsign-resolve:` value naming an unregistered resolver, a
    resolver's own required field absent, or (from validate()) one or
    more required paths unresolvable. The message names exactly which."""


class SettingsResolver(Protocol):
    """Resolves one typed-value node ({"trailsign-resolve": <this
    resolver's own name>, ...}) to a plain value. One implementation per
    resolver name; a new source (AWS Secrets Manager, Azure Key Vault,
    ...) is a new class registered by name, never a change to Settings
    itself."""

    def resolve(self, node: dict[str, Any], settings: "Settings") -> Any: ...


class PlaintextResolver:
    def resolve(self, node: dict[str, Any], settings: "Settings") -> Any:
        try:
            return node["value"]
        except KeyError:
            raise SettingsError("plaintext value missing its 'value' field") from None


class EnvironmentVariableResolver:
    def resolve(self, node: dict[str, Any], settings: "Settings") -> Any:
        name = node.get("name")
        if not name:
            raise SettingsError("environment-variable value missing its 'name' field")
        try:
            return os.environ[name]
        except KeyError:
            raise SettingsError(f"environment variable {name!r} is not set") from None


class OracleKeyVaultResolver:
    """The only resolver allowed to import a cloud SDK -- lazily, so a
    consumer with no oracleKeyVault nodes in their config never needs
    the `oci` package installed at all."""

    def resolve(self, node: dict[str, Any], settings: "Settings") -> Any:
        source = settings.get_credential_source(node["source"])
        secret_ocid = node.get("secret_ocid")
        if not secret_ocid:
            raise SettingsError("oracleKeyVault value missing its 'secret_ocid' field")

        import oci  # local import -- see class docstring

        client = oci.secrets.SecretsClient(_oci_config_from(source))
        response = client.get_secret_bundle(secret_ocid)
        return response.data.secret_bundle_content.content  # base64; decode as needed


def _oci_config_from(source: dict[str, Any]) -> dict[str, Any]:
    """Placeholder -- exact OCI auth shape (config file vs. instance
    principal vs. explicit key) not pinned down yet; see docs/design.md's
    'Still open' section."""
    raise NotImplementedError


def default_resolvers() -> dict[str, SettingsResolver]:
    return {
        "plaintext": PlaintextResolver(),
        "environment-variable": EnvironmentVariableResolver(),
        "oracleKeyVault": OracleKeyVaultResolver(),
    }


class Settings:
    def __init__(self, raw: dict[str, Any], resolvers: dict[str, SettingsResolver] | None = None):
        self._raw = raw
        self._resolvers = resolvers if resolvers is not None else default_resolvers()

    @classmethod
    def from_yaml(cls, path: str | Path, resolvers: dict[str, SettingsResolver] | None = None) -> "Settings":
        with open(path, encoding="utf-8") as f:
            raw = yaml.safe_load(f)
        return cls(raw, resolvers)

    def resolved(self, path: str, default: Any = None, required: bool = False) -> Any:
        """path is dotted, e.g. "news_source.gnews" or "models.main.api-key".
        Returns the node at that path with every {"trailsign-resolve":
        <name>, ...} descendant replaced by its resolved value -- plain
        dicts/lists/scalars for everything else, unchanged."""
        node = self._raw
        for part in path.split("."):
            if not isinstance(node, dict) or part not in node:
                if required:
                    raise SettingsError(f"required setting {path!r} is not present")
                return default
            node = node[part]
        return self._resolve_node(node)

    def get_credential_source(self, name: str) -> dict[str, Any]:
        """Looked up by resolvers that need a named, reusable connection
        block (see oracleKeyVault's `source:` field) -- not meant to be
        called by ordinary settings consumers."""
        try:
            return self._raw["credential_sources"][name]
        except KeyError:
            raise SettingsError(f"no credential_sources entry named {name!r}") from None

    def validate(self, required_paths: list[str]) -> None:
        """Resolve every path up front and fail with ONE error listing
        everything unresolvable, instead of the process starting,
        looking healthy, and dying on first use of a missing key. A
        consuming project's entry point should call this with its own
        required-key list before doing anything else."""
        errors = []
        for path in required_paths:
            try:
                self.resolved(path, required=True)
            except SettingsError as exc:
                errors.append(str(exc))
        if errors:
            raise SettingsError("missing/invalid settings:\n  " + "\n  ".join(errors))

    def _resolve_node(self, node: Any) -> Any:
        """A dict is a resolvable value iff it carries the reserved
        RESOLVE_KEY -- purely structural, independent of what resolvers
        happen to be registered or what any subsystem's own
        `type:`-style discriminator fields happen to say. A
        `trailsign-resolve` value naming an unregistered resolver is an
        error, not a silent pass-through -- once a node declares intent
        to be resolved, an unrecognized target should never resolve to
        itself unresolved."""
        if isinstance(node, dict):
            if RESOLVE_KEY in node:
                name = node[RESOLVE_KEY]
                resolver = self._resolvers.get(name)
                if resolver is None:
                    raise SettingsError(f"no resolver registered for '{RESOLVE_KEY}: {name}'")
                return resolver.resolve(node, self)
            return {k: self._resolve_node(v) for k, v in node.items()}
        if isinstance(node, list):
            return [self._resolve_node(v) for v in node]
        return node
