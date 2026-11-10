"""Tests voor de robuustheid van het ophalen van plugin-data.

Dekt twee dingen:
1. fetchers/http_utils.py: User-Agent, timeout, retry en veilig meesturen van het GitHub-token.
2. cron.py: een mislukte fetch mag bestaande (gevulde) plugin-data nooit meer wissen.
"""
from unittest.mock import MagicMock, patch

import mongomock
import pytest
import requests

import cron
from fetchers import http_utils
from fetchers.http_utils import http_get


def _response(status=200, headers=None):
    resp = MagicMock()
    resp.status_code = status
    resp.headers = headers or {}
    return resp


@pytest.fixture(autouse=True)
def _no_sleep_and_clean_env(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GH_TOKEN", raising=False)
    with patch("fetchers.http_utils.time.sleep") as sleep:
        yield sleep


# ---------------------------------------------------------------------------
# http_get
# ---------------------------------------------------------------------------

def test_http_get_sets_user_agent_and_timeout():
    with patch("requests.get", return_value=_response()) as mock_get:
        http_get("https://api.modrinth.com/v2/project/x")
    kwargs = mock_get.call_args.kwargs
    assert kwargs["headers"]["User-Agent"] == http_utils.DEFAULT_USER_AGENT
    assert kwargs["timeout"] == http_utils.DEFAULT_TIMEOUT


def test_http_get_keeps_caller_headers_and_timeout():
    with patch("requests.get", return_value=_response()) as mock_get:
        http_get("https://example.com", headers={"user-agent": "Custom/1.0", "X-Test": "1"}, timeout=3)
    kwargs = mock_get.call_args.kwargs
    assert kwargs["headers"] == {"user-agent": "Custom/1.0", "X-Test": "1"}
    assert kwargs["timeout"] == 3


def test_http_get_retries_on_429_then_succeeds(_no_sleep_and_clean_env):
    responses = [_response(429, {"Retry-After": "2"}), _response(200)]
    with patch("requests.get", side_effect=responses) as mock_get:
        result = http_get("https://api.modrinth.com/v2/project/x")
    assert result.status_code == 200
    assert mock_get.call_count == 2
    _no_sleep_and_clean_env.assert_called_once_with(2.0)


def test_http_get_returns_last_response_when_retries_exhausted():
    responses = [_response(503) for _ in range(http_utils.MAX_ATTEMPTS)]
    with patch("requests.get", side_effect=responses) as mock_get:
        result = http_get("https://example.com")
    assert result.status_code == 503
    assert mock_get.call_count == http_utils.MAX_ATTEMPTS


def test_http_get_does_not_retry_client_errors():
    with patch("requests.get", return_value=_response(404)) as mock_get:
        result = http_get("https://example.com")
    assert result.status_code == 404
    assert mock_get.call_count == 1


def test_http_get_retries_connection_errors_then_raises():
    with patch("requests.get", side_effect=requests.exceptions.ConnectionError("boom")) as mock_get:
        with pytest.raises(requests.exceptions.ConnectionError):
            http_get("https://example.com")
    assert mock_get.call_count == http_utils.MAX_ATTEMPTS


def test_http_get_recovers_after_timeout():
    side_effect = [requests.exceptions.Timeout("slow"), _response(200)]
    with patch("requests.get", side_effect=side_effect) as mock_get:
        assert http_get("https://example.com").status_code == 200
    assert mock_get.call_count == 2


def test_github_token_only_sent_to_api_github_com(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "secret-token")
    with patch("requests.get", return_value=_response()) as mock_get:
        http_get("https://api.github.com/repos/a/b")
        assert mock_get.call_args.kwargs["headers"]["Authorization"] == "Bearer secret-token"

        http_get("https://github.com/a/b")
        assert "Authorization" not in mock_get.call_args.kwargs["headers"]

        http_get("https://api.github.com.evil.example/repos/a/b")
        assert "Authorization" not in mock_get.call_args.kwargs["headers"]

        http_get("https://api.modrinth.com/v2/project/x")
        assert "Authorization" not in mock_get.call_args.kwargs["headers"]


def test_github_token_does_not_override_caller_authorization(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "secret-token")
    with patch("requests.get", return_value=_response()) as mock_get:
        http_get("https://api.github.com/repos/a/b", headers={"Authorization": "token mine"})
    assert mock_get.call_args.kwargs["headers"]["Authorization"] == "token mine"


# ---------------------------------------------------------------------------
# cron: lege fetch-resultaten mogen bestaande data niet overschrijven
# ---------------------------------------------------------------------------

URL = "https://modrinth.com/plugin/test-plugin"

FULL_PLUGIN = {
    "url": URL,
    "owner": "owner_user",
    "title": "Test Plugin",
    "description": "Een testplugin",
    "author": "Someone",
    "icon": "https://example.com/icon.png",
    "versions": "1.20.1 1.20.4",
    "loaders": ["paper", "spigot"],
    "pinned_version": "2.0.0",
}

EMPTY_FETCH = {
    "url": URL,
    "title": "",
    "description": "",
    "author": "",
    "icon": "",
    "versions": "",
    "loaders": [],
}


@pytest.fixture
def db():
    database = mongomock.MongoClient()["cron_test"]
    database.plugins.insert_one(dict(FULL_PLUGIN))
    with patch.object(cron, "_db", database), \
            patch.object(cron, "PLUGIN_DELAY_SECONDS", 0), \
            patch.object(cron, "wait_for_connectivity", return_value=True):
        yield database


def test_has_fetched_data():
    assert not cron.has_fetched_data(EMPTY_FETCH)
    assert not cron.has_fetched_data({"title": "   ", "loaders": []})
    assert cron.has_fetched_data({**EMPTY_FETCH, "loaders": ["paper"]})


def test_merge_keeps_existing_values_for_empty_fields():
    merged = cron.merge_plugin_data(FULL_PLUGIN, {**EMPTY_FETCH, "title": "Nieuwe Titel"})
    assert merged["title"] == "Nieuwe Titel"
    assert merged["author"] == "Someone"
    assert merged["versions"] == "1.20.1 1.20.4"
    assert merged["loaders"] == ["paper", "spigot"]


def test_merge_takes_new_values_when_present():
    fetched = {**EMPTY_FETCH, "versions": "1.21", "loaders": ["paper"]}
    merged = cron.merge_plugin_data(FULL_PLUGIN, fetched)
    assert merged["versions"] == "1.21"
    assert merged["loaders"] == ["paper"]


def test_cron_cycle_keeps_data_when_every_fetcher_failed(db):
    with patch.object(cron, "update_plugin", return_value=dict(EMPTY_FETCH, owner="owner_user")):
        success = cron.run_cron_cycle()
    assert success == 0
    stored = db.plugins.find_one({"url": URL}, {"_id": 0})
    assert stored == FULL_PLUGIN


def test_cron_cycle_merges_partial_results(db):
    partial = {**EMPTY_FETCH, "owner": "owner_user", "title": "Test Plugin v2", "versions": "1.21"}
    with patch.object(cron, "update_plugin", return_value=partial):
        success = cron.run_cron_cycle()
    assert success == 1
    stored = db.plugins.find_one({"url": URL}, {"_id": 0})
    assert stored["title"] == "Test Plugin v2"
    assert stored["versions"] == "1.21"
    # niet opgehaalde velden en velden die cron niet beheert blijven intact
    assert stored["author"] == "Someone"
    assert stored["loaders"] == ["paper", "spigot"]
    assert stored["pinned_version"] == "2.0.0"


def test_no_update_notification_when_previous_version_was_unknown(db):
    db.plugins.update_one({"url": URL}, {"$set": {"versions": ""}})
    existing = db.plugins.find_one({"url": URL}, {"_id": 0})
    updated = {**EMPTY_FETCH, "owner": "owner_user", "versions": "1.21"}
    with patch.object(cron, "dispatch_discord_webhooks") as webhooks:
        cron.detect_and_record_changes(existing, updated, "owner_user")
    assert db.notifications.count_documents({}) == 0
    assert db.plugin_changes.count_documents({}) == 0
    webhooks.assert_not_called()


# ---------------------------------------------------------------------------
# Connectiviteitscheck en diagnose
# ---------------------------------------------------------------------------

def test_http_get_logs_final_failure_to_stderr(capsys):
    with patch("requests.get", side_effect=requests.exceptions.ConnectionError("dns kapot")):
        with pytest.raises(requests.exceptions.ConnectionError):
            http_get("https://api.modrinth.com/v2/project/x")
    err = capsys.readouterr().err
    assert "api.modrinth.com" in err and "ConnectionError" in err


def test_http_get_logs_blocking_status(capsys):
    with patch("requests.get", return_value=_response(403)):
        http_get("https://hangar.papermc.io/api/v1/projects/x")
    assert "hangar.papermc.io: HTTP 403" in capsys.readouterr().err


def test_http_get_does_not_log_success_or_404(capsys):
    with patch("requests.get", side_effect=[_response(200), _response(404)]):
        http_get("https://example.com/a")
        http_get("https://example.com/b")
    assert capsys.readouterr().err == ""


def test_check_connectivity_counts_any_http_response_as_reachable():
    side_effect = [
        _response(200),
        _response(403),
        requests.exceptions.ConnectionError("down"),
        requests.exceptions.Timeout("slow"),
    ]
    with patch("requests.get", side_effect=side_effect):
        reachable = cron.check_connectivity()
    assert reachable == list(cron.CONNECTIVITY_CHECK_URLS[:2])


def test_wait_for_connectivity_gives_up_after_all_attempts(_no_sleep_and_clean_env):
    with patch.object(cron, "check_connectivity", return_value=[]) as check:
        assert cron.wait_for_connectivity() is False
    assert check.call_count == cron.CONNECTIVITY_ATTEMPTS
    assert _no_sleep_and_clean_env.call_count == cron.CONNECTIVITY_ATTEMPTS - 1


def test_wait_for_connectivity_recovers_when_network_comes_up():
    with patch.object(cron, "check_connectivity", side_effect=[[], [], ["https://api.github.com/"]]) as check:
        assert cron.wait_for_connectivity() is True
    assert check.call_count == 3


def test_cron_cycle_is_skipped_when_offline():
    database = mongomock.MongoClient()["cron_offline"]
    database.plugins.insert_one(dict(FULL_PLUGIN))
    with patch.object(cron, "_db", database), \
            patch.object(cron, "wait_for_connectivity", return_value=False), \
            patch.object(cron, "update_plugin") as update:
        result = cron.run_cron_cycle()
    assert result is None
    update.assert_not_called()
    assert database.plugins.find_one({"url": URL}, {"_id": 0}) == FULL_PLUGIN
    # een overgeslagen cyclus mag niet als geslaagde fetch geregistreerd worden
    assert database.settings.count_documents({}) == 0


def test_launcher_forwards_fetcher_stderr(capsys):
    import subprocess
    import launcher
    completed = subprocess.CompletedProcess(args=[], returncode=0, stdout="[]", stderr="[http_get] x: HTTP 403")
    with patch("launcher.subprocess.run", return_value=completed):
        assert launcher.run_script("loaders", "https://example.com") == "[]"
    assert "[loaders] [http_get] x: HTTP 403" in capsys.readouterr().err
