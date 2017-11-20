#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
from httpwookiee.http.parser.header import Header
from httpwookiee.http.parser.chunk import Chunk
from httpwookiee.core.tools import Tools


class Message(object):

    STATUS_OPTIONAL_SEPARATOR = 0
    STATUS_HEADERS = 1
    STATUS_BODY = 2
    STATUS_CHUNK_HEADER = 3
    STATUS_CHUNK = 4
    STATUS_COMPLETED = 5

    ERROR_BAD_FIRST_LINE = 'Bad First line in Message'
    ERROR_HAS_INVALID_HEADER = 'Has invalid Header'
    ERROR_HAS_INVALID_NUMERIC_HEADER = 'Has invalid Numeric Header'
    ERROR_HAS_INVALID_CHUNK = 'Has invalid Chunk'
    ERROR_BAD_CHUNKED_HEADER = 'Has Bad transfer Encoding chunked header'
    ERROR_HAS_BAD_CHUNK = 'Has bad Chunk'
    ERROR_HAS_INVALID_CHUNK_DATA = 'Has invalid Chunk data'
    ERROR_HAS_EXTRA_CHUNK_DATA = 'Has extra Chunk data'
    ERROR_DOUBLE_CONTENT_LENGTH = 'Has more than one Content-length Header'
    ERROR_CONTENT_LENGTH_AND_CHUNKED = 'Has Content-length and chunks'
    ERROR_FIRST_HEADER_OPS_FOLD = ('Has first header in the optional '
                                   'folding format')

    READ_UNTIL_THE_END = -99

    def __str__(self):
        out = ""
        if self.error:
            if not self.valid:
                out = "****INVALID {0} <".format(self.name)
            else:
                out = "****BAD {0} <".format(self.name)
            for error, value in Tools.iteritems(self.errors):
                out += " {0};".format(error)
            out += ">****\n"
        out += " [{0} 1st line]\n{1}".format(self.short_name, self.first_line)
        out += " [{0} Headers]\n".format(self.short_name)
        for header in self.headers:
            out += "{0}".format(header)
        if self.chunked:
            out += " [{0} Chunks] ({1})\n".format(self.short_name,
                                                  len(self.chunks))
            for chunk in self.chunks:
                out += "{0}".format(chunk)
        bodylen = len(self.body)
        if (bodylen > 1000):
            body = self.body[0:1000] + b'( to be continued...)'
        else:
            body = self.body
        out += " [{0} Body] (size {1})\n{2}".format(self.short_name,
                                                    bodylen,
                                                    body)
        out += "\n ++++++++++++++++++++++++++++++++++++++\n"
        return out

    def __init__(self):
        self.valid = True
        self.errors = {}
        self.error = False
        self.code = 999
        self.first_line = b''
        self.headers = []
        self.body = b''
        self.body_size = 0
        self.chunked = False
        self.chunks = []
        self.chunk_size = 0
        self.name = u'Message'
        self.short_name = u'Msg.'
        # for multiline headers
        self.has_previous_header = False

    def _parse_first_line(self, first_line):
        'Incomplete implementation, please override.'
        return self.STATUS_BODY

    def parse_first_line(self, first_line):
        if b'\n' == first_line or b'\r\n' == first_line:
            # this is not really a response or request, more an allowed
            # extra CRLF separator between messages, for old servers
            return self.STATUS_OPTIONAL_SEPARATOR
        else:
            # quite certainly something to rewrite in child implementations
            return self._parse_first_line(first_line)

    def parse_header_line(self, line):
        if b'\n' == line or b'\r\n' == line:
            return self.STATUS_BODY
        else:
            header = Header().parse(line)
            if (header.error and
                    Header.ERROR_MULTILINE_OPTIONAL in header.errors):
                # oups, this is in fact the previous header continuation
                if not self.has_previous_header:
                    self.setError(self.ERROR_FIRST_HEADER_OPS_FOLD)
                else:
                    previous_header = self.headers.pop()
                    previous_header.merge_value(header)
                    header = previous_header
            else:
                self.has_previous_header = True

            self.headers.append(header)
            if not header.valid:
                self.setError(self.ERROR_HAS_INVALID_HEADER)
            else:
                if header.error:
                    # non critical error
                    self.setError(self.ERROR_HAS_INVALID_HEADER,
                                  critical=False)
            return self.STATUS_HEADERS

    def analyze_headers(self, compute_content_length=True):
        "We have all headers, not extract some informations from it."

        self.has_cl = False
        for header in self.headers:

            if 'CONTENT-LENGTH' == header.header:
                if self.has_cl:
                    self.setError(self.ERROR_HAS_INVALID_HEADER)
                    self.setError(self.ERROR_DOUBLE_CONTENT_LENGTH)
                    # we should stop here in a regular parser
                    # but for this parser we'll keep the last one talking as
                    # the right one
                if self.chunked:
                    self.setError(self.ERROR_HAS_INVALID_HEADER)
                    self.setError(self.ERROR_CONTENT_LENGTH_AND_CHUNKED)
                if not header.value.isdigit():
                    self.setError(self.ERROR_HAS_INVALID_NUMERIC_HEADER)
                else:
                    if compute_content_length:
                        self.body_size = int(header.value)
                    self.has_cl = True

            if 'TRANSFER-ENCODING' == header.header:
                hval = header.value.strip()
                # FIXME: is CHUNKED valid?
                if hval[-7:] == 'chunked':
                    self.chunked = True
                    if self.has_cl:
                        self.setError(self.ERROR_CONTENT_LENGTH_AND_CHUNKED)
                else:
                    if 'chunked' in hval:
                        self.setError(self.ERROR_BAD_CHUNKED_HEADER)

    def parse_chunk_header(self, line):
        chunk = Chunk().parse(line)
        self.chunks.append(chunk)
        if not chunk.valid:
            self.setError(self.ERROR_HAS_INVALID_CHUNK)
            # TODO: in case of invalid chunk we should maybe stop analysis
            self.chunk_size = 0
        else:
            if chunk.error:
                # non critical error
                self.setError(self.ERROR_HAS_BAD_CHUNK, critical=False)
            self.chunk_size = chunk.real_size
        return self.STATUS_CHUNK

    def get_expected_chunk_size(self):
        return self.chunk_size

    def get_expected_body_size(self):
        "Return expected body size. Requests and responses are different"
        # WARNING: @see request and response implementations
        return self.body_size

    def parse_body(self, data):
        self.body = data
        return self.STATUS_COMPLETED

    def parse_chunk(self, data):
        datalen = len(data)
        if datalen == self.chunk_size:
            # this is wrong, we should have a CRLF after the chunk
            self.setError(self.ERROR_HAS_INVALID_CHUNK_DATA)
        if b'\r\n' != data[-2:]:
            # we should only have CRLF after the chunk
            self.setError(self.ERROR_HAS_EXTRA_CHUNK_DATA, critical=False)
            if b'\n' != data[-1:]:
                data = data[:-1]
        else:
            data = data[:-2]
        datalen = len(data)
        if datalen != self.chunk_size:
            # we should only have CRLF after the chunk
            self.setError(self.ERROR_HAS_EXTRA_CHUNK_DATA, critical=False)
            data = data[:self.chunk_size]

        self.body += data
        if self.chunk_size == 0:
            # this was the last chunk
            return self.STATUS_COMPLETED
        else:
            return self.STATUS_CHUNK_HEADER

    def setError(self, msgidx, critical=True):
        self.errors[msgidx] = True
        if critical:
            self.valid = False
        self.error = True
