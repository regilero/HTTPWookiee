#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# from httpwookiee.config import ConfigFactory
from httpwookiee.config import Register
from httpwookiee.core.base import BaseTest
from httpwookiee.core.tools import Tools
from httpwookiee.core.result import TextStatusResult
from httpwookiee.core.testloader import WookieeTestLoader
from httpwookiee.core.testrunner import WookieeTestRunner

import unittest
import inspect
import sys
# ###################################### TESTS #########################


class AbstractTestHost(BaseTest):
    """Test host header & absolute uri tricks.

    Basically the problem is that the Host header is used to find
    the right name-based VirtualHost, BUT an old syntax in the first
    line, with absolute uri, has to be supported.

        # This is for Host foo
        GET /a HTTP/1.1\r\n
        Host: foo\r\n
        \r\n

        # This is for Host foo (same request)
        GET http://foo/a HTTP/1.1\r\n
        Host: bar\r\n
        \r\n

    Host header is ignored when abolsute uri is used, but it may be
    transmitted to applications with the bad contet, or worse,
    transmitted to backends by a reverse proxy.
    """

    tested_char = u''
    tested_char_name = u'asbtract'

    def __init__(self, *args, **kwargs):
        super(AbstractTestHost, self).__init__(*args, **kwargs)
        # we do not use pipelines
        self.send_mode = self.SEND_MODE_UNIQUE

    def test_5000_preflight_default_vhost_absolute(self):
        """Check that the default vhost works and can be identified

        """
        self.real_test = "{0}_{1}".format(inspect.stack()[0][3],
                                          self.tested_char_name)
        self.setGravity(self.GRAVITY_MINOR)
        if Register.hasFlag('abs_default_vhost', default=False):
            self.skipTest("Preflight test already done.")
        self.req.set_method('GET')
        target_host = self.config.get('SERVER_HOST')
        self.req.host = self.config.get('SERVER_HOST')
        self.req.location = 'http://{0}{1}'.format(
            target_host, self.req.location)
        self._end_almost_regular_query(regular_expected=True)
        Register.flag('abs_default_vhost', self.status == self.STATUS_ACCEPTED)
        self.assertIn(self.status,
                      [self.STATUS_ACCEPTED],
                      'Bad response status {0}'.format(self.status))

    def test_5001_absolute_uri_hosts_behavior_default(self):
        """Using absolute URI, target default Vhost,inject bad Host chars.

        """
        self.real_test = "{0}_{1}".format(inspect.stack()[0][3],
                                          self.tested_char_name)
        if not Register.hasFlag('abs_default_vhost', default=False):
            self.skipTest("Default Virtualhost is not working"
                          " in absolute mode.")
        self.setGravity(self.GRAVITY_MINOR)
        self.req.set_method('GET')
        # Absolute URI trick
        target_host = self.config.get('SERVER_HOST')
        self.req.host = '{0}'.format(self.tested_char)
        self.req.location = 'http://{0}{1}'.format(
            target_host,
            self.get_non_default_location(
                with_prefix=self.use_backend_location))

        # for RP mode:
        self.transmission_map = {
            'Host: {0}\r\n'.format(
                self.tested_char): self.STATUS_TRANSMITTED_EXACT,
        }

        self._add_default_status_map(
            valid=False,
            always_allow_rejected=True
        )

        # local changes
        self.status_map[self.STATUS_TRANSMITTED_EXACT] = self.GRAVITY_WARNING
        self._end_1st_line_query()
        self._end_expected_error()


