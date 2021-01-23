import httplib2
from httplib2.cookie import Cookie
import pytest
import socket
import tests
from six.moves import urllib
from datetime import datetime, timedelta
import time


@pytest.fixture
def cookie_jar():
    cj = httplib2.CookieJar({"g_a": "1", "g_b": "2", "g_c": "3"})
    cj.set("aaa", "111", domain="example.com", max_age=10000)
    cj.set("bbb", "222", domain=".example.com", secure=True)
    cj.set("ccc", "333", domain=".example.com", path="/dir_a", secure=True)
    cj.set("ddd", "444", domain=".example.com", path="/dir_b/dir_c")
    yield cj
    cj.clear()


@pytest.fixture
def cookie_file(tmpdir, cookie_jar):
    d = tmpdir.join("cookie.txt")
    cookie_jar.save(str(d))
    yield str(d)


def test_cookie_jar_basic():
    """Test making cookies and set, get cookies from cookiejar."""
    cj = httplib2.CookieJar()
    assert cj.get() == []

    cookie1 = Cookie.create("abc", "123", "example.com")
    cj.set(cookie1)

    cookie2 = Cookie.create("def", "456", ".example.com", "/dir_a", max_age=0)
    cj.set(cookie2)

    expires = (datetime.utcnow() + timedelta(seconds=5)).strftime("%a, %d %b %Y %H:%M:%S GMT")
    cookie3 = Cookie.create("ghi", "789", ".example.com", "/dir_b", expires=expires)
    cj.set(cookie3)

    # A global and secure
    cookie4 = Cookie.create("jkl", "000", secure=True)
    cj.set(cookie4)

    assert len(cj.get()) == 4
    assert cj.get("example.com") == [cookie1]
    assert cj.get("example.com", "/") == [cookie1]
    assert cj.get("example.com", "/", "abc") == cookie1
    assert set(cj.get(".example.com")) == {cookie2, cookie3}
    assert cj.get(".example.com", "/dir_b") == [cookie3]
    assert cj.get(".") == [cookie4]

    with pytest.raises(KeyError):
        cj.get("example.com", "/", "123")


def test_cookie_jar_expire():
    """Test expired cookie."""
    cookie = Cookie.create("abc", "123", max_age=5)
    assert not cookie.is_expired()

    # a cookie with max_age 0 or negtive will expire the cookie immeditely
    cookie = Cookie.create("abc", "123", max_age=0)
    assert cookie.is_expired()

    cookie = Cookie.create("abc", "123", max_age=-1)
    assert cookie.is_expired()

    expires = (datetime.utcnow() + timedelta(seconds=5)).strftime("%a, %d %b %Y %H:%M:%S GMT")
    cookie = Cookie.create("abc", "123", expires=expires)
    assert not cookie.is_expired()

    expires = (datetime.utcnow() - timedelta(seconds=1)).strftime("%a, %d %b %Y %H:%M:%S GMT")
    cookie = Cookie.create("abc", "123", expires=expires)
    assert cookie.is_expired()


def test_cookie_jar_init_with_cookies():
    """Initialize the cookie jar with global cookies."""
    cj = httplib2.CookieJar({"a": "1", "b": "2", "c": "3"})
    assert len(cj.get()) == 3
    assert len(cj.get(".")) == 3
    assert len(cj.get(".", "/")) == 3


def test_cookie_jar_auto_persistence(tmpdir):
    """Initialize the cookie jar with cookie file."""
    ckfile = str(tmpdir.join("cookie.txt"))
    cj = httplib2.CookieJar({"a": "1", "b": "2", "c": "3"}, filename=ckfile)

    cookie = Cookie.create("abc", "123", "example.com")
    cj.set(cookie)
    assert len(cj.get()) == 4

    # Cookies with global domain (.) will not be saved.
    cj = httplib2.CookieJar(filename=ckfile)
    assert len(cj.get()) == 1

    cj = httplib2.CookieJar({"a": 1}, filename=ckfile)
    assert len(cj.get()) == 2
    cj.clear()

    cj = httplib2.CookieJar(filename=ckfile)
    assert len(cj.get()) == 0


