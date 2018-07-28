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

# For local testing.
sys.path.insert(0, "/usr/local/google-cloud-sdk/platform/google_appengine")

try:
    import dev_appserver

    dev_appserver.fix_sys_path()
    from google.appengine.ext import testbed
except ImportError:
    if os.environ.get("TRAVIS_PYTHON_VERSION") is not None:
        pytestmark = pytest.mark.skip(
            "Unable to import Google App Engine SDK. Skipping all tests."
        )
    else:
        raise

# For local testing. Ensure that we are not loading the httplib2 version
# included in the Google App Engine SDK.
if os.environ.get("TRAVIS_PYTHON_VERSION") is None:
    _parent_dir = '/'.join(os.path.realpath(__file__).split('/')[:-2])
    sys.path.insert(0, os.path.join(_parent_dir, "python2"))


@pytest.mark.skipif(
    os.environ.get("TRAVIS_PYTHON_VERSION") not in (None, "2.7"),
    reason="TODO: Requires further testing with Google SDK & Python 3.",
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

    def test_get_http_returns_200(self):
        self._configure()
        self._verify_gae_environment()
        http = httplib2.Http()
        response, _ = http.request("http://www.google.com")
        assert len(http.connections) == 1
        assert response.status == 200
        assert response["status"] == "200"

    def test_get_https_bypasses_proxy_and_returns_200(self):
        self._configure()
        self._verify_gae_environment()
        http = httplib2.Http(
            proxy_info=httplib2.ProxyInfo(
                httplib2.socks.PROXY_TYPE_HTTP, "255.255.255.255", 8001
            )
        )
        response, _ = http.request("https://www.google.com")
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

    def _configure(self, setup_testbed=True, import_httplib2=True):
        if setup_testbed:
            self._testbed = testbed.Testbed()
            self._testbed.activate()
            self._testbed.init_urlfetch_stub()
        if import_httplib2:
            global httplib2
            import httplib2

    def _verify_gae_environment(self):
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
