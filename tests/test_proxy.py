"""Proxy tests.

Tests do modify `os.environ` global states. Each test must be run in separate
process. Must use `pytest --forked` or similar technique.
"""

import ipaddress
import os
import pytest
import random
import socket
import socks
from unittest import mock
import urllib

import httplib2
import tests
from tests import socks5


def _raise_name_not_known_error(*args, **kwargs):
    raise socket.gaierror(socket.EAI_NONAME, "Name or service not known")


@pytest.mark.parametrize(
    "url,kind,host,port,user,password",
    [
        # ("noscheme.means.http", socks.PROXY_TYPE_HTTP, "noscheme.means.http", 80, None, None),
        ("http://myproxy.example.com", socks.PROXY_TYPE_HTTP, "myproxy.example.com", 80, None, None),
        ("http://zoidberg:fish@someproxy:99", socks.PROXY_TYPE_HTTP, "someproxy", 99, "zoidberg", "fish"),
        ("http://leila@fro.xy:1032", socks.PROXY_TYPE_HTTP, "fro.xy", 1032, "leila", None),
        ("http://[::1]:8888", socks.PROXY_TYPE_HTTP, "::1", 8888, None, None),
        ("socks4://myproxy.example.com", socks.PROXY_TYPE_SOCKS4, "myproxy.example.com", 80, None, None),
        ("socks4://zoidberg:fish@someproxy:99", socks.PROXY_TYPE_SOCKS4, "someproxy", 99, "zoidberg", "fish"),
        ("socks4://leila@fro.xy:1032", socks.PROXY_TYPE_SOCKS4, "fro.xy", 1032, "leila", None),
        ("socks4://[::1]:8888", socks.PROXY_TYPE_SOCKS4, "::1", 8888, None, None),
        ("socks5://myproxy.example.com", socks.PROXY_TYPE_SOCKS5, "myproxy.example.com", 80, None, None),
        ("socks5://zoidberg:fish@someproxy:99", socks.PROXY_TYPE_SOCKS5, "someproxy", 99, "zoidberg", "fish"),
        ("socks5://leila@fro.xy:1032", socks.PROXY_TYPE_SOCKS5, "fro.xy", 1032, "leila", None),
        ("socks5://[::1]:8888", socks.PROXY_TYPE_SOCKS5, "::1", 8888, None, None),
    ],
)
def test_from_url(url, kind, host, port, user, password):
    pi = httplib2.proxy_info_from_url(url)
    assert pi.proxy_type == kind, f"proxy_type expected={kind} invalid={pi.proxy_type}"
    assert pi.proxy_host == host, f"proxy_host expected={host} invalid={pi.proxy_host}"
    assert pi.proxy_port == port, f"proxy_port expected={port} invalid={pi.proxy_port}"
    assert pi.proxy_user == user, f"proxy_user expected={user} invalid={pi.proxy_user}"
    assert pi.proxy_pass == password, f"proxy_pass expected={password} invalid={pi.proxy_pass}"


@pytest.mark.forked
def test_from_env(monkeypatch):
    assert os.environ.get("http_proxy") is None
    monkeypatch.setenv("http_proxy", "http://myproxy.example.com:8080")
    pi = httplib2.proxy_info_from_environment()
    assert pi.proxy_host == "myproxy.example.com"
    assert pi.proxy_port == 8080


@pytest.mark.forked
def test_from_env_https(monkeypatch):
    assert os.environ.get("http_proxy") is None
    monkeypatch.setenv("http_proxy", "http://myproxy.example.com:80")
    monkeypatch.setenv("https_proxy", "http://myproxy.example.com:81")
    pi = httplib2.proxy_info_from_environment("https")
    assert pi.proxy_host == "myproxy.example.com"
    assert pi.proxy_port == 81


@pytest.mark.forked
def test_from_env_none():
    os.environ.clear()
    pi = httplib2.proxy_info_from_environment()
    assert pi is None


def test_from_env_other():
    pi = httplib2.proxy_info_from_environment("foobar")
    assert pi is None


def test_proxy_info_repr():
    pi = httplib2.ProxyInfo(3, "pseudorandom", 8123, proxy_pass="secret")
    r = repr(pi)
    assert "pseudorandom" in r
    assert "8123" in r
    assert "secret" not in r


