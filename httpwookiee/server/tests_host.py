#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
from httpwookiee.core.result import TextStatusResult
from httpwookiee.core.proxy import ProxyTest
from httpwookiee.core.testrunner import WookieeTestRunner
from httpwookiee.core.testloader import WookieeTestLoader
from httpwookiee.core.behavior import Behavior
from httpwookiee.core.tools import Tools
from httpwookiee.client.tests_host import (AbstractTestHost,
                                           AbstractTestNonDefaultHost)

import sys
import unittest


class TestNonDefaultHostProxy(ProxyTest, AbstractTestNonDefaultHost):

    def __init__(self, methodName="runTest"):
        super(TestNonDefaultHostProxy, self).__init__(methodName)
        self.send_mode = self.SEND_MODE_UNIQUE

    def getBehavior(self):
        "What is the server expected behavior?"
        behavior = Behavior()
        behavior.accept_invalid_request = True
        behavior.add_wookiee_response = False
        behavior.keep_alive_on_error = True
        behavior.alt_content = True
        return behavior


class TestHostProxy(ProxyTest, AbstractTestHost):

    def __init__(self, methodName="runTest"):
        super(TestHostProxy, self).__init__(methodName)
        self.send_mode = self.SEND_MODE_UNIQUE

    def getBehavior(self):
        "What is the server expected behavior?"
        behavior = Behavior()
        behavior.accept_invalid_request = True
        behavior.add_wookiee_response = False
        behavior.keep_alive_on_error = True
        behavior.alt_content = False
        return behavior


def load_tests(loader, tests, pattern):
    test_cases = unittest.TestSuite()
    tl = WookieeTestLoader()
    TestClass = type('TestHostProxy_space', (TestHostProxy,),
                     {'tested_char_name': 'space',
                      'tested_char': Tools.SP})
    test_cases.addTests(tl.loadTestsFromTestCase(TestClass))
    TestClass = type('TestNonDefaultHostProxy_space',
                     (TestNonDefaultHostProxy,),
                     {'tested_char_name': 'space',
                      'tested_char': Tools.SP})
    test_cases.addTests(tl.loadTestsFromTestCase(TestClass))
    for charname, char in Tools.CONTROL_CHARS.items():
        TestClass = type('TestHostProxy_{0}'.format(charname),
                         (TestHostProxy,), {'tested_char_name': charname,
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
