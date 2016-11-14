#!/usr/bin/env python
# -*- coding: utf-8 -*-
from httpwookiee.config import Register
from httpwookiee.core.tools import Tools, get_rand, inmsg
from httpwookiee.core.order import Order
from httpwookiee.core.info import Info
from httpwookiee.core.behavior import Behavior
from httpwookiee.core.base import BaseTest
from httpwookiee.core.exceptions import (NoServerThreadResponse,
                                         BadServerThreadResponse)
import six
try:
    import queue as Queue
except ImportError:
    import Queue


class ProxyTest(BaseTest):

    backend = None
    backend_status = None
    test_id = None
    server_in = None
    server_out = None
    reverse_proxy_mode = True

    def __init__(self, methodName="runTest"):
        super(ProxyTest, self).__init__(methodName)
        self.test_id = get_rand()
        self.reverse_proxy_mode = True
        # comm queues are not yet created
        self.server_in = False
        self.server_out = False
        self.use_backend_location = True

    def setUp(self):
        super(ProxyTest, self).setUp()
        self._cleanup_server_workers()
        if self.send_mode == self.SEND_MODE_UNIQUE:
            self.req.add_argument('httpw', '--{0}--'.format(self.test_id))
            # self.req.add_header('Cookie', 'Foo=Bar')
        elif self.send_mode == self.SEND_MODE_PIPE:
            self.req1.add_argument('httpw', '--{0}--'.format(self.test_id))
            self.req2.add_argument('httpw', '--{0}--'.format(self.test_id))
            # self.req1.add_header('Cookie', 'Foo=Bar')
            # self.req2.add_header('Cookie', 'Foo=Bar')
        self._prepare_server_worker_behavior()

    def _wait_for_server_thread_response(self):
        "We've send an order to the server thread, wait for response."
        try:
            handled = False
            while not handled:
                info = self.server_out.get(True, 5)
                if info.id == self.test_id:
                    handled = True
                    if info.status == Info.INFO_REJECT:
                        raise BadServerThreadResponse('Rejected order')
                    return info.status
        except Queue.Empty:
            raise NoServerThreadResponse()

    def _ensure_comm_queues(self):
        "Ensure self.server_in and our are ready for server communication."
        if self.server_in is False:
            self.server_in = Register.get('server_in_queue', False)
            if self.server_in is False:
                raise Exception('Missing 1st server thread comm queue.')
        if self.server_out is False:
            self.server_out = Register.get('server_out_queue', False)
            if self.server_out is False:
                raise Exception('Missing 2nd server thread comm queue.')

    def _cleanup_server_workers(self):
        "Ask server thread for ready workers."
        self._ensure_comm_queues()
        self.server_in.put_nowait(Order(Order.ACTION_CLEANUP, self.test_id))
        if Info.INFO_OK != self._wait_for_server_thread_response():
            raise Exception('Cannot set server cleanup.')

    def _prepare_server_worker_behavior(self):
        "Transmit some expected behaviors to the server thread workers."
        self._ensure_comm_queues()
        self.server_in.put_nowait(Order(Order.ACTION_BEHAVIOR,
                                  self.test_id,
                                  self.getBehavior()))
        if Info.INFO_OK != self._wait_for_server_thread_response():
            raise Exception('Cannot set server behavior.')

    def _prepare_proxy_test(self):
        pass

    def getBehavior(self):
        "What is the server expected behavior?"
        behavior = Behavior()
        behavior.accept_invalid_request = True
        behavior.add_wookie_response = False
        behavior.wookie_stream_position = 2
        behavior.keep_alive_on_error = True
        return behavior


class AbstractEchoProxy(ProxyTest):

    def getBehavior(self):
        "What is the server expected behavior?"
        behavior = Behavior()
        behavior.accept_invalid_request = True
        behavior.add_wookie_response = False
        behavior.wookie_stream_position = 2
        behavior.keep_alive_on_error = True
        behavior.echo_query = True
        return behavior

    def __init__(self, methodName="runTest"):
        super(AbstractEchoProxy, self).__init__(methodName)
        self.backend_queries = None
        # status of echo read
        self.partial_echo = False

    def setUp(self):
        super(AbstractEchoProxy, self).setUp()
        self.backend_queries = None

    def get_echoed_query(self):
        try:
            while True:
                # we use a short timeout, we already have the server
                # response, so the echo should already be in the queue
                # info = self.server_out.get(True, 0.1)
                # or maybe not
                info = self.server_out.get(True, 1)
                if info.id == self.test_id:
                    if info.status == Info.INFO_DATA:
                        self.partial_echo = False
                        return info.data
                    if info.status == Info.INFO_PARTIAL_DATA:
                        self.partial_echo = True
                        return info.data
        except Queue.Empty:
            raise NoServerThreadResponse('Timeout waiting for echoed query.')

    def _hook_while_sending(self):
        "Hook running while request are sent to the tested server."
        transmit = True
        try:
            self.backend_queries = self.get_echoed_query()
        except NoServerThreadResponse:
            # well our bad query was maybe not transmitted
            inmsg('# No transmission from backend.')
            transmit = False
        if transmit:
            inmsg('# received query from backend echo.')
            inmsg(str(self.backend_queries))

            self._analyze_echo_queries()

    def _analyze_echo_queries(self):
        if self.partial_echo:
            self._analyze_invalid_echo_queries(stream_mode=True)
        else:
            if (not self.backend_queries.valid) or self.backend_queries.error:
                self._analyze_invalid_echo_queries()
            else:
                self._analyze_valid_echo_queries()

    def _analyze_invalid_echo_queries(self, stream_mode=False):
        "Having a backend received query which is invalid"
        if self.transmission_zone is not None:
            if stream_mode:
                zone = self.backend_queries
            else:
                if self.transmission_zone is Tools.ZONE_FIRST_LINE:
                    query = self.backend_queries[0]
                    zone = query.first_line.raw
                    inmsg('# zone to analyze:.')
                    inmsg(str(zone))
                if self.transmission_zone is Tools.ZONE_HEADERS:
                    query = self.backend_queries[0]
                    zone = b''
                    for header in query.headers:
                        zone += header.raw
                    inmsg('# zone to analyze:.')
                    inmsg(str(zone))
                if self.transmission_zone is Tools.ZONE_CHUNK_SIZE:
                    query = self.backend_queries[0]
                    zone = b''
                    if query.chunked:
                        for chunk in query.chunks:
                            zone += chunk.raw
                    inmsg('# zone to analyze:.')
                    inmsg(str(zone))

        if self.transmission_map:
            for proof, status in Tools.iteritems(self.transmission_map):
                # here we manipulate bytes strings
                if isinstance(proof, six.string_types):
                    # we do not use special non-ascii chars internally
                    proof = proof.encode('ascii')
                if proof in zone:
                    inmsg('# found one transmission proof,'
                          ' status to : {0}'.format(status))
                    inmsg(repr(proof))
                    self.setStatus(status)
                    return True

        self.setStatus(self.STATUS_TRANSMITTED)

    def _analyze_valid_echo_queries(self):
        "Having a backend received query which is not invalid, want to check?"
        pass
