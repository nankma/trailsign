import pytest

from trailsign import SettingsError


def test_resolved_walks_nested_dict_recursively(settings, monkeypatch):
    monkeypatch.setenv("GNEWS_API_KEY", "the-real-key")
    result = settings.resolved("news_source.gnews")
    assert result == {
        "type": "api",
        "url": "https://gnews.io/api/v4/search",
        "api-key": "the-real-key",
        "queryadoptor": "GNewsAdaptor",
    }


def test_resolved_leaves_plain_scalars_untouched(settings):
    result = settings.resolved("news_source.bbc")
    assert result == {
        "type": "rss",
        "url": "https://feeds.bbci.co.uk/news/technology/rss.xml",
        "queryadoptor": "RssAdaptor",
    }


def test_resolved_plaintext_node(settings):
    result = settings.resolved("models.main")
    assert result["api-key"] == "sk-xxxx"
    assert result["url"] == "https://api.deepseek.com"


def test_resolved_missing_path_returns_default(settings):
    assert settings.resolved("no.such.path", default="fallback") == "fallback"
    assert settings.resolved("no.such.path") is None


def test_resolved_missing_required_path_raises(settings):
    with pytest.raises(SettingsError, match="no.such.path"):
        settings.resolved("no.such.path", required=True)


def test_resolved_unregistered_resolver_raises(settings):
    settings._raw["broken"] = {"trailsign-resolve": "no-such-resolver"}
    with pytest.raises(SettingsError, match="no-such-resolver"):
        settings.resolved("broken")


def test_dispatch_key_does_not_collide_with_type_field(settings):
    """Regression test for docs/internal/design.md's 'Fixing an ambiguity'
    section (private submodule; full collision history there):
    trailsign-credential-sources.oci-vault-main.type == 'oracleKeyVault'
    (a plain connection-definition field) must NOT be treated as a
    trailsign-resolve dispatch, even though its value equals a real
    resolver name -- only the presence of the `trailsign-resolve` key
    itself triggers dispatch, never a subsystem's own `type:` field."""
    result = settings.resolved("trailsign-credential-sources.oci-vault-main")
    assert result == {
        "type": "oracleKeyVault",
        "region": "us-ashburn-1",
        "vault_ocid": "ocid1.vault.oc1....",
        "compartment_ocid": "ocid1.compartment.oc1....",
    }


def test_dispatch_key_does_not_collide_with_subsystem_type_field(settings, monkeypatch):
    """Same regression, other direction: telemetry.events.type == 'logfire'
    is a consumer discriminator with no trailsign-resolve key and must
    survive resolution unchanged, alongside a sibling api-key node that
    genuinely does dispatch."""

    def fake_oracle_resolve(node, settings):
        return "the-real-secret"

    monkeypatch.setattr(
        settings._resolvers["oracleKeyVault"], "resolve", fake_oracle_resolve
    )
    result = settings.resolved("telemetry.events")
    assert result == {"type": "logfire", "api-key": "the-real-secret"}