@pytest.mark.forked
def test_applies_to(monkeypatch):
    monkeypatch.setenv("http_proxy", "http://myproxy.example.com:80")
    monkeypatch.setenv("https_proxy", "http://myproxy.example.com:81")
    monkeypatch.setenv("no_proxy", "localhost,example.com,.wildcard")
    pi = httplib2.proxy_info_from_environment()
    assert not pi.applies_to("localhost")
    assert pi.applies_to("www.google.com")
    assert pi.applies_to("prefixlocalhost")
    assert pi.applies_to("www.example.com")
    assert pi.applies_to("sub.example.com")
    assert not pi.applies_to("sub.wildcard")
    assert not pi.applies_to("pub.sub.wildcard")


@pytest.mark.forked
def test_noproxy_trailing_comma(monkeypatch):
    monkeypatch.setenv("http_proxy", "http://myproxy.example.com:80")
    monkeypatch.setenv("no_proxy", "localhost,other.host,")
    pi = httplib2.proxy_info_from_environment()
    assert not pi.applies_to("localhost")
    assert not pi.applies_to("other.host")
    assert pi.applies_to("example.domain")


@pytest.mark.forked
def test_noproxy_star(monkeypatch):
    monkeypatch.setenv("http_proxy", "http://myproxy.example.com:80")
    monkeypatch.setenv("NO_PROXY", "*")
    pi = httplib2.proxy_info_from_environment()
    for host in ("localhost", "169.254.38.192", "www.google.com"):
        assert not pi.applies_to(host)


def test_headers():
    headers = {"key0": "val0", "key1": "val1"}
    pi = httplib2.ProxyInfo(httplib2.socks.PROXY_TYPE_HTTP, "localhost", 1234, proxy_headers=headers)
    assert pi.proxy_headers == headers


@mock.patch("socket.socket.connect", spec=True)
def test_server_not_found_error_is_raised_for_invalid_hostname(mock_socket_connect):
    """Invalidates https://github.com/httplib2/httplib2/pull/100."""
    mock_socket_connect.side_effect = _raise_name_not_known_error
    http = httplib2.Http(proxy_info=httplib2.ProxyInfo(httplib2.socks.PROXY_TYPE_HTTP, "255.255.255.255", 8001))
    try:
        http.request("http://invalid.hostname.foo.bar/", "GET")
    except httplib2.ServerNotFoundError:
        pass
    except Exception as e:
        assert "name or service not known" in str(e).lower()


def test_auth_str_bytes():
    # https://github.com/httplib2/httplib2/pull/115
    # Proxy-Authorization b64encode() TypeError: a bytes-like object is required, not 'str'
    with tests.server_const_http(request_count=2) as uri:
        uri_parsed = urllib.parse.urlparse(uri)
        http = httplib2.Http(
            proxy_info=httplib2.ProxyInfo(
                httplib2.socks.PROXY_TYPE_HTTP,
                proxy_host=uri_parsed.hostname,
                proxy_port=uri_parsed.port,
                proxy_rdns=True,
                proxy_user="user_str",
                proxy_pass="pass_str",
            )
        )
        response, _ = http.request(uri, "GET")
        assert response.status == 200

    with tests.server_const_http(request_count=2) as uri:
        uri_parsed = urllib.parse.urlparse(uri)
        http = httplib2.Http(
            proxy_info=httplib2.ProxyInfo(
                httplib2.socks.PROXY_TYPE_HTTP,
                proxy_host=uri_parsed.hostname,
                proxy_port=uri_parsed.port,
                proxy_rdns=True,
                proxy_user=b"user_bytes",
                proxy_pass=b"pass_bytes",
            )
        )
        response, _ = http.request(uri, "GET")
        assert response.status == 200


def test_socks5_auth():
    def proxy_conn(client, tick):
        data = client.recv(64)
        assert data == bytes(
            [socks5.VERSION, 0x02, socks5.AUTH_NO_AUTHENTICATION_REQUIRED, socks5.AUTH_USERNAME_PASSWORD]
        )
        client.send(socks5.SERVER_GREETING_USER_PASS)
        data = client.recv(64)
        assert data == b"\x01\x08user_str\x08pass_str"
        client.send(socks5.AUTH_FAILURE)
        tick(None)

    with tests.server_socket(proxy_conn) as uri:
        uri_parsed = urllib.parse.urlparse(uri)
        proxy_info = httplib2.ProxyInfo(
            httplib2.socks.PROXY_TYPE_SOCKS5,
            proxy_host=uri_parsed.hostname,
            proxy_port=uri_parsed.port,
            proxy_rdns=True,
            proxy_user="user_str",
            proxy_pass="pass_str",
        )
        http = httplib2.Http(proxy_info=proxy_info)
        try:
            http.request(uri, "GET")
            assert False, "expected socks authentication error"
        except httplib2.socks.SOCKS5AuthError:
            pass
        except Exception as e:
            assert "authentication failed" in str(e)


