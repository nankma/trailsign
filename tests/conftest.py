import pytest

from trailsign import Settings

# Mirrors docs/architecture.md's worked examples: a
# trailsign-credential-sources block whose own `type:` field equals a
# real resolver name (the exact collision shape docs/internal/design.md's
# "Fixing an ambiguity" section covers in full), plus both walkthroughs
# (news_source.gnews via environment-variable, telemetry.events via
# oracleKeyVault).
RAW_CONFIG = {
    "trailsign-credential-sources": {
        "oci-vault-main": {
            "type": "oracleKeyVault",
            "region": "us-ashburn-1",
            "vault_ocid": "ocid1.vault.oc1....",
            "compartment_ocid": "ocid1.compartment.oc1....",
        },
    },
    "models": {
        "guardrail": {
            "api-key": {
                "trailsign-resolve": "oracleKeyVault",
                "source": "oci-vault-main",
                "secret_ocid": "ocid1.vaultsecret.oc1....",
                "name": "guardrail-deepseek-key",
            },
            "url": "https://api.deepseek.com",
            "model": "deepseek-v4-flash",
        },
        "main": {
            "api-key": {"trailsign-resolve": "plaintext", "value": "sk-xxxx"},
            "url": "https://api.deepseek.com",
            "model": "deepseek-v4-flash",
        },
    },
    "news_source": {
        "bbc": {
            "type": "rss",
            "url": "https://feeds.bbci.co.uk/news/technology/rss.xml",
            "queryadoptor": "RssAdaptor",
        },
        "gnews": {
            "type": "api",
            "url": "https://gnews.io/api/v4/search",
            "api-key": {
                "trailsign-resolve": "environment-variable",
                "name": "GNEWS_API_KEY",
            },
            "queryadoptor": "GNewsAdaptor",
        },
    },
    "telemetry": {
        "events": {
            "type": "logfire",
            "api-key": {
                "trailsign-resolve": "oracleKeyVault",
                "source": "oci-vault-main",
                "secret_ocid": "ocid1.vaultsecret.oc1....",
            },
        },
    },
}


@pytest.fixture
def settings():
    return Settings(dict(RAW_CONFIG))
