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
from trailsign.settings import _oci_secrets_client


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


def _install_fake_oci(monkeypatch, secret_bundle_b64: str) -> MagicMock:
    """Injects a fake `oci` module into sys.modules -- `import oci` happens
    lazily inside `_oci_secrets_client()`, so this isolates the test from
    needing the real SDK (or a real OCI instance-metadata service, which
    `InstancePrincipalsSecurityTokenSigner()` would otherwise require)."""
    fake_secret_bundle = MagicMock()
    fake_secret_bundle.data.secret_bundle_content.content = secret_bundle_b64

    fake_secrets_client_cls = MagicMock(
        return_value=MagicMock(get_secret_bundle=MagicMock(return_value=fake_secret_bundle))
    )
    fake_signer_cls = MagicMock()

    fake_oci = types.ModuleType("oci")
    fake_oci.secrets = types.SimpleNamespace(SecretsClient=fake_secrets_client_cls)
    fake_oci.auth = types.SimpleNamespace(
        signers=types.SimpleNamespace(InstancePrincipalsSecurityTokenSigner=fake_signer_cls)
    )
    monkeypatch.setitem(sys.modules, "oci", fake_oci)
    return fake_secrets_client_cls


def test_oci_secrets_client_uses_instance_principal_auth(monkeypatch):
    """Regression test for the real auth-shape bug found while verifying
    against a live OCI Vault secret: the SDK call must be
    `SecretsClient(config={}, signer=<InstancePrincipalsSecurityTokenSigner
    instance>)`, not a populated config dict with no signer -- that's the
    shape this project's real deployed secret fetches actually use."""
    fake_secrets_client_cls = _install_fake_oci(monkeypatch, "ZmFrZS1zZWNyZXQ=")
    _oci_secrets_client()
    _, kwargs = fake_secrets_client_cls.call_args
    assert kwargs["config"] == {}
    assert kwargs["signer"] is not None


def test_oracle_key_vault_resolver_happy_path_with_mocked_oci(settings, monkeypatch):
    """"ZmFrZS1zZWNyZXQ=" is "fake-secret" base64-encoded -- the resolver is
    expected to hand back the decoded plain string, same contract as
    every other resolver, not the base64 wire format."""
    fake_secrets_client_cls = _install_fake_oci(monkeypatch, "ZmFrZS1zZWNyZXQ=")

    resolver = OracleKeyVaultResolver()
    node = {
        "trailsign-resolve": "oracleKeyVault",
        "source": "oci-vault-main",
        "secret_ocid": "ocid1.vaultsecret.oc1....",
    }
    result = resolver.resolve(node, settings)
    assert result == "fake-secret"
    fake_secrets_client_cls.return_value.get_secret_bundle.assert_called_once_with("ocid1.vaultsecret.oc1....")
