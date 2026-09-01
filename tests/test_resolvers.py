import sys
import types
from unittest.mock import MagicMock

import pytest

from trailsign import (
    EnvironmentVariableResolver,
    OracleKeyVaultResolver,
    PlaintextResolver,
    Settings,
    SettingsError,
)
from trailsign.settings import _oci_config_from


def test_plaintext_resolver_returns_value_field():
    resolver = PlaintextResolver()
    node = {"trailsign-resolve": "plaintext", "value": "sk-xxxx"}
    assert resolver.resolve(node, settings=None) == "sk-xxxx"


def test_plaintext_resolver_missing_value_field_raises():
    resolver = PlaintextResolver()
    with pytest.raises(SettingsError, match="value"):
        resolver.resolve({"trailsign-resolve": "plaintext"}, settings=None)


def test_environment_variable_resolver_reads_process_environment(monkeypatch):
    monkeypatch.setenv("GNEWS_API_KEY", "the-real-key")
    resolver = EnvironmentVariableResolver()
    node = {"trailsign-resolve": "environment-variable", "name": "GNEWS_API_KEY"}
    assert resolver.resolve(node, settings=None) == "the-real-key"


def test_environment_variable_resolver_missing_name_field_raises():
    resolver = EnvironmentVariableResolver()
    with pytest.raises(SettingsError, match="name"):
        resolver.resolve({"trailsign-resolve": "environment-variable"}, settings=None)


def test_environment_variable_resolver_unset_variable_raises(monkeypatch):
    monkeypatch.delenv("SOME_UNSET_VAR", raising=False)
    resolver = EnvironmentVariableResolver()
    node = {"trailsign-resolve": "environment-variable", "name": "SOME_UNSET_VAR"}
    with pytest.raises(SettingsError, match="SOME_UNSET_VAR"):
        resolver.resolve(node, settings=None)


def test_oracle_key_vault_resolver_missing_secret_ocid_raises(settings):
    resolver = OracleKeyVaultResolver()
    node = {"trailsign-resolve": "oracleKeyVault", "source": "oci-vault-main"}
    with pytest.raises(SettingsError, match="secret_ocid"):
        resolver.resolve(node, settings)


def test_oracle_key_vault_resolver_unknown_source_raises(settings):
    resolver = OracleKeyVaultResolver()
    node = {
        "trailsign-resolve": "oracleKeyVault",
        "source": "no-such-source",
        "secret_ocid": "ocid1.vaultsecret.oc1....",
    }
    with pytest.raises(SettingsError, match="no-such-source"):
        resolver.resolve(node, settings)


def test_oci_config_from_is_still_a_stub():
    with pytest.raises(NotImplementedError):
        _oci_config_from({"type": "oracleKeyVault"})


def test_oracle_key_vault_resolver_happy_path_with_mocked_oci(settings, monkeypatch):
    """`import oci` happens lazily inside resolve() -- inject a fake module
    into sys.modules rather than requiring the real oci SDK to be
    installed. `_oci_config_from` is stubbed for now (see docs/design.md's
    'Still open' section), so it's patched here to isolate this test from
    that undecided auth shape."""
    fake_secret_bundle = MagicMock()
    fake_secret_bundle.data.secret_bundle_content.content = "ZmFrZS1zZWNyZXQ="

    fake_secrets_client_cls = MagicMock(return_value=MagicMock(get_secret_bundle=MagicMock(return_value=fake_secret_bundle)))

    fake_oci = types.ModuleType("oci")
    fake_oci.secrets = types.SimpleNamespace(SecretsClient=fake_secrets_client_cls)
    monkeypatch.setitem(sys.modules, "oci", fake_oci)
    monkeypatch.setattr("trailsign.settings._oci_config_from", lambda source: {})

    resolver = OracleKeyVaultResolver()
    node = {
        "trailsign-resolve": "oracleKeyVault",
        "source": "oci-vault-main",
        "secret_ocid": "ocid1.vaultsecret.oc1....",
    }
    result = resolver.resolve(node, settings)
    assert result == "ZmFrZS1zZWNyZXQ="
    fake_secrets_client_cls.return_value.get_secret_bundle.assert_called_once_with("ocid1.vaultsecret.oc1....")
