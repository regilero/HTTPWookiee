#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
from httpwookiee.http.parser.firstheader import FirstResponseHeader
from httpwookiee.http.parser.message import Message


class Response(Message):

    ERROR_BAD_FIRST_LINE = 'Bad First line in Response'
    ERROR_HTTP09_RESPONSE = 'This is an HTTP/0.9 Response'

    def __init__(self):
        super(Response, self).__init__()
        self.name = u'Response'
        self.short_name = u'Resp.'

    def _parse_first_line(self, first_line):
        'Response implementation of HTTP message 1st line'
        header = FirstResponseHeader().parse(first_line)
        self.first_line = header
        self.code = header.code
        self.version_major = header.version_major
        self.version_minor = header.version_minor
        self.response_title = header.value
        if (not header.valid) or header.error:
            self.setError(self.ERROR_BAD_FIRST_LINE,
                          critical=not(header.valid))
        if FirstResponseHeader.ERROR_MAYBE_09 in header.errors:
            self.setError(self.ERROR_HTTP09_RESPONSE)
        if self.version_major == 0 and self.version_minor == 9:
            return self.STATUS_BODY
        else:
            return self.STATUS_HEADERS

    def parse_body(self, data):
        if self.version_major == 0 and self.version_minor == 9:
            # In 0.9 mode the first line raw content is part of the body, as
            # everything is just a body
            self.body = self.first_line.raw
            self.body += data
        else:
            self.body = data
        return self.STATUS_COMPLETED

    def get_expected_body_size(self):
        "Return expected body size. Requests and responses are different"
        if not self.has_cl:
            # FIXME:
            # without Content-Length information:
            # unless request method is HEAD, response status is 1xx 204 or 304
            # Unless a 2xx responses after a CONNECT
            # unless chunked is the last Transfer-Encoding
            # For responses the body size is the whole message.
            return self.READ_UNTIL_THE_END
        else:
            return self.body_size
