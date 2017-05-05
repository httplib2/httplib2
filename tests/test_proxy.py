'''Warning: these tests modify os.environ global state.
Each test must be run in separate process.
Must use pytest --forked or similar technique.
'''
import httplib2
import os
import pytest
import sys
# import tests


def test_from_url():
    pi = httplib2.proxy_info_from_url('http://myproxy.example.com')
    assert pi.proxy_host == 'myproxy.example.com'
    assert pi.proxy_port == 80
    assert pi.proxy_user is None


def test_from_url_ident():
    pi = httplib2.proxy_info_from_url('http://zoidberg:fish@someproxy:99')
    assert pi.proxy_host == 'someproxy'
    assert pi.proxy_port == 99
    assert pi.proxy_user == 'zoidberg'
    assert pi.proxy_pass == 'fish'


def test_from_env():
    os.environ['http_proxy'] = 'http://myproxy.example.com:8080'
    pi = httplib2.proxy_info_from_environment()
    assert pi.proxy_host == 'myproxy.example.com'
    assert pi.proxy_port == 8080


def test_from_env_https():
    os.environ['http_proxy'] = 'http://myproxy.example.com:80'
    os.environ['https_proxy'] = 'http://myproxy.example.com:81'
    pi = httplib2.proxy_info_from_environment('https')
    assert pi.proxy_host == 'myproxy.example.com'
    assert pi.proxy_port == 81


def test_from_env_none():
    os.environ.clear()
    pi = httplib2.proxy_info_from_environment()
    assert pi is None


@pytest.mark.skipif(sys.version_info >= (3,), reason='FIXME: https://github.com/httplib2/httplib2/issues/53')
def test_applies_to():
    os.environ['http_proxy'] = 'http://myproxy.example.com:80'
    os.environ['https_proxy'] = 'http://myproxy.example.com:81'
    os.environ['no_proxy'] = 'localhost,otherhost.domain.local,example.com'
    pi = httplib2.proxy_info_from_environment()
    assert not pi.applies_to('localhost')
    assert pi.applies_to('www.google.com')
    assert not pi.applies_to('www.example.com')


@pytest.mark.skipif(sys.version_info >= (3,), reason='FIXME: https://github.com/httplib2/httplib2/issues/53')
def test_noproxy_star():
    os.environ['http_proxy'] = 'http://myproxy.example.com:80'
    os.environ['NO_PROXY'] = '*'
    pi = httplib2.proxy_info_from_environment()
    for host in ('localhost', '169.254.38.192', 'www.google.com'):
        assert not pi.applies_to(host)


@pytest.mark.skipif(sys.version_info >= (3,), reason='FIXME: https://github.com/httplib2/httplib2/issues/53')
def test_headers():
    headers = {'key0': 'val0', 'key1': 'val1'}
    pi = httplib2.ProxyInfo(httplib2.socks.PROXY_TYPE_HTTP, 'localhost', 1234, proxy_headers=headers)
    assert pi.proxy_headers == headers
