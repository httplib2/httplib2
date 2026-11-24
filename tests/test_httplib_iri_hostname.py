import pytest
from httplib2.iri2uri import iri2uri


@pytest.mark.parametrize("source,expected", [
    ("http://\u00e9@example.com/", "http://%C3%A9@example.com/"),
    ("http://user:p\u00e4ss@\u00e9xample.com:8080/", "http://user:p%C3%A4ss@xn--xample-9ua.com:8080/"),
    ("http://user@" + "a" * 63 + ".com:8080/", "http://user@" + "a" * 63 + ".com:8080/"),
    ("http://" + "a" * 63 + ":8080/", "http://" + "a" * 63 + ":8080/"),
    ("http://user:pass@[2001:db8::1]:8080/", "http://user:pass@[2001:db8::1]:8080/"),
    ("http://[fe80::1%25eth0]/", "http://[fe80::1%25eth0]/"),
    ("http://user%40name@example.com/", "http://user%40name@example.com/"),
])
def test_iri_authority_components_are_encoded_separately(source, expected):
    assert iri2uri(source) == expected
    assert iri2uri(expected) == expected
