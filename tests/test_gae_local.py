# -*- coding: utf-8 -*-
"""Tests httplib2 on Google App Engine locally.

Requires Python 2.7 and Google App Engine SDK. See
https://cloud.google.com/appengine/docs/standard/python/download.

Google App Engine Standard Environment only supports Python 2.7 at the moment.
Google App Engine Python Flexible Environment however supports Python 3.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import mock
import os
import pytest
import sys
import unittest

sys.path.insert(0, "/usr/local/google-cloud-sdk/platform/google_appengine")

import dev_appserver

dev_appserver.fix_sys_path()

from google.appengine.ext import testbed

# Ensure that we are not loading the httplib2 version included in the Google
# App Engine SDK.
sys.path.insert(
    0,
    os.path.join(
        os.path.split(os.path.dirname(os.path.realpath(__file__)))[0], "python2"
    ),
)

_DISABLED_ON_TRAVIS_MESSAGE = (
    "Note that there is no official pip package for Google App Engine SDK so "
    "disabling all test cases on Travis."
)


@pytest.mark.skipif(
    os.environ.get("TRAVIS_PYTHON_VERSION") is not None,
    reason=_DISABLED_ON_TRAVIS_MESSAGE,
)
class Test(object):
    def setup_method(self):
        self._testbed = None

    def teardown_method(self):
        if self._testbed is not None:
            self._testbed.deactivate()
        global httplib2
        del sys.modules["httplib2"]
        del httplib2

    def _configure(self, setup_testbed=True, import_httplib2=True):
        if setup_testbed:
            self._testbed = testbed.Testbed()
            self._testbed.activate()
            self._testbed.init_urlfetch_stub()
        if import_httplib2:
            global httplib2
            import httplib2

    def test_gae_environment(self):
        self._configure()
        assert httplib2.SCHEME_TO_CONNECTION["http"] == httplib2.AppEngineHttpConnection
        assert (
            httplib2.SCHEME_TO_CONNECTION["https"] == httplib2.AppEngineHttpsConnection
        )
        assert (
            not httplib2.SCHEME_TO_CONNECTION["http"]
            == httplib2.HTTPConnectionWithTimeout
        )
        assert (
            not httplib2.SCHEME_TO_CONNECTION["https"]
            == httplib2.HTTPSConnectionWithTimeout
        )

    def test_get_http_returns_200(self):
        self._configure()
        http = httplib2.Http()
        response, content = http.request("http://www.google.com")
        assert len(http.connections) == 1
        assert response.status == 200
        assert response["status"] == "200"

    def test_get_https_bypass_proxy_and_returns_200(self):
        self._configure()
        http = httplib2.Http(
            proxy_info=httplib2.ProxyInfo(
                httplib2.socks.PROXY_TYPE_HTTP, "255.255.255.255", 8001
            )
        )
        response, content = http.request("https://www.google.com")
        assert len(http.connections) == 1
        assert response.status == 200
        assert response["status"] == "200"

    @mock.patch.dict("os.environ", {"SERVER_SOFTWARE": ""})
    def test_standard_environment(self):
        self._configure(setup_testbed=False)
        assert (
            httplib2.SCHEME_TO_CONNECTION["http"] == httplib2.HTTPConnectionWithTimeout
        )
        assert (
            httplib2.SCHEME_TO_CONNECTION["https"]
            == httplib2.HTTPSConnectionWithTimeout
        )
