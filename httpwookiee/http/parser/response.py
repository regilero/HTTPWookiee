#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
from httpwookiee.http.parser.firstheader import FirstResponseHeader
from httpwookiee.http.parser.message import Message


class Response(Message):

    ERROR_BAD_FIRST_LINE = 'Bad First line in Response'
    ERROR_HTTP09_RESPONSE = 'This is an HTTP/0.9 Response'
    ERROR_UNEXPECTED_CONTENT_LENGTH_HEADER = ('This sort of response must not'
                                              ' contain a Content-length'
                                              ' Header')

    def __init__(self):
        super(Response, self).__init__()
        self.name = u'Response'
        self.short_name = u'Resp.'
        self.interim_responses = []

    def render_iterim_parts(self):
        "For responses, representation of interim responses"
        out = ""
        if (len(self.interim_responses) > 0):
            out += " ** Interim responses detected **\n"
            for interim in self.interim_responses:
                out += "\nINTERIM RESPONSE:\n{0}\n".format(interim)
        return out

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

    def detect_empty_body_conditions(self, parent_request_method):
        "https://tools.ietf.org/html/rfc7230#section-3.3 Message Body"
        if ((self.code in (204, 304, 100, 101)) or
                (parent_request_method == 'HEAD') or
                (parent_request_method == 'CONNECT' and self.code == 200)):
            self.body_size = 0
            self.empty_body_expected = True
            # https://tools.ietf.org/html/rfc7230#section-3.3.2
            if self.has_cl and self.code in (204, 100, 101):
                # response is bad, it should not contain a Content-Length
                # header
                self.setError(self.ERROR_UNEXPECTED_CONTENT_LENGTH_HEADER,
                              critical=False)

    def get_expected_body_size(self):
        "Return expected body size. Requests and responses are different"
        if self.empty_body_expected:
            return 0

        # Note that chunked messages are not coming in this section
        if not self.has_cl:
            return self.READ_UNTIL_THE_END
        else:
            return self.body_size

    def had_interim_responses(self):
        return (len(self.interim_responses) > 0)

    def is_interim_response(self):
        return ((self.body == b'') and
                (self.body_size == 0) and
                (self.code == 100) and
                (self.first_line.value == u'Continue')
                # (self.headers == []) and
                )
