#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
from httpwookiee.http.parser.firstheader import FirstRequestHeader
from httpwookiee.http.parser.message import Message


class Request(Message):

    ERROR_BAD_FIRST_LINE = 'Bad First line in Request'

    def __init__(self):
        super(Request, self).__init__()
        self.name = u'Request'
        self.short_name = u'Req.'
        self.http09 = False

    def _parse_first_line(self, first_line):
        header = FirstRequestHeader().parse(first_line)
        self.first_line = header
        self.version_major = header.version_major
        self.version_minor = header.version_minor
        self.method = header.method
        self.location = header.location
        self.has_args = header.has_args
        self.query_string = header.query_string

        if (not header.valid) or header.error:
            self.setError(self.ERROR_BAD_FIRST_LINE,
                          critical=not(header.valid))
        if self.version_major == 0 and self.version_minor == 9:
            self.http09 = True
            return self.STATUS_BODY
        else:
            return self.STATUS_HEADERS

    def detect_empty_body_conditions(self, parent_request_method):
        "https://tools.ietf.org/html/rfc7230#section-3.3 Message Body"
        # In requests, no conditions are enforcing an empty body,
        # only in responses
        self.empty_body_expected = False

    def get_expected_body_size(self):
        "Return expected body size. Requests and responses are different"
        # WARNING: @see request and response implementations
        if not self.has_cl:
            # without Content-Length information:
            # We are not in a chunked message (method not called)
            # https://tools.ietf.org/html/rfc7230#section-3.3.3 [6]
            # For requests we could consider it a 0 sized messages
            return 0
        else:
            return self.body_size
