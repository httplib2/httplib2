import os
import re
import time
import email
import calendar
from collections import namedtuple


RE_SPLIT_COOKIE = re.compile(r"(?:,)\s*(?=[^;, ]*?=[^;, ]*)")


CookieBase = namedtuple("Cookie", ["name", "value", "domain", "path", "expires", "secure"])


class Cookie(CookieBase):
    """Represent a Cookie with all attributes."""

    def is_expired(self):
        return self.expires and (time.time() >= self.expires)

    @staticmethod
    def normalize_path(path):
        # A normal cookie path always starts with / and ends with /
        path = path or "/"
        if not path.startswith("/"):
            path = "/" + path

        if not path.endswith("/"):
            path += "/"
        return path

    @staticmethod
    def create(name, value, domain=None, path=None, max_age=None, expires=None, secure=False):
        """Create a cookie by the given attributes.

        domain:
            Host to which the cookie will be sent.

            Dot(.) is a special domain in httplib2, that indicates the cookie
            can be used over all domains. It's also the default value if the
            domain is not specified.

        path:
            Path to which the cookie will be sent. The default path is "/" if
            not specified.

        max_age:
            Number of seconds until the cookie expires. A zero or negative
            number will expire the cookie immediately.

            max_age has higher priority than 'expires' date.

        expires:
            The maximum lifetime of the cookie as an HTTP-date timestamp.
            Format:
                <day-name>, <day> <month> <year> <hour>:<minute>:<second> GMT
            Example: Wed, 21 Oct 2015 07:28:00 GMT

        secure:
            A secure cookie is only sent to the server when a request is made
            with the https: scheme. False by default.
        """
        if max_age is not None:
            expires = time.time() + int(max_age)
        elif expires is not None:
            expires = calendar.timegm(email.utils.parsedate_tz(expires))
        else:
            expires = None

        domain = domain or "."
        path = Cookie.normalize_path(path)

        return Cookie(name, value, domain, path, expires, secure)


