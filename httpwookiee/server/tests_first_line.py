#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
from httpwookiee.core.result import TextStatusResult
from httpwookiee.core.proxy import AbstractEchoProxy
from httpwookiee.core.tools import Tools
from httpwookiee.client.tests_first_line import (
    AbstractFirstLineSeparators,
    AbstractCarriageReturnFirstLineSpaceSeparators,
    AbstractTestHTTPVersion)
from httpwookiee.core.testrunner import WookieeTestRunner
from httpwookiee.core.testloader import WookieeTestLoader

import sys


class AbstractFirstLineProxy(AbstractEchoProxy,
                             AbstractFirstLineSeparators):
    pass


class TestNullFirstLineProxy(AbstractFirstLineProxy):
    "Test NULL separator at various places on first line of request."

    def setLocalSettings(self):
        self.separator = Tools.NULL
        self.valid_prefix = False
        self.valid_suffix = False
        self.valid_method_prefix = False
        self.valid_method_suffix = False
        self.valid_location = False
        self.valid_09_location = False
        self.can_be_rejected = True


class TestFormFeedFirstLineProxy(AbstractFirstLineProxy):
    "Test FF separator at various places on first line of request."

    def setLocalSettings(self):
        self.separator = Tools.FF
        self.valid_prefix = False
        self.valid_suffix = False
        self.valid_method_prefix = False
        self.valid_method_suffix = True
        self.valid_location = False
        self.valid_09_location = False
        self.can_be_rejected = True


class TestBackSpaceFirstLineProxy(AbstractFirstLineProxy):
    "Test BACKSPACE separator at various places on first line of request."

    def setLocalSettings(self):
        self.separator = Tools.BS
        self.valid_prefix = False
        self.valid_suffix = False
        self.valid_method_prefix = False
        self.valid_method_suffix = False
        self.valid_location = False
        self.valid_09_location = True
        self.can_be_rejected = True


class TestBellFirstLineProxy(AbstractFirstLineProxy):
    "Test BELL separator at various places on first line of request."

    def setLocalSettings(self):
        self.separator = Tools.BEL
        self.valid_prefix = False
        self.valid_suffix = False
        self.valid_method_prefix = False
        self.valid_method_suffix = False
        self.valid_location = False
        self.valid_09_location = True
        self.can_be_rejected = True


class TestHTabFirstLineProxy(AbstractFirstLineProxy):
    "Test VTAB separator at various places on first line of request."

    def setLocalSettings(self):
        self.separator = Tools.TAB
        self.valid_prefix = False
        self.valid_suffix = False
        self.valid_method_prefix = False
        self.valid_method_suffix = True
        self.valid_location = False
        self.valid_09_location = False
        self.can_be_rejected = True


class TestVerticalTabFirstLineProxy(AbstractFirstLineProxy):
    "Test VTAB separator at various places on first line of request."

    def setLocalSettings(self):
        self.separator = Tools.VTAB
        self.valid_prefix = False
        self.valid_suffix = False
        self.valid_method_prefix = False
        self.valid_method_suffix = True
        self.valid_location = False
        self.valid_09_location = False
        self.can_be_rejected = True


class AbstractCarriageReturnFirstLineProxy(
        AbstractEchoProxy,
        AbstractCarriageReturnFirstLineSpaceSeparators):
    pass


class TestCarriageReturnFirstLineProxy(AbstractCarriageReturnFirstLineProxy):
    "Test CR separator at various places on first line of request."

    def setLocalSettings(self):
        self.separator = Tools.CR
        self.valid_prefix = True
        self.valid_suffix = False
        self.valid_method_prefix = False
        self.valid_method_suffix = True
        self.valid_location = False
        self.valid_09_location = False
        self.can_be_rejected = True


class AbstractHTTPVersionProxy(AbstractEchoProxy,
                               AbstractTestHTTPVersion):
    pass


class TestHTTPVersionProxy(AbstractHTTPVersionProxy):
    """Test Bad Digits variations on requested HTTP version."""
    pass


if __name__ == '__main__':
    tl = WookieeTestLoader(debug=True)
    testSuite = tl.loadTestsFromModule(sys.modules[__name__])
    # without stream forced here python 2.7 is failing
    WookieeTestRunner(resultclass=TextStatusResult,
                      verbosity=2,
                      buffer=True,
                      stream=sys.stderr).run(testSuite)
