#!/usr/bin/env python
# -*- coding: utf-8 -*-
import unittest
import importlib
import sys
from httpwookiee.core.base import BaseTest
from unittest.loader import _make_failed_load_tests


class WookieeTestLoader(unittest.TestLoader):

    def __init__(self, filters={}, debug=False):
        self.debug = debug
        self.filters = filters
        super(WookieeTestLoader, self).__init__()

    def loadTestsFromClass(self, tclass, use_load_tests=True):

        importlib.import_module(tclass)
        module = sys.modules[tclass]
        return self.loadTestsFromModule(module, use_load_tests)

    def loadTestsFromModule(self, module, use_load_tests=True):
        """Return a suite of all tests cases contained in the given module"""
        tests = []
        for name in dir(module):
            obj = getattr(module, name)
            if isinstance(obj, type) and issubclass(obj, BaseTest):
                tests.append(self.loadTestsFromTestCase(obj))

        load_tests = getattr(module, 'load_tests', None)
        tests = self.suiteClass(tests)
        if use_load_tests and load_tests is not None:
            try:
                tests = load_tests(self, tests, None)
            except Exception as e:
                tests = _make_failed_load_tests(module.__name__, e,
                                                self.suiteClass)
        return self.filter_and_sort_tests(tests)

    def filter_and_sort_tests(self, tests, listmode=False):

        testlist = {}
        for test in tests:
            if isinstance(test, unittest.TestSuite):
                testlist.update(self.filter_and_sort_tests(
                    test, listmode=True))
            else:
                test_class_name = test.__class__.__name__
                test_name = test._testMethodName
                if 'Test' == test_class_name[:4]:
                    matched = True
                    if self.filters:
                        if self.filters['nums']:
                            matched = False
                            for num in self.filters['nums']:
                                res = test_name.lower().find(
                                    'test_{0}_'.format(num))
                                if not (res == -1):
                                    if self.debug:
                                        print(' + test filtered by num (ok) '
                                              '[{0}]: {1}'.format(
                                                  num, test_name))
                                    matched = True
                                    break
                        if self.filters['exclude']:
                            for excluding in self.filters['exclude']:
                                res = test_class_name.lower().find(excluding)
                                if not (res == -1):
                                    matched = False
                                    if self.debug:
                                        print(' - test excluded '
                                              '[{0}]: {1}'.format(
                                                  excluding, test_class_name))
                                    break
                        if matched and self.filters['match']:
                            for matching in self.filters['match']:
                                res = test_class_name.lower().find(matching)
                                if res == -1:
                                    matched = False
                                    if self.debug:
                                        print(' - test do not match [{0}]:'
                                              ' {1}'.format(matching,
                                                            test_class_name))
                                    break
                    if matched:
                        if self.debug:
                            print('   \->{0} ({1})'.format(test_class_name,
                                                           test_name))
                        testlist[str(test)] = test
        if listmode:
            return testlist
        else:
            testcases = unittest.TestSuite()
            for testId in sorted(testlist):
                testcases.addTest(testlist[testId])
            if self.debug:
                print('    => {0} test loaded from this module'.format(
                    len(testlist)))
            return testcases