def test_cookie_jar_manual_persistence(cookie_file):
    """Save cookies to cookie file and load them back."""
    cj = httplib2.CookieJar()
    assert cj.get() == []

    cj.load(cookie_file)
    assert len(cj.get()) == 4

    cj.set(Cookie.create("username", "john"))  # global cookie
    cj.set(Cookie.create("password", "123456", "example.com"))
    assert len(cj.get()) == 6

    cj.save(cookie_file)
    cj.load(cookie_file)
    assert len(cj.get()) == 6

    # the global cookies are cleared
    cj.clear()
    cj.load(cookie_file)
    assert len(cj.get()) == 5

    cookie = cj.get(".example.com", "/dir_a", "ccc")
    assert cookie.name == "ccc"
    assert cookie.value == "333"
    assert cookie.domain == ".example.com"
    assert cookie.path == "/dir_a/"
    assert cookie.expires is None
    assert cookie.secure


def test_cookie_jar_iter(cookie_jar):
    """Test cookie iterator"""
    count = 0
    for cookie in cookie_jar.iter():
        count += 1
    assert count == 7

    count = 0
    for cookie in cookie_jar.iter("example.com"):
        count += 1
    assert count == 1

    count = 0
    for cookie in cookie_jar.iter(".example.com", "/dir_a"):
        count += 1
    assert count == 1

    with pytest.raises(KeyError):
        for cookie in cookie_jar.iter(".example2.com"):
            pass

    with pytest.raises(KeyError):
        for cookie in cookie_jar.iter(".example.com", "/dir_c"):
            pass


def test_cookie_jar_clear(cookie_jar):
    """Test clear the cookies in cookie jar"""

    # Clear a non-existing cookie won't raise exception
    cookie_jar.clear(".example2.com")
    assert len(cookie_jar.get()) == 7

    # Clear cookies by domain and path
    cookie_jar.clear(".example.com", "/dir_a")
    assert len(cookie_jar.get()) == 6

    # Clear global cookies
    cookie_jar.clear(".")
    assert len(cookie_jar.get()) == 3

    # Clear all cookies
    cookie_jar.clear()
    assert len(cookie_jar.get()) == 0


def test_cookie_jar_get_header(cookie_jar):
    """Test getting the HTTP Cookie header from cookie jar"""
    header = cookie_jar.get_header("example.com", "/a/b/c", False)
    assert set(header.split("; ")) == {"g_a=1", "g_b=2", "g_c=3", "aaa=111"}

    header = cookie_jar.get_header("a.example.com", "/dir_a", False)
    assert set(header.split("; ")) == {"g_a=1", "g_b=2", "g_c=3"}

    header = cookie_jar.get_header("a.example.com", "/dir_a/c/d/e", False)
    assert set(header.split("; ")) == {"g_a=1", "g_b=2", "g_c=3"}

    header = cookie_jar.get_header("a.example.com", "/dir_a", True)
    assert set(header.split("; ")) == {"g_a=1", "g_b=2", "g_c=3", "bbb=222", "ccc=333"}

    header = cookie_jar.get_header("a.example.com", "/dir_a/c/d/e", True)
    assert set(header.split("; ")) == {"g_a=1", "g_b=2", "g_c=3", "bbb=222", "ccc=333"}

    header = cookie_jar.get_header("a.example.com", "/dir_b/dir_c/d/e", True)
    assert set(header.split("; ")) == {"g_a=1", "g_b=2", "g_c=3", "bbb=222", "ddd=444"}

    cookie_jar.set(Cookie.create("abc", "123", ".example.com", "/dir_a", max_age=1))
    header = cookie_jar.get_header("a.example.com", "/dir_a/c/d/e", True)
    assert set(header.split("; ")) == {"g_a=1", "g_b=2", "g_c=3", "bbb=222", "ccc=333", "abc=123"}

    # Wait for the cookie expired
    time.sleep(1)
    header = cookie_jar.get_header("a.example.com", "/dir_a/c/d/e", True)
    assert set(header.split("; ")) == {"g_a=1", "g_b=2", "g_c=3", "bbb=222", "ccc=333"}

    cookie_jar.clear()
    header = cookie_jar.get_header("a.example.com", "/dir_a/c/d/e", True)
    assert header == ""


