#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
from httpwookiee.config import ConfigFactory
from httpwookiee.core.tools import outmsg, inmsg
from httpwookiee.http.worker import Worker
from httpwookiee.core.order import Order
from httpwookiee.core.info import Info
import sys
import socket
import select
import threading

try:
    import queue as Queue
except ImportError:
    import Queue


class HttpServerThread(threading.Thread):

    http_server = None
    abort = None
    in_queue = None
    out_queue = None
    err_queue = None
    config = None
    port = None
    hostip = b''
    request = None
    _listen_sock = None
    workers = []

    def __init__(self, group=None, target=None, name=None, *args, **kwargs):
        super(HttpServerThread, self).__init__(group,
                                               target,
                                               name,
                                               args,
                                               kwargs)

        self.config = ConfigFactory.getConfig()
        self.abort = threading.Event()
        # kwargs None will fail because of missing communications queues
        # so we do not have to handle defaults out of this if for other
        # variables
        if kwargs is not None:
            if 'in_queue' in kwargs:
                self.in_queue = kwargs['in_queue']
            if 'out_queue' in kwargs:
                self.out_queue = kwargs['out_queue']
            if 'err_queue' in kwargs:
                self.err_queue = kwargs['err_queue']

            if 'port' in kwargs:
                self.port = kwargs['port']
            else:
                self.port = self.config.getint('BACKEND_PORT')

            if 'hostip' in kwargs:
                self.hostip = kwargs['hostip']
            else:
                self.hostip = '0.0.0.0'

            if 'queue' in kwargs:
                self.queue = kwargs['queue']
            else:
                self.queue = 5

        if (self.in_queue is None or
                self.out_queue is None or
                self.err_queue is None):
            raise Exception('no In/Out/Err comm. queues for ServerTHread.')

        self.workers = [Worker('WRK1', out_queue=self.out_queue),
                        Worker('WRK2', out_queue=self.out_queue),
                        Worker('WRK3', out_queue=self.out_queue)]
        self.listen_sock = None

    def inmsg(self, message):
        inmsg(message, prefix=b'BACKEND> ', color='blue')

    def outmsg(self, message):
        outmsg(message, prefix=b'BACKEND> ', color='yellow')

    def run(self):
        try:
            self._prepare_server_socket()
            while not self.abort.is_set():

                # 1) manage TCP/IP communications
                sockets = [self.listen_sock]
                wsockets = []
                for worker in self.workers:
                    if not worker.ready:
                        # still handling an HTTp communication, so may need
                        # to perform some IO on sockets
                        sockets.append(worker._sock)
                        wsockets.append(worker._sock)

                # list args of select are list of socket to monitor for:
                # - readability
                # - writeablity
                # - error_states
                # 1 is the timeout of this socket monitoring operation
                readables, writables, errored = select.select(sockets,
                                                              wsockets,
                                                              sockets,
                                                              1)

                # push write before checking for reads (for better closing
                # sockets managment)
                self._handle_writables(writables)
                self._handle_readables(readables)
                self._handle_errored(errored)

                # 2) now check the content of the internal messages queues
                try:
                    # blocks for 0.05 and throw Queue.Empty
                    order = self.in_queue.get(True, 0.05)
                    self.manageOrder(order)
                except Queue.Empty:
                    continue
            self.outmsg('End of server run operations, bye.')
        except BaseException:
            self.err_queue.put(sys.exc_info())
        self.close()

    def manageOrder(self, order):
        "Manage Order and Info objects for the thread message's queues"
        self.inmsg('order received {0}'.format(order))

        if Order.ACTION_PING == order.getAction():
            self.out_queue.put(Info(Info.INFO_PONG,
                                    order.getId(),
                                    order.getData()))

        elif Order.ACTION_STOP == order.getAction():
            self.out_queue.put(Info(Info.INFO_OK,
                                    order.getId()))
            self.abort.set()

        elif Order.ACTION_CLEANUP == order.getAction():
            for worker in self.workers:
                worker.close()
            self.out_queue.put(Info(Info.INFO_OK,
                                    order.getId()))

        elif Order.ACTION_BEHAVIOR == order.getAction():
            # specific behavior requested for a test
            test_id = order.getId()
            behavior = order.getData()
            self.out_queue.put(Info(Info.INFO_OK, test_id))
            # Register the test and the matching behavior on all workers.
            # If they detect the test they will know how to react
            for worker in self.workers:
                worker.setTestId(test_id)
                worker.setTestBehavior(behavior)

        else:
            self.out_queue.put(Info(Info.INFO_REJECT,
                                    order.getId()))

    def _handle_readables(self, readables):
        'Manage incoming sockets having some content.'
        for s in readables:
            if s is self.listen_sock:
                # incoming connection from the listening server sock
                client_connection, client_address = self.listen_sock.accept()
                handled = False
                for worker in self.workers:
                    if worker.ready:
                        self.inmsg('# New Connection from ' +
                                   '{0} assigned to {1}'.format(
                                       client_address,
                                       worker.name))
                        worker.init(client_connection, client_address)
                        handled = True
                        break
                if not handled:
                    self.inmsg(
                        "# Too many connections," +
                        " conn from {0} rejected".format(client_address))
                    client_connection.close()
            else:
                # worker socket has some content, delegate task to worker
                for worker in self.workers:
                    if s is worker._sock:
                        worker.read_socket()
                        break

    def _handle_writables(self, writables):
        """Manage opened sockets (from current workers).

        Delegate potential writes to workers, if they have a response ready
        they will send it throught that opened socket and maybe close the
        socket if the whole response is managed."""
        for s in writables:
            for worker in self.workers:
                if s is worker._sock:
                    worker.write_socket()
                    break

    def _handle_errored(self, errored):
        'manage tcp/ip socket in error states'
        for s in errored:
            if s is self.listen_sock:
                self.inmsg('# socket error in server master socket.')
                self.close()
            else:
                self.inmsg('# Error in client socket detected')
                for worker in self.workers:
                    if s is worker._sock:
                        self.inmsg('# worker found for errored socket')
                        worker.close_socket()
                        break

    def _prepare_server_socket(self):
        try:
            self.inmsg(
                '# Connecting Listening socket to IP: {0} PORT: {1}'.format(
                    self.hostip, self.port))
            self.listen_sock = socket.socket(socket.AF_INET,
                                             socket.SOCK_STREAM)
            self.listen_sock.setsockopt(socket.SOL_SOCKET,
                                        socket.SO_REUSEADDR,
                                        1)
            self.listen_sock.bind((self.hostip, self.port))
            self.listen_sock.listen(self.queue)
            self.inmsg('# Start Listening with queue size {0}'.format(
                       self.queue))
        except socket.error as msg:
            self.inmsg("[ERROR] {0}".format(msg))
            raise Exception('error creating listening socket')

    def close(self):
        'close all opened sockets (in and out).'
        print('set abort event')
        self.abort.set()
        if self.listen_sock is not None:
            try:
                self.listen_sock.shutdown(socket.SHUT_RDWR)
                self.listen_sock.close()
            except Exception:
                pass
            self.listen_sock = None
        for worker in self.workers:
            worker.close()

    def join(self, timeout=None):
        'thread termination, send internal close() call.'
        self.close()
        super(HttpServerThread, self).join(timeout)
