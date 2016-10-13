"""Tests for httplib2 on Google App Engine."""

import mock
import os
import sys
import unittest

APP_ENGINE_PATH='/usr/local/google_appengine'

sys.path.insert(0, APP_ENGINE_PATH)

import dev_appserver
dev_appserver.fix_sys_path()

from google.appengine.ext import testbed
from google.appengine.api.urlfetch import set_default_fetch_deadline

# Ensure that we are not loading the httplib2 version included in the Google
# App Engine SDK.
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))

# Ensure that httplib2 will use the patched httplib version later
if sys.version_info >= (2, 7):
    import google.appengine.dist27.httplib
    sys.modules["httplib"] = google.appengine.dist27.httplib
else:
    import google.appengine.dist.httplib
    sys.modules["httplib"] = google.appengine.dist.httplib
import httplib


class AberrationsTest(unittest.TestCase):

  def setUp(self):
    self.testbed = testbed.Testbed()
    self.testbed.activate()
    self.testbed.init_urlfetch_stub()

  def tearDown(self):
    self.testbed.deactivate()

  @mock.patch.dict('os.environ', {'SERVER_SOFTWARE': ''})
  def testConnectionInit(self):
    global httplib2
    import httplib2
    self.assertNotEqual(
      httplib2.SCHEME_TO_CONNECTION['https'], httplib2.AppEngineHttpsConnection)
    self.assertNotEqual(
      httplib2.SCHEME_TO_CONNECTION['http'], httplib2.AppEngineHttpConnection)
    del globals()['httplib2']


class AppEngineHttpTest(unittest.TestCase):

  def setUp(self):
    self.testbed = testbed.Testbed()
    self.testbed.activate()
    self.testbed.init_urlfetch_stub()
    global httplib2
    import httplib2
    reload(httplib2)

  def tearDown(self):
    self.testbed.deactivate()
    del globals()['httplib2']

  def testConnectionInit(self):
    self.assertEqual(
      httplib2.SCHEME_TO_CONNECTION['https'], httplib2.AppEngineHttpsConnection)
    self.assertEqual(
      httplib2.SCHEME_TO_CONNECTION['http'], httplib2.AppEngineHttpConnection)

  def testGet(self):
    http = httplib2.Http()
    response, content = http.request("http://www.google.com")
    self.assertEqual(httplib2.SCHEME_TO_CONNECTION['https'],
                     httplib2.AppEngineHttpsConnection)
    self.assertEquals(1, len(http.connections))
    self.assertEquals(response.status, 200)
    self.assertEquals(response['status'], '200')

  def testTimeout(self):
    with self.assertRaises(httplib.HTTPException):
        set_default_fetch_deadline(1)
        http = httplib2.Http()
        response, content = http.request("http://httpbin.org/delay/2")

  def testProxyInfoIgnored(self):
    http = httplib2.Http(proxy_info=mock.MagicMock())
    response, content = http.request("http://www.google.com")
    self.assertEquals(response.status, 200)


if __name__ == '__main__':
    unittest.main()