def test_cookie_jar_parse_iter():
    """Test parsing cookies from HTTP Set-Cookie header."""
    for cookie in httplib2.CookieJar.parse_iter(
        "G=7; HttpOnly; SameSite=Strict; domain=example.com; Path=/login/a; MyAttr=1; MyAttr2"
    ):

        assert cookie["name"] == "G"
        assert cookie["value"] == "7"
        assert cookie["domain"] == ".example.com"
        assert cookie["path"] == "/login/a"
        assert cookie["HttpOnly"] is True
        assert cookie["SameSite"] == "Strict"
        # custom cookie attribute in the header
        assert cookie["MyAttr"] == "1"
        assert cookie["MyAttr2"] is True

    for cookie in httplib2.CookieJar.parse_iter("A=1,B=2,C=3"):
        assert cookie["name"] in "ABC"


def test_cookie_jar_extract_header():
    """Test extracting cookies from HTTP Set-Cookie header to cookie jar"""
    cj = httplib2.CookieJar()
    cj.extract_header("www.example.com", "/login.cgi", "A=1;Max-Age=100")
    assert len(cj.get()) == 1

    cj.extract_header("www.example.com", "/login.cgi", "B=2; Max-Age=100,C=3, D=4")
    assert len(cj.get()) == 4

    cj.extract_header("www.example.com", "/login.cgi", "A=1;Max-Age=0")
    assert len(cj.get()) == 4

    cj.extract_header("www.example.com", "/login.cgi", "E=5; Expires=Wed, 21 Oct 2015 07:28:00 GMT;Max-Age=0")
    assert cj.get("www.example.com", "/", "E").is_expired()

    expires = (datetime.utcnow() + timedelta(seconds=5)).strftime("%a, %d %b %Y %H:%M:%S GMT")
    cj.extract_header(
        "www.example.com", "/login/login.cgi", "F=6; Expires={}; Secure; HttpOnly; SameSite=Strict".format(expires)
    )
    cookie = cj.get("www.example.com", "/login", "F")
    assert cookie.secure
    assert cookie.domain == "www.example.com"
    assert cookie.path == "/login/"
    assert not cookie.is_expired()

    cj.extract_header(
        "www.example.com", "/login/login.cgi", "G=7; HttpOnly; SameSite=Strict; domain=example.com; Path=/login/a"
    )
    cookie = cj.get(".example.com", "/login/a", "G")
    assert not cookie.secure
    assert cookie.domain == ".example.com"
    assert cookie.path == "/login/a/"
    assert not cookie.is_expired()

    cj.extract_header("www.example.com", "/login.cgi", "")
    assert len(cj.get()) == 7


# Test Cookie Manager
@pytest.fixture
def cookie_http():
    cj = httplib2.CookieJar()
    http = httplib2.Http(cookie_jar=cj)
    yield http
    http.close()


@pytest.fixture
def cookie_http2(cookie_jar):
    http = httplib2.Http(cookie_jar=cookie_jar)
    yield http
    http.close()


SET_COOKIE_HEADERS = ("A=1; Max-Age=100,B=2, C=3", ("A=1; Max-Age=100", "B=2", "C=3"))


@pytest.mark.parametrize("cookie_header", SET_COOKIE_HEADERS, ids=["single", "multiple"])
def test_response_cookie_attribute(cookie_header):
    """ Test the attribute 'cookies' in Response object."""
    http = httplib2.Http()

    with tests.server_const_http(headers={"set-cookie": cookie_header}) as uri:
        response, _ = http.request(uri, "GET")
        assert len(response.cookies) == 3
        assert response.cookies["A"] == "1"
        assert response.cookies["B"] == "2"
        assert response.cookies["C"] == "3"


def test_onetime_cookie():
    http = httplib2.Http()
    cookies = {"AAA": "111", "BBB": "222"}
    handler = tests.http_reflect_with_cookies()

    with tests.server_request(handler) as uri:
        response, content = http.request(uri, "GET", body="this request have one time cookie", cookies=cookies)
        assert response.status == 200
        assert dict([ck.split("=") for ck in content.decode().split("; ")]) == cookies


