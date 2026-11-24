import httplib2


def test_digest_quoted_values_round_trip_without_changing_the_digest():
    value = 'a"b\\c'
    challenge = r'Digest realm="a\"b\\c", nonce="a\"b\\c", qop="auth", opaque="a\"b\\c"'
    authentication = httplib2.DigestAuthentication(
        (value, "secret"), "example.com", "/resource", {},
        {"www-authenticate": challenge}, b"", httplib2.Http())
    headers = {}
    authentication.request("GET", "/resource", headers, b"", cnonce=value)
    parsed = httplib2.auth._parse_www_authenticate({"www-authenticate": headers["authorization"]})["digest"]
    for field in ("username", "realm", "nonce", "cnonce", "opaque"):
        assert parsed[field] == value
    assert parsed["uri"] == "/resource"
    assert parsed["response"] == "e5dfb374193e02b901d80f90caad5bef"
    assert parsed["nc"] == "00000001"


def test_digest_escapes_the_quoted_uri():
    uri = '/resource?name="quoted"'
    authentication = httplib2.DigestAuthentication(
        ("user", "password"), "example.com", uri, {},
        {"www-authenticate": 'Digest realm="example", nonce="n", qop="auth"'},
        b"", httplib2.Http())
    headers = {}
    authentication.request("GET", uri, headers, b"", cnonce="c")
    parsed = httplib2.auth._parse_www_authenticate({"www-authenticate": headers["authorization"]})["digest"]
    assert parsed["uri"] == uri
    assert parsed["username"] == "user"
