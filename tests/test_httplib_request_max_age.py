import email.utils

import httplib2
import pytest


@pytest.mark.parametrize("response_lifetime,request_age,age,expected", [
    (60, 3600, 120, "STALE"),
    (3600, 60, 120, "STALE"),
    (3600, 60, 30, "FRESH"),
    (60, 3600, 30, "FRESH"),
])
@pytest.mark.parametrize("directive", ["max-age", "expires"])
def test_request_age_cannot_extend_response_freshness(
        monkeypatch, response_lifetime, request_age, age, expected, directive):
    now = 1700000000
    monkeypatch.setattr(httplib2.time, "time", lambda: now)
    response = {"date": email.utils.formatdate(now - age, usegmt=True)}
    if directive == "max-age":
        response["cache-control"] = "max-age=" + str(response_lifetime)
    else:
        response["expires"] = email.utils.formatdate(now - age + response_lifetime, usegmt=True)
    request = {"cache-control": "max-age=" + str(request_age)}
    assert httplib2._entry_disposition(response, request) == expected


def test_request_max_age_does_not_create_a_freshness_lifetime(monkeypatch):
    now = 1700000000
    monkeypatch.setattr(httplib2.time, "time", lambda: now)
    response = {"date": email.utils.formatdate(now - 10, usegmt=True)}
    assert httplib2._entry_disposition(response, {"cache-control": "max-age=3600"}) == "STALE"
