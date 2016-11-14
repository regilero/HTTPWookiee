#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
from httpwookiee.http.client import Client  # , ClosedSocketError
from httpwookiee.config import Register
from httpwookiee.core.base import BaseTest
from httpwookiee.core.result import TextStatusResult
from httpwookiee.http.request import Request
from httpwookiee.core.tools import outmsg, Tools
import inspect
import sys
import unittest


class AbstractTestRegular(BaseTest):

    def test_0001_regular(self):
        "regular simple HTTP query."
        self.real_test = "{0}".format(inspect.stack()[0][3])

        Register.flag('available', False)
        self._end_regular_query()
        Register.flag('available', True)

    def test_0002_regular_09(self):
        "regular simple HTTP/0.9 query."
        self.real_test = "{0}".format(inspect.stack()[0][3])

        self._prepare_simple_test()
        self.req.version_09 = True
        status_map = {
            self.STATUS_ACCEPTED: self.GRAVITY_WARNING,
            self.STATUS_TRANSMITTED: self.GRAVITY_CRITICAL,
        }
        self._end_almost_regular_query(status_map=status_map,
                                       http09_allowed=True,
                                       regular_expected=True)
        if self.status in [self.STATUS_09OK, self.STATUS_09DOWNGRADE]:
            Register.flag('http_09_support', True)
        self.assertIn(self.status,
                      [self.STATUS_09OK,
                       self.STATUS_ACCEPTED,
                       self.STATUS_REJECTED,
                       self.STATUS_ERR400,
                       self.STATUS_501_NOT_IMPLEMENTED,
                       self.STATUS_09DOWNGRADE],
                      'Should be a 0.9 headerless response. Or a refusal.'
                      ' or a valid http 1.0 response.'
                      'Bad response status {0}.'.format(self.status))

    def test_0003_regular_keepalive(self):
        "Chain two regular queries in a keepalive conn."
        self.real_test = "{0}".format(inspect.stack()[0][3])
        self._prepare_simple_test()
        self.req.add_header('Connection', 'keep-alive')
        responses2 = False
        with Client() as csock:
            csock.send(self.req)
            responses1 = csock.read_all()
            outmsg(str(responses1))
            self.analysis(responses1,
                          http09_allowed=False,
                          regular_expected=True)
            if self.status == self.STATUS_REJECTED:
                Register.flag('keepalive', False)

            self.assertIn(self.status,
                          [self.STATUS_ACCEPTED],
                          'Bad response status {0}'.format(self.status))
            if responses1.count:
                # TODO: check Connection: keep-alive on response headers
                self._prepare_simple_test()
                csock.send(self.req)
                # inform server we are done with sending data
                # FIXME: this is failing with Nginx (at least)
                # try:
                #     csock.close_sending()
                # except ClosedSocketError:
                #     Register.flag('keepalive', False)
                #     self.setGravity(self.GRAVITY_UNKNOWN)
                #     raise AssertionError('Connection closed before reading')
                responses2 = csock.read_all()
                outmsg(str(responses2))

        self.analysis(responses2,
                      http09_allowed=False,
                      regular_expected=True)

        self.assertIn(self.status,
                      [self.STATUS_ACCEPTED],
                      'Bad response status {0}'.format(self.status))


class AbstractTestRegularPipe(BaseTest):

    def __init__(self, methodName="runTest"):
        super(AbstractTestRegularPipe, self).__init__(methodName)
        self.send_mode = self.SEND_MODE_PIPE

    def test_0004_regular_pipeline(self):
        "Chain two regular queries in a pipeline (no waits between requests)."
        self.real_test = "{0}".format(inspect.stack()[0][3])
        self._prepare_pipe_test()
        responses = self.send_queries()
        if responses.count == 1:
            Register.flag('pipelining', False)
        self._end_regular_query(responses,
                                expected_number=2)

    def test_0005_bad_pipeline(self):
        "Chain 3 queries, second is bad, should stop the response stream."
        self.real_test = "{0}".format(inspect.stack()[0][3])
        self._prepare_pipe_test()
        self.req2.set_location(Tools.NULL,
                               random=True)
        self.req3 = Request(id(self))
        self.req3.set_location(self.config.get('SERVER_DEFAULT_LOCATION'),
                               random=True)
        with Client() as csock:
            csock.send(self.req1)
            csock.send(self.req2)
            csock.send(self.req3)
            responses = csock.read_all()
            outmsg(str(responses))

        self.analysis(responses,
                      expected_number=2,
                      regular_expected=False)

        self.assertTrue((responses.count <= 2))
        if (responses.count > 1):
            self.assertIn(self.status,
                          [self.STATUS_REJECTED, self.STATUS_ERR400],
                          'Bad response status {0}'.format(self.status))


class TestRegular(AbstractTestRegular):
    pass


class TestRegularPipe(AbstractTestRegularPipe):
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
