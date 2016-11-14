#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
from httpwookiee.http.parser.messages import Messages
from httpwookiee.http.parser.message import Message
from httpwookiee.http.parser.request import Request
from httpwookiee.http.parser.exceptions import (EndOfBufferError,
                                                OptionalCRLFSeparator)


class Requests(Messages):

    def __init__(self, rfc=False):
        super(Requests, self).__init__()
        self.rfc = rfc
        self.conn_close = False
        self.name = u'Requests'

    def _getMessage(self):
        return Request()

    def __getattr__(self, item):
        # redirect direct access to requests
        if item is 'requests':
            return self.messages
        else:
            raise AttributeError('unknown {0} attribute'.format(item))

    def _abort_parsing(self):
        self.byteidx = len(self.bytesbuff)
        if self.rfc:
            # memorize we should lose the socket very soon
            self.conn_close = True

    def parse_start_of_stream(self, msg):
            firstline = self.parse_line_from_buffer()
            status = msg.parse_first_line(firstline)
            if Request.STATUS_OPTIONAL_SEPARATOR == status:
                # Ok, it was not really the first line, this is allowed 1 time
                # but 1 time only
                try:
                    firstline = self.parse_line_from_buffer()
                    status = msg.parse_first_line(firstline)
                except EndOfBufferError:
                    # well, it was an extra CRLF at the end
                    raise OptionalCRLFSeparator()
                while Request.STATUS_OPTIONAL_SEPARATOR == status:
                    # oups, we've got too much CRLF between requests
                    self.setError(self.ERROR_BAD_MESSAGES_SEPARATOR)
                    if self.rfc:
                        self._abort_parsing()
                        return False
                    try:
                        firstline = self.parse_line_from_buffer()
                        status = msg.parse_first_line(firstline)
                    except EndOfBufferError:
                        # we've reach EOS on a CRLF or LF serie
                        return False

            if msg.version_major == 0 and msg.version_minor == 9 and self.rfc:
                # In rfc mode we just stop the parsing here
                # and go to the response mode+close directly
                self._abort_parsing()
                status = Message.STATUS_COMPLETED
                # note that this parser will try to extract 'regular' http
                # query even if http/0.9 is detected if not set in rfc mode

            return status
