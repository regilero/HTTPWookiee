#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
from httpwookiee.core.tools import Tools
from httpwookiee.core.result import TextStatusResult
from httpwookiee.core.proxy import AbstractEchoProxy
from httpwookiee.core.testrunner import WookieeTestRunner
from httpwookiee.core.testloader import WookieeTestLoader
from httpwookiee.core.behavior import Behavior
from httpwookiee.client.tests_chunks import (AbstractTestChunks,
                                             AbstractChunksOverflow)
import sys


class Test20ChunksProxy(AbstractEchoProxy,
                        AbstractTestChunks):

    def _analyze_valid_echo_queries(self):
        "Having a backend received query which is not invalid, want to check?"

        # force analysis on test_chunked_size_truncation
        # we want to check that this valid but strange syntax
        # is not used.
        # and yes this is kind of a crappy hack on status
        # because by default this call will set TRANSMITTED
        old_status = self.status
        if self.transmission_zone is Tools.ZONE_CHUNK_SIZE:
            self._analyze_invalid_echo_queries()
            if not (self.status == self.STATUS_TRANSMITTED_CRAP):
                self.status = old_status


class AbstractChunksOverflowProxy(AbstractEchoProxy,
                                  AbstractChunksOverflow):

    def getBehavior(self):
        "What is the server expected behavior? in RP mode"
        behavior = Behavior()
        behavior.accept_invalid_request = True
        behavior.add_wookiee_response = False
        behavior.wookie_stream_position = 2
        behavior.keep_alive_on_error = True
        behavior.echo_query = True
        behavior.echo_incomplete_query = True
        return behavior
#
# class Test25ChunksOverflow256Proxy(AbstractChunksOverflowProxy):
#
#    def setLocalSettings(self):
#        self.nb = 256


class Test25ChunksOverflow65536Proxy(AbstractChunksOverflowProxy):

    def setLocalSettings(self):
        self.nb = 65536


class Test25ChunksOverflow4294967296Proxy(AbstractChunksOverflowProxy):

    def setLocalSettings(self):
        self.nb = 4294967296


class Test25ChunksOverflow18446744073709551616Proxy(
        AbstractChunksOverflowProxy):

    def setLocalSettings(self):
        self.nb = 18446744073709551616


if __name__ == '__main__':
    tl = WookieeTestLoader()
    testSuite = tl.loadTestsFromModule(sys.modules[__name__])
    # without stream forced here python 2.7 is failing
    WookieeTestRunner(resultclass=TextStatusResult,
                      verbosity=2,
                      buffer=True,
                      stream=sys.stderr).run(testSuite)
