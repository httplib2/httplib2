import httplib2
import pytest


@pytest.mark.parametrize("algorithm,password_algorithm,expected", [
    ("HMAC-SHA-1", "SHA-1", "fce1da94b334bf3aa7b0fb13773145689d2f1904"),
    ("HMAC-SHA-1", "MD5", "d9790b7ff6329af0a333fe19ae14887460e804a2"),
    ("HMAC-MD5", "SHA-1", "672c8653b7fb7f77432d830d04d45bdf"),
    ("HMAC-MD5", "MD5", "546430fb99f17c0d3561b9139383e1b7"),
])
def test_hmac_digest_hashlib_vectors(monkeypatch, algorithm, password_algorithm, expected):
    challenge = ('HMACDigest realm="example", snonce="server", salt="salt", '
                 'algorithm="%s", pw-algorithm="%s"' % (algorithm, password_algorithm))
    authentication = httplib2.HmacDigestAuthentication(
        ("Aladdin", "open sesame"), "example.com", "/resource", {},
        {"www-authenticate": challenge}, b"", httplib2.Http())
    monkeypatch.setattr(httplib2, "_cnonce", lambda: "client")
    headers = {}
    authentication.request("GET", "/resource", headers, b"")
    parsed = httplib2.auth._parse_www_authenticate({"www-authenticate": headers["authorization"]})["hmacdigest"]
    assert parsed["response"] == expected
    assert parsed["username"] == "Aladdin"
    assert parsed["headers"] == ""
    assert parsed["snonce"] == "server"


def test_hmac_digest_encodes_text_as_utf8(monkeypatch):
    challenge = 'HMACDigest realm="r\u00e9alm", snonce="server", salt="s\u00e4lt"'
    authentication = httplib2.HmacDigestAuthentication(
        ("T\u00e9st", "p\u00e4ss"), "example.com", "/resource", {},
        {"www-authenticate": challenge}, b"", httplib2.Http())
    monkeypatch.setattr(httplib2, "_cnonce", lambda: "client")
    headers = {}
    authentication.request("GET", "/resource", headers, b"")
    parsed = httplib2.auth._parse_www_authenticate({"www-authenticate": headers["authorization"]})["hmacdigest"]
    assert parsed["response"] == "9208554f2375df992a036037ac9cb40f231964ca"
    assert parsed["username"] == "T\u00e9st"
