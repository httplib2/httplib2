import email.utils

import httplib2
import pytest


@pytest.mark.parametrize("control,expected", [
    ('max-age="3600", no-store', {"max-age": "3600", "no-store": 1}),
    ('no-cache="Set-Cookie, X-Session", max-age=20',
     {"no-cache": "set-cookie, x-session", "max-age": "20"}),
    (r'custom="a\"b,c", min-fresh="2"', {"custom": 'a"b,c', "min-fresh": "2"}),
])
def test_quoted_cache_directives(control, expected):
    assert httplib2._parse_cache_control({"cache-control": control}) == expected


def test_quoted_response_age_is_fresh(monkeypatch):
    now = 1700000000
    monkeypatch.setattr(httplib2.time, "time", lambda: now)
    response = {"date": email.utils.formatdate(now - 30, usegmt=True), "cache-control": 'max-age="60"'}
    assert httplib2._entry_disposition(response, {}) == "FRESH"


def test_quoted_request_age_and_min_fresh_are_honored(monkeypatch):
    now = 1700000000
    monkeypatch.setattr(httplib2.time, "time", lambda: now)
    response = {"date": email.utils.formatdate(now - 30, usegmt=True), "cache-control": "max-age=60"}
    assert httplib2._entry_disposition(response, {"cache-control": 'max-age="40"'}) == "FRESH"
    assert httplib2._entry_disposition(response, {"cache-control": 'min-fresh="40"'}) == "STALE"
