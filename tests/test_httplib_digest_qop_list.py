import httplib2
import pytest


def make_authentication(qop):
    challenge = ('Digest realm="testrealm@host.com", '
                 'nonce="dcd98b7102dd2f0e8b11d0f600bfb0c093", qop="' + qop + '"')
    return httplib2.DigestAuthentication(
        ("Mufasa", "Circle Of Life"), "host.com", "/dir/index.html", {},
        {"www-authenticate": challenge}, b"", httplib2.Http())


@pytest.mark.parametrize("qop", ["auth,auth-int", "auth-int, auth", " auth , auth-int ", "auth"])
def test_comma_separated_digest_qop_uses_auth(qop):
    authentication = make_authentication(qop)
    headers = {}
    authentication.request("GET", "/dir/index.html", headers, b"", cnonce="0a4f113b")
    assert 'response="6629fae49393a05397450978507c4ef1"' in headers["authorization"]
    assert "qop=auth," in headers["authorization"]