@pytest.mark.parametrize("cookie_header", SET_COOKIE_HEADERS, ids=["single", "multiple"])
def test_cookie_manager_enabled(cookie_header, cookie_http):
    print(cookie_header)
    handler = tests.http_reflect_with_cookies({"/login": cookie_header})

    with tests.server_request(handler, request_count=2) as uri:
        login_url = urllib.parse.urljoin(uri, "/login")
        response, content = cookie_http.request(login_url, "POST", body="this is a login request")
        assert response.status == 200
        assert len(response.cookies) == 3

        op_url = urllib.parse.urljoin(uri, "/op")
        response, content = cookie_http.request(op_url, "POST", body="this is an op request")
        assert response.status == 200

        if isinstance(cookie_header, (list, tuple)):
            cookie_header = ", ".join(cookie_header)
        expect_cookies = {ck["name"]: ck["value"] for ck in httplib2.CookieJar.parse_iter(cookie_header)}
        assert dict([ck.split("=") for ck in content.decode().split("; ")]) == expect_cookies


def test_cookie_manager_expire(cookie_http):
    expires = (datetime.utcnow() + timedelta(seconds=2)).strftime("%a, %d %b %Y %H:%M:%S GMT")
    cookie_header = ("A=1", "B=2; Max-Age=1", "C=3; Expires={}".format(expires))
    handler = tests.http_reflect_with_cookies({"/login": cookie_header})

    with tests.server_request(handler, request_count=4, timeout=20) as uri:
        login_url = urllib.parse.urljoin(uri, "/login")
        response, content = cookie_http.request(login_url, "POST", body="this is a login request")
        assert response.status == 200

        op_url = urllib.parse.urljoin(uri, "/op")
        response, content = cookie_http.request(op_url, "POST", body="op request 1")
        assert response.status == 200

        time.sleep(1)
        response, content = cookie_http.request(op_url, "POST", body="op reques 2")
        assert response.status == 200
        expect_cookies = {"A": "1", "C": "3"}
        assert dict([ck.split("=") for ck in content.decode().split("; ")]) == expect_cookies

        time.sleep(1)
        response, content = cookie_http.request(op_url, "POST", body="op reques 3")
        assert response.status == 200
        expect_cookies = {"A": "1"}
        assert dict([ck.split("=") for ck in content.decode().split("; ")]) == expect_cookies


class HttpConnectionWithDNSResolve(httplib2.HTTPConnectionWithTimeout):
    def connect(self):
        host = "localhost" if self.host.endswith(".example.com") else self.host
        self.sock = self._create_connection((host, self.port), self.timeout, self.source_address)
        self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)


