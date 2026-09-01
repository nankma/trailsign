import pytest

from trailsign import SettingsError


def test_validate_passes_when_all_required_paths_resolve(settings, monkeypatch):
    monkeypatch.setenv("GNEWS_API_KEY", "the-real-key")
    settings.validate(["models.main.api-key", "news_source.gnews.api-key"])


def test_validate_combines_all_errors_into_one_exception(settings, monkeypatch):
    """validate() is the eager, fail-together path -- it should report every
    unresolvable required path in one SettingsError, not stop at the
    first failure (that's the whole point vs. plain resolved(required=True),
    which does fail fast per-call)."""
    monkeypatch.delenv("GNEWS_API_KEY", raising=False)
    with pytest.raises(SettingsError) as exc_info:
        settings.validate(
            [
                "models.main.api-key",  # resolves fine
                "news_source.gnews.api-key",  # env var unset -- fails
                "no.such.path",  # missing entirely -- fails
            ]
        )
    message = str(exc_info.value)
    assert "GNEWS_API_KEY" in message
    assert "no.such.path" in message


def test_resolved_required_true_fails_fast_on_first_missing_path(settings):
    """Contrast with validate(): a single resolved(..., required=True) call
    raises immediately for its own path, with no aggregation -- that's
    validate()'s job, not resolved()'s."""
    with pytest.raises(SettingsError, match="no.such.path"):
        settings.resolved("no.such.path", required=True)
