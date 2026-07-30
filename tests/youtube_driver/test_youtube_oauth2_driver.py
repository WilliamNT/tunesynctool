import json
import os
import sys

from googleapiclient.errors import HttpError

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "webui"))

from api.drivers.youtube.driver import YouTubeOAuth2Driver
from tunesynctool.exceptions import ServiceDriverException
from tunesynctool.models import Track


class FakeResponse:
    status = 429
    reason = "Too Many Requests"


def make_http_error(reason: str) -> HttpError:
    return HttpError(
        resp=FakeResponse(),
        content=json.dumps({
            "error": {
                "code": 429,
                "message": "Quota exceeded.",
                "errors": [
                    {
                        "domain": "youtube.quota",
                        "reason": reason,
                        "message": "Quota exceeded.",
                    }
                ],
            }
        }).encode("utf-8"),
    )


class FakeExecutableRequest:
    def execute(self):
        raise make_http_error("rateLimitExceeded")


class FakeSearchResource:
    def list(self, **kwargs):
        return FakeExecutableRequest()


class FakeOfficialClient:
    def search(self):
        return FakeSearchResource()


class FailingLegacyDriver:
    def search_tracks(self, query: str, limit: int = 10):
        raise ServiceDriverException("legacy search failed")


def test_rate_limit_exception_reads_error_details_reason():
    driver = object.__new__(YouTubeOAuth2Driver)

    assert driver._is_rate_limit_exception(make_http_error("quotaExceeded"))
    assert driver._is_rate_limit_exception(make_http_error("rateLimitExceeded"))
    assert driver._is_rate_limit_exception(make_http_error("userRateLimitExceeded"))


def test_rate_limit_exception_rejects_unrelated_error_details_reason():
    driver = object.__new__(YouTubeOAuth2Driver)

    assert not driver._is_rate_limit_exception(make_http_error("forbidden"))


def test_search_tracks_uses_public_search_when_authenticated_legacy_fallback_fails(monkeypatch):
    fallback_track = Track(
        title="WOW",
        primary_artist="Artist",
        service_id="video-id",
        service_name="youtube",
    )
    driver = object.__new__(YouTubeOAuth2Driver)
    driver.client = FakeOfficialClient()
    driver._YouTubeOAuth2Driver__legacy_driver = FailingLegacyDriver()

    monkeypatch.setattr(
        YouTubeOAuth2Driver,
        "_YouTubeOAuth2Driver__search_tracks_without_auth",
        lambda self, query, limit=10: [fallback_track],
    )

    assert driver.search_tracks("WOW", limit=5) == [fallback_track]