@pytest.mark.forked
def test_functional_socks5(monkeypatch):
    expect_body = "unique-{}".format(random.randint(1, 100)).encode("utf-8")
    gserver = [None, b""]
    glog = []

    def proxy_conn(client, tick):
        assert gserver[0] is not None
        assert gserver[1]

        data_hello = client.recv(64)
        assert data_hello == bytes([socks5.VERSION, 1, socks5.AUTH_NO_AUTHENTICATION_REQUIRED])
        client.send(socks5.SERVER_GREETING_NO_AUTH)

        data_connect = client.recv(64)
        assert data_connect == bytes([socks5.VERSION, socks5.CMD_CONNECT, 0x00]) + gserver[1]
        http_endpoint = gserver[0]  # TODO parse data_connect
        backend = socket.create_connection(http_endpoint, timeout=5)
        client.send(b"\x05\x00\x00\x01\x00\x00\x00\x00\x00\x00")

        request_buf = tests.BufferedReader(client)
        request = tests.HttpRequest.from_buffered(request_buf)
        assert request is not None
        glog.append(request)
        backend.sendall(request.raw)
        response_buf = tests.BufferedReader(backend)
        backend_response = tests.HttpResponse.from_buffered(response_buf)
        client.sendall(backend_response.raw)

        tick(request)

    with tests.server_socket(proxy_conn, scheme=None) as proxy_endpoint, tests.server_const_http(
        body=expect_body, scheme=None
    ) as http_endpoint:
        http_host, http_port = http_endpoint
        http_ip_version = check_ip_version(http_host)
        http_endpoint_socks_format = b""
        if http_ip_version == 4:
            http_endpoint_socks_format = b"\x01" + bytes(map(int, http_host.split(".")))
        elif http_ip_version == 6:
            pass  # TODO
        else:
            http_endpoint_socks_format = b"\x03" + bytes([len(http_host)]) + http_host.encode("ascii")
        assert http_endpoint_socks_format
        http_endpoint_socks_format += http_port.to_bytes(2, byteorder="big")
        gserver[0] = http_endpoint
        gserver[1] = http_endpoint_socks_format

        proxy_uri = "socks5://{}:{}".format(*proxy_endpoint)
        monkeypatch.setenv("http_proxy", proxy_uri)
        uri = "http://{}:{}/".format(*http_endpoint)
        http = httplib2.Http()
        response, body = http.request(uri, "GET")
        assert response.status == 200
        assert body == expect_body


def check_ip_version(s: str):
    try:
        ip = ipaddress.ip_address(s)
        if isinstance(ip, ipaddress.IPv4Address):
            return 4
        elif isinstance(ip, ipaddress.IPv6Address):
            return 6
        else:
            raise NotImplementedError
    except ValueError:
        return None


@pytest.mark.forked
def test_functional_noproxy_star_http(monkeypatch):
    def handler(request):
        if request.method == "CONNECT":
            return tests.http_response_bytes(
                status="400 Expected direct",
                headers={"connection": "close"},
            )
        return tests.http_response_bytes()

    with tests.server_request(handler) as uri:
        monkeypatch.setenv("http_proxy", uri)
        monkeypatch.setenv("no_proxy", "*")
        http = httplib2.Http()
        response, _ = http.request(uri, "GET")
        assert response.status == 200


@pytest.mark.forked
def test_functional_noproxy_star_https(monkeypatch):
    def handler(request):
        if request.method == "CONNECT":
            return tests.http_response_bytes(
                status="400 Expected direct",
                headers={"connection": "close"},
            )
        return tests.http_response_bytes()

    with tests.server_request(handler, tls=True) as uri:
        monkeypatch.setenv("https_proxy", uri)
        monkeypatch.setenv("no_proxy", "*")
        http = httplib2.Http(ca_certs=tests.CA_CERTS)
        response, _ = http.request(uri, "GET")
        assert response.status == 200
