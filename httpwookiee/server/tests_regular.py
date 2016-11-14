#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
from httpwookiee.core.result import TextStatusResult
from httpwookiee.core.proxy import ProxyTest, AbstractEchoProxy
from httpwookiee.core.testrunner import WookieeTestRunner
from httpwookiee.core.testloader import WookieeTestLoader
from httpwookiee.core.behavior import Behavior
from httpwookiee.client.tests_regular import (AbstractTestRegular,
                                              AbstractTestRegularPipe)

import sys


class TestRegularProxy(ProxyTest, AbstractTestRegular):

    def __init__(self, methodName="runTest"):
        super(TestRegularProxy, self).__init__(methodName)
        self.send_mode = self.SEND_MODE_UNIQUE

    def getBehavior(self):
        "What is the server expected behavior?"
        behavior = Behavior()
        behavior.accept_invalid_request = True
        behavior.add_wookiee_response = False
        behavior.keep_alive_on_error = True
        return behavior

    def test_00_proxy_regular(self):
        """Basic test for a regular query to a reverse proxy of our server.

        So it looks simple, but a lot of things happen. Our final server
        backend thread is configured to catch a specific query (id in query
        args). The request goes to the reverse proxy, which should exists and
        proxy our bckend on url defined by BACKEND_LOCATION in the config.
        Our server backend thread will respond and the reverse proxy will
        send us back this response.
        TODO:
        In case of something missing in the env this test will fail and
        all other tests using ProxyTest should be avoided.
        """
        self._end_regular_query()

    def test_wookiee(self):

        wlocation = self.get_wookiee_location()
        self.req.set_location(wlocation, random=True)
        self._end_almost_regular_query()
        self.assertEqual(self.status,
                         self.STATUS_WOOKIEE,
                         'Wookiee response is Expected, strange.')


class TestRegularProxyPipe(AbstractEchoProxy, AbstractTestRegularPipe):

    def _analyze_valid_echo_queries(self):
        "Having a backend received query which is not invalid, want to check?"
        if not self.backend_queries.messages[0].errors == {}:
            # We have at least one warning on the first messages
            # we estimate this is a problem
            self.setStatus(self.STATUS_TRANSMITTED)
            self._analyze_invalid_echo_queries()


if __name__ == '__main__':
    tl = WookieeTestLoader()
    testSuite = tl.loadTestsFromModule(sys.modules[__name__])
    # without stream forced here python 2.7 is failing
    WookieeTestRunner(resultclass=TextStatusResult,
                      verbosity=2,
                      buffer=True,
                      stream=sys.stderr).run(testSuite)
