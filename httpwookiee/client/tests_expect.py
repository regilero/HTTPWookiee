#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
from httpwookiee.config import Register
from httpwookiee.core.base import BaseTest
from httpwookiee.core.result import TextStatusResult
from httpwookiee.core.tools import Tools
import inspect
import sys
import unittest


class AbstractTestExpect(BaseTest):

    def __init__(self, *args, **kwargs):
        super(AbstractTestExpect, self).__init__(*args, **kwargs)
        # for RP mode message analysis
        self.transmission_zone = Tools.ZONE_HEADERS
        self.send_mode = self.SEND_MODE_UNIQUE

    def test_0050_preflight_regular_chunked_get(self):
        """Let's start by a regular GET with chunked body

        """
        self.real_test = "{0}".format(inspect.stack()[0][3])
        self.setGravity(self.GRAVITY_MINOR)
        self.req.set_method('GET')
        self.req.add_header('Expect', '100-continue')
        self._end_almost_regular_query()
        Register.flag('get_expect_{0}'.format(self.reverse_proxy_mode),
                      (self.status == self.STATUS_ACCEPTED))
        Register.flag('managed_get_expect_{0}'.format(self.reverse_proxy_mode),
                      (self.interim_responses == 1))
        self.assertIn(self.status,
                      [self.STATUS_ACCEPTED, self.STATUS_ERR417],
                      'Bad response status {0}'.format(self.status))

    def test_0051_expect(self):
        "Regular Expect HTTP query. We should have on Interim response, or 417"

        self.real_test = "{0}".format(inspect.stack()[0][3])
        self.setGravity(self.GRAVITY_MINOR)
        self.req.set_method('GET')
        self.req.add_header('Expect', '100-continue')
        self._end_almost_regular_query()
        if self.status is not self.STATUS_ERR417:
            self.assertEqual(self.interim_responses, 1)


class TestExpect(AbstractTestExpect):
    pass


if __name__ == '__main__':
    testcases = []
    for name, obj in inspect.getmembers(sys.modules[__name__]):
        if 'Test' == name[:4] and inspect.isclass(obj):
            testcases.append(obj)
    suites = [unittest.TestLoader().loadTestsFromTestCase(classobj)
              for classobj in testcases]
    testSuite = unittest.TestSuite(suites)
    unittest.TextTestRunner(resultclass=TextStatusResult,
                            verbosity=2,
                            buffer=True).run(testSuite)
