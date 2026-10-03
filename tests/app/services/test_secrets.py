"""Unit tests for app.services.secrets.get_secret.

Covers: cache miss -> fetch + parse + cache; cache hit within TTL; expired
cache triggers re-fetch; ClientError wrapped; JSON parse error wrapped.

The module keeps a module-level _cache dict; the autouse fixture clears it
before each test so tests are isolated.
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from app.services import secrets as mod


@pytest.fixture(autouse=True)
def clear_cache():
    mod._cache.clear()
    yield
    mod._cache.clear()


def _mock_client(secret_string: str):
    client = MagicMock()
    client.get_secret_value.return_value = {"SecretString": secret_string}
    return client


class TestGetSecret:
    def test_fetch_parse_and_cache(self):
        client = _mock_client(json.dumps({"api_key": "xyz"}))
        with patch.object(mod.boto3, "client", return_value=client):
            result = mod.get_secret("my-secret")
        assert result == {"api_key": "xyz"}
        client.get_secret_value.assert_called_once_with(SecretId="my-secret")
        assert mod._cache["my-secret"]["data"] == {"api_key": "xyz"}

    def test_cache_hit_skips_fetch(self):
        client = _mock_client(json.dumps({"v": 1}))
        with patch.object(mod.boto3, "client", return_value=client):
            mod.get_secret("s")
            # Second call should hit cache; boto3.client not needed again.
            result = mod.get_secret("s")
        assert result == {"v": 1}
        assert client.get_secret_value.call_count == 1

    def test_expired_cache_refetches(self):
        client = _mock_client(json.dumps({"v": 2}))
        with patch.object(mod.boto3, "client", return_value=client):
            mod.get_secret("s")
            # Force the cached timestamp beyond the TTL window.
            mod._cache["s"]["ts"] -= (mod._CACHE_TTL + 1)
            mod.get_secret("s")
        assert client.get_secret_value.call_count == 2

    def test_client_error_wrapped(self):
        client = MagicMock()
        client.get_secret_value.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "no"}}, "GetSecretValue"
        )
        with patch.object(mod.boto3, "client", return_value=client):
            with pytest.raises(Exception) as exc:
                mod.get_secret("s")
        assert "Failed to retrieve secret s" in str(exc.value)

    def test_json_decode_error_wrapped(self):
        client = _mock_client("not-json{")
        with patch.object(mod.boto3, "client", return_value=client):
            with pytest.raises(Exception) as exc:
                mod.get_secret("s")
        assert "Failed to parse secret s as JSON" in str(exc.value)
