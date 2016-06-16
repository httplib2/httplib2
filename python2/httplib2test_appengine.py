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

# Ensure that we are not loading the httplib2 version included in the Google
# App Engine SDK.
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))


class AberrationsTest(unittest.TestCase):

  def setUp(self):
    self.testbed = testbed.Testbed()
    self.testbed.activate()
    self.testbed.init_urlfetch_stub()
    self._original_server_software = os.environ['SERVER_SOFTWARE']
    del os.environ['SERVER_SOFTWARE']
    global httplib2
    import httplib2

  def tearDown(self):
    self.testbed.deactivate()
    os.environ['SERVER_SOFTWARE'] = self._original_server_software
    del globals()['httplib2']

  def testConnectionInit(self):
    self.assertNotEqual(
      httplib2.SCHEME_TO_CONNECTION['https'], httplib2.AppEngineHttpsConnection)
    self.assertNotEqual(
      httplib2.SCHEME_TO_CONNECTION['http'], httplib2.AppEngineHttpConnection)


if __name__ == '__main__':
    unittest.main()
