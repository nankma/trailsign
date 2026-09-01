"""Trailsign: resolves a declarative, self-describing config into plain
values. See docs/design.md at the repo root for the full design."""

from .settings import (
    RESOLVE_KEY,
    EnvironmentVariableResolver,
    OracleKeyVaultResolver,
    PlaintextResolver,
    Settings,
    SettingsError,
    SettingsResolver,
    default_resolvers,
)

__all__ = [
    "RESOLVE_KEY",
    "EnvironmentVariableResolver",
    "OracleKeyVaultResolver",
    "PlaintextResolver",
    "Settings",
    "SettingsError",
    "SettingsResolver",
    "default_resolvers",
]
