from httplib2.iri2uri import iri2uri

import pytest


@pytest.mark.parametrize(
    "iri,uri",
    [
        # Userinfo is not part of the host, so it must not be IDNA-encoded.
        ("http://user@exämple.com/", "http://user@xn--exmple-cua.com/"),
        (
            "http://user:pass@exämple.com/",
            "http://user:pass@xn--exmple-cua.com/",
        ),
        (
            "http://user:pass@exämple.com:8080/path?query#fragment",
            "http://user:pass@xn--exmple-cua.com:8080/path?query#fragment",
        ),
        ("//user@exämple.com/", "//user@xn--exmple-cua.com/"),
        # ASCII userinfo and host are left untouched.
        ("http://user:pass@example.com/", "http://user:pass@example.com/"),
        # No userinfo: pre-existing behavior is preserved.
        ("http://exämple.com/", "http://xn--exmple-cua.com/"),
        ("http://exämple.com:8080/", "http://xn--exmple-cua.com:8080/"),
    ],
)
def test_iri2uri_userinfo_not_idna_encoded(iri, uri):
    assert iri2uri(iri) == uri