class CookieJar(object):
    """Store and manipulate HTTP Cookies."""

    def __init__(self, init_cookies=None, filename=None):
        """
        init_cookies:
            A dict of cookies {<name>: <value>} to initialize the cookie jar.
            These cookies are suitable for use over all domains and paths and
            never expire.

        filename:
            Cookie file to be loaded and saved. The file will be kept updating
            when any cookies are added or deleted.
        """

        # Cookies are stored in hierarchy: domain > path > name > cookie
        self._cookies = {}

        self.filename = filename
        if filename and os.path.isfile(filename):
            self.load(filename)

        for name, value in (init_cookies or {}).items():
            cookie = Cookie.create(name, value)
            self.set(cookie)

    def load(self, filename):
        """Load cookies from file.

        Cookie file format spec:
            https://curl.haxx.se/docs/http-cookies.html
        """
        with open(filename, "rt") as fd:
            for line in fd:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue  # blank line

                domain, _, path, secure, expires, name, value = line.split("\t")

                expires = int(expires) if expires else None
                secure = secure == "TRUE"

                cookie = Cookie(name, value, domain, path, expires, secure)

                cookielist = self._cookies.setdefault(domain, {}).setdefault(path, {})
                cookielist[name] = cookie

    def save(self, filename):
        """Save cookies to file.

        Cookie file format spec:
            https://curl.haxx.se/docs/http-cookies.html

        Note that global cookies (domain attribute is dot) will not be saved.
        """
        file_header = """\
# Netscape HTTP Cookie File
# https://curl.haxx.se/docs/http-cookies.html
# This is a generated file! Do not edit.

"""
        with open(filename, "wt") as fd:
            fd.write(file_header)

            for cookie in self.iter():
                if cookie.is_expired() or cookie.domain == ".":
                    continue

                secure = "TRUE" if cookie.secure else "FALSE"
                with_subdomain = "TRUE" if cookie.domain.startswith(".") else "FALSE"

                if cookie.expires is not None:
                    expires = str(int(cookie.expires))
                else:
                    expires = ""

                cookie_line = "\t".join(
                    [cookie.domain, with_subdomain, cookie.path, secure, expires, cookie.name, cookie.value]
                )
                fd.write(cookie_line + "\n")

    def set(self, cookie, value=None, **kwargs):
        """Put a new cookie or update the existing cookie to this cookie jar.

        cookie:
            Either a cookie name or cookie object.
            In case it's a cookie name, the value must be provided. And other
            optional parameters are the same as Cookie.create().
        """
        if not isinstance(cookie, Cookie):
            assert cookie is not None and value is not None, "name and value must be given to create a cookie"
            cookie = Cookie.create(cookie, value, **kwargs)
        path_cookies = self._cookies.setdefault(cookie.domain, {}).setdefault(cookie.path, {})
        path_cookies[cookie.name] = cookie

        if self.filename and cookie.domain != ".":
            self.save(self.filename)

    def get(self, domain=None, path=None, name=None):
        """Get cookies filtered by domain, path or name

        If one parameter is specified, the preceding parameter(s) must also
        be specified.

        If name is specified, only returns the cookie with that name.
        Otherwise, return a cookie list.

        Return KeyError if no matching cookie found.
        """
        if name is not None:
            assert domain and path, "domain and path must be given to get a cookie by name"
            path = Cookie.normalize_path(path)
            return self._cookies[domain][path][name]

        if path is not None:
            assert domain, "domain must be given to get cookies by path"
            path = Cookie.normalize_path(path)
            path_cookies = self._cookies[domain][path]
            return list(path_cookies.values())

        if domain is not None:
            return [ck for pc in self._cookies[domain].values() for ck in pc.values()]

        return [ck for dc in self._cookies.values() for pc in dc.values() for ck in pc.values()]

    def iter(self, domain=None, path=None):
        """Return an iterator of cookies filtered by domain, path.

        If domain and path are not specified, all cookies are returned.

        Raise KeyError if no matching cookie found.
        """
        if path is not None:
            assert domain, "domain must be given to get cookies by path"
            path = Cookie.normalize_path(path)
            for ck in self._cookies[domain][path].values():
                yield ck
            return

        if domain is not None:
            for pc in self._cookies[domain].values():
                for ck in pc.values():
                    yield ck
            return

        for dc in self._cookies.values():
            for pc in dc.values():
                for ck in pc.values():
                    yield ck

    def clear(self, domain=None, path=None, name=None):
        """Delete cookies by domain, path, or name.

        If one parameter is specified, the preceding parameter(s) must also
        be specified.

        No error if no matching cookie found.
        """
        try:
            if name is not None:
                assert domain and path, "domain and path must be given to remove a cookie by name"
                path = Cookie.normalize_path(path)
                del self._cookies[domain][path][name]
                return

            if path is not None:
                assert domain, "domain must be given to remove cookies by path"
                path = Cookie.normalize_path(path)
                del self._cookies[domain][path]
                return

            if domain is not None:
                del self._cookies[domain]
                return
        except KeyError:
            return

        self._cookies = {}

        if self.filename:
            self.save()

    def _match_path(self, request_uri, cookie_path):
        return cookie_path[:-1] == request_uri or request_uri.startswith(cookie_path)

    def _match_domain(self, request_host, cookie_domain):
        if cookie_domain.startswith("."):
            return cookie_domain == "." or request_host.endswith(cookie_domain)
        return request_host == cookie_domain

    def get_header(self, request_host, request_uri, is_https):
        """Get the Cookie header to be applied to the request."""
        cookie_header = []

        for domain, domain_cookies in self._cookies.items():
            if not self._match_domain(request_host, domain):
                continue

            for path, cookies in domain_cookies.items():
                if not self._match_path(request_uri, path):
                    continue

                for cookie in cookies.values():
                    if cookie.is_expired():
                        continue

                    if cookie.secure and not is_https:
                        continue

                    cookie_header.append("{0}={1}".format(cookie.name, cookie.value))

        return "; ".join(cookie_header)

    @staticmethod
    def parse_iter(header):
        """An iterator to parse cookies in HTTP-style header(Set-Cookie).

        cookie header example:
            sid=vBj3zbrmgynsZ8ggVpmSIOc9bXAueT3z; HttpOnly;

        It may contain multiple cookies separated by comma(RFC 2109).

        Example:
            BD_NOT_HTTPS=1; path=/; Max-Age=300, BIDUPSID=D2504FE922735DE;
            expires=Thu, 31-Dec-37 23:55:55 GMT; max-age=2147483647; path=/;
            domain=.example.com, PSTM=1595329370

        The 'expires' also contains comma. Be careful!
        """
        if not header:
            return

        for cookie_str in RE_SPLIT_COOKIE.split(header):
            cookie, *attribute_list = cookie_str.split(";")
            name, value = cookie.split("=")
            cookie = {"name": name, "value": value}

            for attr_str in attribute_list:
                attr, *val = attr_str.split("=", 1)
                attr = attr.strip()
                attr_l = attr.lower()

                if attr_l == "max-age":
                    cookie["max_age"] = val[0]
                elif attr_l == "expires":
                    cookie["expires"] = val[0]
                elif attr_l == "domain":
                    domain = val[0].lower()
                    if not domain.startswith("."):
                        domain = "." + domain
                    cookie["domain"] = domain
                elif attr_l == "path":
                    cookie["path"] = val[0]
                elif attr_l == "secure":
                    cookie["secure"] = True
                elif val:
                    # Other attrbute not handled
                    cookie[attr] = val[0]
                else:
                    # Other name-only attrbute not handled
                    cookie[attr] = True

            yield cookie

    def extract_header(self, request_host, request_uri, header):
        """Extract cookies from HTTP-style header(Set-Cookie) and save them
        to cookie jar.

        For an expired cookie, just save it and overwrite the old one to
        disable the cookie.
        """
        for cookie in self.parse_iter(header):
            domain = cookie.get("domain", request_host)
            path = cookie.get("path", os.path.dirname(request_uri))

            cookie = Cookie.create(
                cookie["name"],
                cookie["value"],
                domain,
                path,
                cookie.get("max_age"),
                cookie.get("expires"),
                cookie.get("secure"),
            )

            self.set(cookie)


class NullCookieJar(object):
    def __init__(self):
        pass

    def load(self, filename):
        pass

    def save(self, filename):
        pass

    def set(self, cookie, value=None, **kwargs):
        pass

    def get(self, domain=None, path=None, name=None):
        return []

    def iter(self, domain=None, path=None):
        return
        yield

    def clear(self, domain=None, path=None, name=None):
        pass

    def get_header(self, request_host, request_uri, is_https):
        return ""

    @staticmethod
    def parse_iter(header):
        return
        yield

    def extract_header(self, request_host, request_uri, header):
        pass
