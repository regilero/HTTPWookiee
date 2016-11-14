#!/usr/bin/env python
# -*- coding: utf-8 -*-
import unittest
from httpwookiee.config import Register
from httpwookiee.core.base import BaseTest
try:
    import queue as Queue
except ImportError:
    import Queue
# import sys


class TextStatusResult(unittest.TestResult):
    """Test result specific implementation with support for more test status

    Based on TextTestResult. We add a specific status which is not only
    ok or fail. As this status will help us detect the server behavior and
    the gravity of the failures.
    We can catch backend server thread errors (when tests are running with a
    server backend).
    We also add a gravity status on tests results.
    Managed Tests should be BaseTest instances."""

    separator1 = '=' * 70
    separator2 = '-' * 70
    server_err_queue = None

    def __init__(self, stream=None, descriptions=None, verbosity=None):

        self.stream = stream
        self.showAll = verbosity > 1
        self.dots = verbosity == 1
        self.descriptions = descriptions
        self.unknown = []
        self.minor = []
        self.warning = []
        self.critical = []

        super(TextStatusResult, self).__init__(
            stream, descriptions, verbosity)

    def startTestRun(self):
        """Called once before any tests are executed.

        See startTest for a method called before each test.
        """
        # when running in server mode we may have a server thread running.
        # Here we catch the err channel of this server to check for excptions
        # from the server
        self.server_err_queue = Register.get('server_err_queue')

    def stopTestRun(self):
        """Called once after all tests are executed.

        See stopTest for a method called after each test.
        """
        if self.server_err_queue is not None:
            self._check_for_server_exceptions()

    def stopTest(self, test):
        "Called when the given test has been run."
        super(TextStatusResult, self).stopTest(test)
        if self.server_err_queue is not None:
            self._check_for_server_exceptions()

    def _check_for_server_exceptions(self):
        """Check that the server thread has not been killed by an exception.

        As we may have a big tendency of sending some bad stuff there...
        """
        try:
            server_exception = self.server_err_queue.get(block=False)
        except Queue.Empty:
            pass
        else:
            exc_ttype, exc_obj, exc_trace = server_exception
            if self.showAll:
                self.stream.write("-Server Thread Exception- ")
                self.stream.writeln("oO*-[INTERNAL ERROR]-*Oo")
            elif self.dots:
                self.stream.writeln('oO*-[INTERNAL ERROR]-*Oo')
                self.stream.flush()
            raise exc_obj

    def startTest(self, test):
        """Copied from TextTestResult,

        Called when the given test is about to be run.
        """
        super(TextStatusResult, self).startTest(test)
        # Debug line
        # self._mirrorOutput = True
        if self.showAll:
            self.stream.write(self.getDescription(test))
            self.stream.write("... ")
            self.stream.flush()

    def _cap80(self, strg):
        if strg:
            strgs = strg.split('\n')
            final = []
            loop = True
            first = True
            line = strgs.pop(0)

            while loop:
                if first:
                    first = False
                    final.append(line)
                    if len(strgs) == 0:
                        strgs.insert(0, '')
                else:
                    if len(line) > 78:
                        ok = line[0:78]
                        final.append(ok)
                        rest = line[78:]
                        strgs.insert(0, rest)
                    else:
                        final.append(line)
                try:
                    line = strgs.pop(0)
                except IndexError:
                    loop = False

            last = final.pop()
            last = "{0:.<78} ".format(last)
            final.append(last)
            return '\n  '.join(final)
        return strg

    def getDescription(self, test):
        doc_first_line = test.shortDescription()
        if self.descriptions and doc_first_line:
            return self._cap80('\n'.join((str(test), doc_first_line)))
        else:
            return self._cap80(str(test))

    def addSuccess(self, test):
        super(TextStatusResult, self).addSuccess(test)
        if self.showAll:
            self.stream.write("-{0}- ".format(test.getStatus('long')))
            self.stream.writeln("   [ok]")
        elif self.dots:
            self.stream.write(test.getStatus('short'))
            # self.stream.write('.')
            self.stream.flush()

    def addError(self, test, err):
        super(TextStatusResult, self).addError(test, err)
        if self.showAll:
            if hasattr(self, 'getStatus'):
                self.stream.write("-{0}- ".format(test.getStatus('long')))
            self.stream.writeln("[ERROR]")
        elif self.dots:
            if hasattr(self, 'getStatus'):
                self.stream.write(test.getStatus('short'))
            self.stream.write('E')
            self.stream.flush()
        self._mirrorOutput = False

    def addFailure(self, test, err):
        super(TextStatusResult, self).addFailure(test, err)
        if self.showAll:
            self.stream.write("-{0}-[{1}]- ".format(test.getStatus('long'),
                                                    test.getGravity(True)))
            self.stream.writeln(" [FAIL]")
        elif self.dots:
            self.stream.write(test.getStatus('short'))
            self.stream.write('F')
            self.stream.flush()
        self._mirrorOutput = False
        gravity = test.getGravity()
        if BaseTest.GRAVITY_CRITICAL == gravity:
            self.critical.append((test, self._exc_info_to_string(err, test)))
        elif BaseTest.GRAVITY_WARNING == gravity:
            self.warning.append((test, self._exc_info_to_string(err, test)))
        elif BaseTest.GRAVITY_MINOR == gravity:
            self.minor.append((test, self._exc_info_to_string(err, test)))
        else:
            self.unknown.append((test, self._exc_info_to_string(err, test)))

    def addSkip(self, test, reason):
        super(TextStatusResult, self).addSkip(test, reason)
        if self.showAll:
            self.stream.writeln("skipped {0!r}".format(reason))
        elif self.dots:
            self.stream.write("s")
            self.stream.flush()

    def addExpectedFailure(self, test, err):
        "TODO: not really managed yet"
        super(TextStatusResult, self).addExpectedFailure(test, err)
        if self.showAll:
            self.stream.writeln("expected failure")
        elif self.dots:
            self.stream.write("x")
            self.stream.flush()

    def addUnexpectedSuccess(self, test):
        "TODO: not really managed yet"
        super(TextStatusResult, self).addUnexpectedSuccess(test)
        if self.showAll:
            self.stream.writeln("unexpected success")
        elif self.dots:
            self.stream.write("u")
            self.stream.flush()

    def printErrors(self):
        if self.dots or self.showAll:
            self.stream.writeln()
        self.printErrorList('FAIL',
                            self.unknown,
                            BaseTest.gravity_format[BaseTest.GRAVITY_UNKNOWN])
        self.printErrorList('FAIL',
                            self.minor,
                            BaseTest.gravity_format[BaseTest.GRAVITY_MINOR])
        self.printErrorList('FAIL',
                            self.warning,
                            BaseTest.gravity_format[BaseTest.GRAVITY_WARNING])
        self.printErrorList('FAIL',
                            self.critical,
                            BaseTest.gravity_format[BaseTest.GRAVITY_CRITICAL])
        self.printErrorList('ERROR', self.errors)

    def printErrorList(self, flavour, errors, gravity=None):
        for test, err in errors:
            self.stream.writeln(self.separator1)
            if gravity is None:
                self.stream.writeln("{0}:".format(flavour))
            else:
                self.stream.writeln("{0} gravity: {1}".format(flavour,
                                                              gravity))
            if hasattr(self, 'getStatus'):
                self.stream.writeln(" {0} -{1}-".format(
                    self.getDescription(test),
                    test.getStatus('long')))
            else:
                self.stream.writeln(" {0}".format(
                    self.getDescription(test)))
            self.stream.writeln(self.separator2)
            self.stream.writeln("%s" % err)
