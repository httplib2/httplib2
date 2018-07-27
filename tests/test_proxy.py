"""Proxy tests.

Tests do modify `os.environ` global states. Each test must be run in separate
process. Must use `pytest --forked` or similar technique.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import httplib2
import mock
import os
import socket
import tests


def _raise_name_not_known_error(*args, **kwargs):
    raise socket.gaierror(socket.EAI_NONAME, "Name or service not known")


def test_from_url():
    pi = httplib2.proxy_info_from_url("http://myproxy.example.com")
    assert pi.proxy_host == "myproxy.example.com"
    assert pi.proxy_port == 80
    assert pi.proxy_user is None


def test_from_url_ident():
    pi = httplib2.proxy_info_from_url("http://zoidberg:fish@someproxy:99")
    assert pi.proxy_host == "someproxy"
    assert pi.proxy_port == 99
    assert pi.proxy_user == "zoidberg"
    assert pi.proxy_pass == "fish"


def test_from_env():
    os.environ["http_proxy"] = "http://myproxy.example.com:8080"
    pi = httplib2.proxy_info_from_environment()
    assert pi.proxy_host == "myproxy.example.com"
    assert pi.proxy_port == 8080


def test_from_env_https():
    os.environ["http_proxy"] = "http://myproxy.example.com:80"
    os.environ["https_proxy"] = "http://myproxy.example.com:81"
    pi = httplib2.proxy_info_from_environment("https")
    assert pi.proxy_host == "myproxy.example.com"
    assert pi.proxy_port == 81


def test_from_env_none():
    os.environ.clear()
    pi = httplib2.proxy_info_from_environment()
    assert pi is None


def test_applies_to():
    os.environ["http_proxy"] = "http://myproxy.example.com:80"
    os.environ["https_proxy"] = "http://myproxy.example.com:81"
    os.environ["no_proxy"] = "localhost,example.com,.wildcard"
    pi = httplib2.proxy_info_from_environment()
    assert not pi.applies_to("localhost")
    assert pi.applies_to("www.google.com")
    assert pi.applies_to("prefixlocalhost")
    assert pi.applies_to("www.example.com")
    assert pi.applies_to("sub.example.com")
    assert not pi.applies_to("sub.wildcard")
    assert not pi.applies_to("pub.sub.wildcard")


def test_noproxy_trailing_comma():
    os.environ["http_proxy"] = "http://myproxy.example.com:80"
    os.environ["no_proxy"] = "localhost,other.host,"
    pi = httplib2.proxy_info_from_environment()
    assert not pi.applies_to("localhost")
    assert not pi.applies_to("other.host")
    assert pi.applies_to("example.domain")


def test_noproxy_star():
    os.environ["http_proxy"] = "http://myproxy.example.com:80"
    os.environ["NO_PROXY"] = "*"
    pi = httplib2.proxy_info_from_environment()
    for host in ("localhost", "169.254.38.192", "www.google.com"):
        assert not pi.applies_to(host)


def test_headers():
    headers = {"key0": "val0", "key1": "val1"}
    pi = httplib2.ProxyInfo(
        httplib2.socks.PROXY_TYPE_HTTP, "localhost", 1234, proxy_headers=headers
    )
    assert pi.proxy_headers == headers


@mock.patch("socket.socket.connect", spec=True)
def test_server_not_found_error_is_raised_for_invalid_hostname(mock_socket_connect):
    """Invalidates https://github.com/httplib2/httplib2/pull/100."""
    mock_socket_connect.side_effect = _raise_name_not_known_error
    http = httplib2.Http(
        proxy_info=httplib2.ProxyInfo(
            httplib2.socks.PROXY_TYPE_HTTP, "255.255.255.255", 8001
        )
    )
    with tests.assert_raises(httplib2.ServerNotFoundError):
        http.request("http://invalid.hostname.foo.bar/", "GET")
