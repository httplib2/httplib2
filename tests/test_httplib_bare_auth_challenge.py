import pytest
from httplib2.auth import _parse_www_authenticate


@pytest.mark.parametrize("header,expected", [
    ("Negotiate", {"negotiate": {"token": None}}),
    ('Negotiate, Basic realm="example"',
     {"negotiate": {"token": None}, "basic": {"realm": "example"}}),
    ('Basic realm="example", Negotiate',
     {"basic": {"realm": "example"}, "negotiate": {"token": None}}),
    ("Negotiate abc==", {"negotiate": {"token": "abc=="}}),
    ('Basic realm="example"', {"basic": {"realm": "example"}}),
])
def test_parameterless_authentication_challenges(header, expected):
    assert _parse_www_authenticate({"www-authenticate": header}) == expected
