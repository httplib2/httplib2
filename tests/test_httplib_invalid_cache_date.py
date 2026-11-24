import email.utils

import httplib2
import pytest


@pytest.mark.parametrize("date", [
    "", "not a date", "Fri, 01 NotAMonth 2024 00:00:00 GMT",
    "Fri, 01 Jan 10000 00:00:00 GMT",
])
def test_invalid_cache_date_is_stale(date):
    headers = {"date": date, "cache-control": "max-age=3600"}
    assert httplib2._entry_disposition(headers, {}) == "STALE"


def test_valid_cache_date_still_allows_fresh_response(monkeypatch):
    now = 1700000000
    monkeypatch.setattr(httplib2.time, "time", lambda: now)
    headers = {"date": email.utils.formatdate(now - 10, usegmt=True), "cache-control": "max-age=3600"}
    assert httplib2._entry_disposition(headers, {}) == "FRESH"
