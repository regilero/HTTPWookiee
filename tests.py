#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Internal Tests
#
from httpwookiee.core.result import TextStatusResult
from httpwookiee.core.testrunner import WookieeTestRunner
from httpwookiee.config import ConfigFactory
import httpwookiee.client.tests_regular
import httpwookiee.client.tests_expect
# import httpwookiee.client.tests_first_line
# import httpwookiee.client.tests_content_length
# import httpwookiee.client.tests_chunks
# (...)
import tests.messages
import tests.internal_server
import inspect
import unittest
import os
import sys

if __name__ == '__main__':
    # use env HTTPWOOKIEE_CONF to override defaults and force AUTOTEST
    # where client testers will run against our proxy backend, without using
    # any proxy, in fact.
    currdir = os.path.dirname(os.path.realpath(__file__))
    os.environ["HTTPWOOKIEE_CONF"] = os.path.join(currdir,
                                                  "tests",
                                                  "tests.ini")
    config = ConfigFactory.getConfig()
    if config.getboolean('DEBUG'):
        verbosity = 2
    else:
        verbosity = 1
    testcases = []
    # Pre Flight tests, detect features support
    for name, obj in inspect.getmembers(httpwookiee.client.tests_regular):
        if 'Test' == name[:4] and inspect.isclass(obj):
            testcases.append(obj)
    classes = []
    classes.append(tests.messages)
    classes.append(tests.internal_server)
    classes.append(httpwookiee.client.tests_regular)
    classes.append(httpwookiee.client.tests_expect)
    # classes.append(httpwookiee.client.tests_first_line)
    # classes.append(httpwookiee.client.tests_content_length)
    # classes.append(httpwookiee.client.tests_chunks)
    # (...)
    for tclass in classes:
        for name, obj in inspect.getmembers(tclass):
            if 'Test' == name[:4] and inspect.isclass(obj):
                testcases.append(obj)
    tl = unittest.TestLoader()
    suites = [tl.loadTestsFromTestCase(classobj)
              for classobj in testcases]
    testSuite = unittest.TestSuite(suites)
    # without stream forced here python 2.7 is failing
    sys.exit(not WookieeTestRunner(resultclass=TextStatusResult,
                                   verbosity=verbosity,
                                   buffer=True,
                                   stream=sys.stderr
                                   ).run(testSuite).wasSuccessful())
