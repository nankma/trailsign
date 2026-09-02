"""Trailsign: resolves a declarative, self-describing config into plain
values. See docs/architecture.md at the repo root for the full design."""

from .settings import (
    CREDENTIAL_SOURCES_KEY,
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
    "CREDENTIAL_SOURCES_KEY",
    "RESOLVE_KEY",
    "EnvironmentVariableResolver",
    "OracleKeyVaultResolver",
    "PlaintextResolver",
    "Settings",
    "SettingsError",
    "SettingsResolver",
    "default_resolvers",
]