class AbstractTestNonDefaultHost(BaseTest):

    tested_char = u''
    tested_char_name = u'asbtract'

    def __init__(self, *args, **kwargs):
        super(AbstractTestNonDefaultHost, self).__init__(*args, **kwargs)
        # we do not use pipelines
        self.send_mode = self.SEND_MODE_UNIQUE

    def _get_expected_content(self):
        return self.config.get(
            'SERVER_NON_DEFAULT_LOCATION_CONTENT').encode('utf8')

    def test_5002_preflight_non_default_vhost(self):
        """Check that the non default vhost works and can be identified

        """
        # FIXME: on preflight: detect bad proxy configuration with
        # empty echo query. Means the 2nd vhost proxy is not working
        # TODO: do this test also on first proxy and test_regular
        self.real_test = "{0}_{1}".format(inspect.stack()[0][3],
                                          self.tested_char_name)
        if not self.config.getboolean('MULTIPLE_HOSTS_TESTS'):
            self.skipTest("Tests with multiple virtualhosts are not activated"
                          " in configuration.")
        if Register.hasFlag('non_default_vhost', default=False):
            self.skipTest("Preflight test already done.")
        self.setGravity(self.GRAVITY_MINOR)
        self.req.set_method('GET')
        self.req.host = self.config.get('SERVER_NON_DEFAULT_HOST')
        self.req.location = self.get_non_default_location(
            with_prefix=self.use_backend_location)
        self._end_almost_regular_query(regular_expected=True)
        Register.flag('non_default_vhost',
                      self.status == self.STATUS_ACCEPTED)
        self.assertIn(self.status,
                      [self.STATUS_ACCEPTED],
                      'Bad response status {0}'.format(self.status))

    def test_5003_preflight_non_default_vhost_absolute(self):
        """Check that the non default vhost works in absolute mode

        """
        self.real_test = "{0}_{1}".format(inspect.stack()[0][3],
                                          self.tested_char_name)
        if not self.config.getboolean('MULTIPLE_HOSTS_TESTS'):
            self.skipTest("Tests with multiple virtualhosts are not activated"
                          " in configuration.")
        if not Register.hasFlag('non_default_vhost', default=False):
            self.skipTest("Alternate Virtualhost is not working.")
        if not Register.hasFlag('abs_default_vhost', default=False):
            self.skipTest("Default Virtualhost is not working"
                          " in absolute mode.")
        if Register.hasFlag('abs_non_default_vhost'):
            self.skipTest("Preflight test already done.")
        self.setGravity(self.GRAVITY_MINOR)
        self.req.set_method('GET')
        # Absolute URI trick
        target_host = self.config.get('SERVER_NON_DEFAULT_HOST')
        self.req.host = self.config.get('SERVER_HOST')
        self.req.location = 'http://{0}{1}'.format(
            target_host,
            self.get_non_default_location(
                with_prefix=self.use_backend_location))
        self._end_almost_regular_query(regular_expected=True)
        Register.flag('abs_non_default_vhost',
                      self.status == self.STATUS_ACCEPTED)
        self.assertIn(self.status,
                      [self.STATUS_ACCEPTED],
                      'Bad response status {0}'.format(self.status))


class TestHost(AbstractTestHost):
    pass


class TestNonDefaultHost(AbstractTestNonDefaultHost):
    pass


def load_tests(loader, tests, pattern):
    test_cases = unittest.TestSuite()
    tl = WookieeTestLoader()

    TestClass = type('TestHost_space', (TestHost,),
                     {'tested_char_name': 'space',
                      'tested_char': Tools.SP})
    test_cases.addTests(tl.loadTestsFromTestCase(TestClass))
    TestClass = type('TestNonDefaultHost_space', (TestNonDefaultHost,),
                     {'tested_char_name': 'space',
                      'tested_char': Tools.SP})
    test_cases.addTests(tl.loadTestsFromTestCase(TestClass))
    for charname, char in Tools.CONTROL_CHARS.items():
        TestClass = type('TestHost_{0}'.format(charname),
                         (TestHost,), {'tested_char_name': charname,
                                       'tested_char': char})
        test_cases.addTests(tl.loadTestsFromTestCase(TestClass))
    return test_cases


if __name__ == '__main__':
    tl = WookieeTestLoader()
    testSuite = tl.loadTestsFromModule(sys.modules[__name__])
    # without stream forced here python 2.7 is failing
    WookieeTestRunner(resultclass=TextStatusResult,
                      verbosity=2,
                      buffer=True,
                      stream=sys.stderr).run(testSuite)
