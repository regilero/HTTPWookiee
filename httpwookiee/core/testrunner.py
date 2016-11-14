#!/usr/bin/env python
# -*- coding: utf-8 -*-
from httpwookiee.config import ConfigFactory, Register
from httpwookiee.http.server import HttpServerThread
from httpwookiee.core.order import Order
import unittest
try:
    import queue as Queue
except ImportError:
    import Queue
# import time


class WookieeTestRunner(unittest.TextTestRunner):

    server_thread = None

    def __init__(self,
                 stream=None,
                 descriptions=True,
                 verbosity=1,
                 failfast=False,
                 buffer=False,
                 resultclass=None,
                 warnings=None):
        self.config = ConfigFactory.getConfig()
        # warnings argument not working in p2.7
        super(WookieeTestRunner, self).__init__(stream,
                                                descriptions,
                                                verbosity,
                                                failfast,
                                                buffer,
                                                resultclass)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def __del__(self):
        self.close()

    def close(self):
        if self.server_thread and self.server_thread.isAlive():
            print("testRunner Waiting for server thread to join...")
            self.server_thread.join()

    def run(self, test):
        in_queue = Queue.Queue()
        out_queue = Queue.Queue()
        err_queue = Queue.Queue()
        if self.server_thread is None:
            print('testRunner creating server thread')
            self.server_thread = HttpServerThread(name='httpserver',
                                                  in_queue=in_queue,
                                                  out_queue=out_queue,
                                                  err_queue=err_queue)
            self.server_thread.setDaemon(False)
        if not self.server_thread.is_alive():
            print('starting server thread')
            self.server_thread.start()
            Register.set('server_in_queue', in_queue)
            Register.set('server_out_queue', out_queue)
            Register.set('server_err_queue', err_queue)
        # time.sleep(30)
        print('starting tests')
        result = super(WookieeTestRunner, self).run(test)
        print('Now asking server thread to die')
        try:
            in_queue.put_nowait(Order(Order.ACTION_STOP))
        except Queue.Full:
            pass
        self.server_thread.join()
        return result
