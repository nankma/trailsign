import pytest

from trailsign import SettingsError


def test_get_credential_source_returns_named_block(settings):
    source = settings.get_credential_source("oci-vault-main")
    assert source["type"] == "oracleKeyVault"
    assert source["region"] == "us-ashburn-1"


def test_get_credential_source_unknown_name_raises(settings):
    with pytest.raises(SettingsError, match="no-such-source"):
        settings.get_credential_source("no-such-source")