def test_cookie_manager_match(cookie_http):
    # httplib2 client always initiates new connection for new host name.
    # Close the connection after request so server_socket can accept the next
    # request.
    headers = {"connection": "close"}
    handler = tests.http_reflect_with_cookies(
        {
            "/login": ("A=1; domain=example.com", "B=2; Domain=example.com; Max-Age=100", "C=3"),
            "/login2": "D=4; domain=example.com; path=/path_a",
            "/path_a/path_b/login3": "E=5; domain=example.com",  # test default path
        },
        response_headers=headers,
    )

    with tests.server_request(handler, request_count=8, timeout=30) as uri:
        login_url = urllib.parse.urljoin(uri, "/login")
        response, content = cookie_http.request(
            login_url, "POST", body="this is a login request", connection_type=HttpConnectionWithDNSResolve
        )
        assert response.status == 200

        url_parsed = urllib.parse.urlparse(uri)
        netloc = "a.example.com:" + str(url_parsed.port)
        example_url = urllib.parse.urlunparse(
            (url_parsed.scheme, netloc, url_parsed.path, url_parsed.params, url_parsed.query, url_parsed.fragment)
        )
        op_url = urllib.parse.urljoin(example_url, "/op")
        response, content = cookie_http.request(
            op_url, "POST", body="op request 1", connection_type=HttpConnectionWithDNSResolve
        )
        assert response.status == 200
        expect_cookies = {"A": "1", "B": "2"}
        assert dict([ck.split("=") for ck in content.decode().split("; ")]) == expect_cookies

        login2_url = urllib.parse.urljoin(uri, "/login2")
        response, content = cookie_http.request(
            login2_url, "POST", body="this is a login request", connection_type=HttpConnectionWithDNSResolve
        )
        assert response.status == 200

        op_url = urllib.parse.urljoin(example_url, "/path_a/op?vvv=yes")
        response, content = cookie_http.request(
            op_url, "POST", body="op request 2", connection_type=HttpConnectionWithDNSResolve
        )
        assert response.status == 200
        expect_cookies = {"A": "1", "B": "2", "D": "4"}
        assert dict([ck.split("=") for ck in content.decode().split("; ")]) == expect_cookies

        op_url = urllib.parse.urljoin(example_url, "/path_b/op?vvv=yes")
        response, content = cookie_http.request(
            op_url, "POST", body="op request 3", connection_type=HttpConnectionWithDNSResolve
        )
        assert response.status == 200
        expect_cookies = {"A": "1", "B": "2"}
        assert dict([ck.split("=") for ck in content.decode().split("; ")]) == expect_cookies

        login3_url = urllib.parse.urljoin(uri, "/path_a/path_b/login3")
        response, content = cookie_http.request(
            login3_url, "POST", body="this is a login request", connection_type=HttpConnectionWithDNSResolve
        )
        assert response.status == 200

        op_url = urllib.parse.urljoin(example_url, "/path_a/op?vvv=yes")
        response, content = cookie_http.request(
            op_url, "POST", body="op request 4", connection_type=HttpConnectionWithDNSResolve
        )
        assert response.status == 200
        expect_cookies = {"A": "1", "B": "2", "D": "4"}
        assert dict([ck.split("=") for ck in content.decode().split("; ")]) == expect_cookies

        op_url = urllib.parse.urljoin(example_url, "/path_a/path_b/op")
        response, content = cookie_http.request(
            op_url, "POST", body="op request 5", connection_type=HttpConnectionWithDNSResolve
        )
        assert response.status == 200
        expect_cookies = {"A": "1", "B": "2", "D": "4", "E": "5"}
        assert dict([ck.split("=") for ck in content.decode().split("; ")]) == expect_cookies


def test_cookie_manager_with_onetime_cookie(cookie_http2):
    cookies = {"AAA": "111", "BBB": "222"}
    handler = tests.http_reflect_with_cookies()

    with tests.server_request(handler) as uri:
        url_parsed = urllib.parse.urlparse(uri)
        netloc = "a.example.com:" + str(url_parsed.port)
        example_url = urllib.parse.urlunparse(
            (url_parsed.scheme, netloc, url_parsed.path, url_parsed.params, url_parsed.query, url_parsed.fragment)
        )
        url = urllib.parse.urljoin(example_url, "/dir_b/dir_c/op")
        response, content = cookie_http2.request(
            url,
            "GET",
            body="this request include cookies from both one-time cookies and cookie jar",
            connection_type=HttpConnectionWithDNSResolve,
            cookies=cookies,
        )
        assert response.status == 200
        expect_cookies = {"g_a": "1", "g_b": "2", "g_c": "3", "AAA": "111", "BBB": "222", "ddd": "444"}
        assert dict([ck.split("=") for ck in content.decode().split("; ")]) == expect_cookies


@pytest.mark.parametrize("redirect_code", httplib2.REDIRECT_CODES)
def test_cookie_following_30x_redirect(redirect_code, cookie_http):
    # Test that the cookies are automatically follow 301 redirects
    cookie_http.follow_all_redirects = True

    # Python2.x httplib doesn't have this code.
    status_code = "308 Permanent Redirect" if redirect_code == 308 else redirect_code
    routes = {
        "": tests.http_response_bytes(
            status=status_code,
            headers={"set-cookie": ("A=1; Max-Age=100", "B=2"), "location": "/final"},
            body=b"set-cookie header sent",
        ),
        "/final": tests.http_reflect_with_cookies(),
    }
    with tests.server_route(routes, request_count=2) as uri:
        response, content = cookie_http.request(uri, "GET")

    assert response.status == 200
    destination = urllib.parse.urljoin(uri, "/final")
    assert response["content-location"] == destination
    assert response.previous.status == redirect_code
    expect_cookies = {"A": "1", "B": "2"}
    assert dict([ck.split("=") for ck in content.decode().split("; ")]) == expect_cookies
