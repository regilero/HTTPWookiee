#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
from httpwookiee.core.tools import Tools
from httpwookiee.http.parser.message import Message
from httpwookiee.http.parser.exceptions import (EndOfBufferError,
                                                PrematureEndOfStream,
                                                OptionalCRLFSeparator)
import six


class Messages(object):

    ERROR_HAS_INVALID_MESSAGE = 'Has invalid Message'
    ERROR_HAS_BAD_MESSAGE = 'Has bad Message'
    ERROR_BAD_MESSAGES_SEPARATOR = 'Invalid Messages Separators'
    ERROR_INCOMPLETE_STREAM = 'Incomplete stream'

    def __init__(self, rfc=False):
        self.count = 0
        self.messages = []
        self.index = 0
        self.byteidx = 0
        self.parsed_idx = 0
        self.valid = True
        self.errors = {}
        self.error = False
        self.name = u'Messages'

    def _getMessage(self):
        'Create base message object, you certainly need to override'
        return Message()

    def __str__(self):
        out = ""
        if not self.valid:
            out = "******INVALID {0} STREAM <".format(self.name)
            for error, value in Tools.iteritems(self.errors):
                out += " {0};".format(error)
            out += ">******\n"
        out += "-{0} {1}-".format(self.count, self.name)
        for resp in self.messages:
            out += "\n---\n{0}\n---".format(resp)
        return out

    def __getitem__(self, index):
        return self.messages[index]

    def __setitem__(self, key, item):
        self.messages[key] = item

    def __len__(self):
        return len(self.messages)

    def parse(self,
              bufferstr,
              compute_content_length=True,
              requests_infos=None):
        "Parse an HTTP message (may contain several messages)."
        self.extract_messages(bufferstr,
                              compute_content_length,
                              requests_infos)
        return self

    def extract_messages(self,
                         bufferstr,
                         compute_content_length=True,
                         requests_infos=None):
        full_len = len(bufferstr)
        self.byteidx = 0
        self.parsed_idx = 0
        if full_len == 0:
            return
        self.bytesbuff = six.binary_type(bufferstr)

        while self.byteidx < full_len:
            try:
                # print('extraction {0}!{1}'.format(self.byteidx, full_len))
                # this is for responses, they may have a related parent method
                # listed in requests_infos (for HEAD/CONNECT, etc)
                parent_request_method = None
                if ((requests_infos is not None) and
                        (len(requests_infos) > self.count)):
                    parent_request_method = requests_infos[self.count]

                msg = self.extract_one_message(compute_content_length,
                                               parent_request_method)
            except OptionalCRLFSeparator:
                # this is not an error, raised only at end of buffer
                # so we can safely break the loop
                break
            except PrematureEndOfStream:
                msg = False
                self.setError(self.ERROR_INCOMPLETE_STREAM)

            self.check_message_status(msg)

    def check_message_status(self, msg):
        "@see responses for interim responses specific stuff"
        if msg is not False:
            self.count = self.count + 1
            self.messages.append(msg)
            if not msg.valid:
                # print(msg)
                self.setError(self.ERROR_HAS_INVALID_MESSAGE)
            elif msg.error:
                # print(msg)
                self.setError(self.ERROR_HAS_BAD_MESSAGE, critical=False)
            self.parsed_idx = self.byteidx
        else:
            self.setError(self.ERROR_HAS_INVALID_MESSAGE)

    def extract_one_message(self,
                            compute_content_length=True,
                            parent_request_method=None):
        """Return one HTTP Request or response, and set the internal buffer
        index right after that message."""
        msg = self._getMessage()
        try:

            status = self.parse_start_of_stream(msg)
            if status is False:
                return False

            # Parse HEADERS, LF separated ascii lines------
            while Message.STATUS_HEADERS == status:
                line = self.parse_line_from_buffer()
                status = msg.parse_header_line(line)

            msg.analyze_headers(compute_content_length)
            msg.detect_empty_body_conditions(parent_request_method)
            if ((status == Message.STATUS_BODY) and
                    (msg.chunked) and
                    (not msg.empty_body_expected)):
                status = Message.STATUS_CHUNK_HEADER

            # Parse body, abstract binary content lines------
            while status != Message.STATUS_COMPLETED:

                if Message.STATUS_BODY == status:

                    # FIXME: here we may have a problem if our current buffer
                    # is shorter than the whole received message (in 0.9 or if
                    # no Content-Length header was transmitted...)
                    if msg.version_major == 0 and msg.version_minor == 9:
                        # http 0.9 request or response, read all
                        size_of_body = len(self.bytesbuff) - self.byteidx
                    else:
                        size_of_body = msg.get_expected_body_size()
                        if Message.READ_UNTIL_THE_END == size_of_body:
                            size_of_body = len(self.bytesbuff) - self.byteidx
                    data = self.extract_size_from_buffer(size_of_body)
                    status = msg.parse_body(data)

                if Message.STATUS_CHUNK_HEADER == status:
                    line = self.parse_line_from_buffer()
                    status = msg.parse_chunk_header(line)

                if Message.STATUS_CHUNK == status:
                    size_of_chunk = msg.get_expected_chunk_size()
                    data = self.extract_chunk_from_buffer(size_of_chunk)
                    status = msg.parse_chunk(data)

            return msg

        except (EndOfBufferError, PrematureEndOfStream):
            # a line-read or nb-bytes-read reached EOS, should not happen
            # unless stream is incomplete
            raise PrematureEndOfStream

    def parse_start_of_stream(self, msg):
        firstline = self.parse_line_from_buffer()
        status = msg.parse_first_line(firstline)
        if Message.STATUS_OPTIONAL_SEPARATOR == status:
            # Ok, it was not really the first line, this is allowed 1 time
            # but 1 time only
            try:
                firstline = self.parse_line_from_buffer()
                status = msg.parse_first_line(firstline)
            except EndOfBufferError:
                # well, it was an extra CRLF at the end
                raise OptionalCRLFSeparator()
            while Message.STATUS_OPTIONAL_SEPARATOR == status:
                # oups, we've got too much CRLF between requests/responses
                self.setError(self.ERROR_BAD_MESSAGES_SEPARATOR)
                try:
                    firstline = self.parse_line_from_buffer()
                    status = msg.parse_first_line(firstline)
                except EndOfBufferError:
                    # we've reach EOS on a CRLF or LF serie
                    return False
        return status

    def read_one_byte(self):
        """Read one byte from the internal Buffer,
        and increment index for next read"""
        try:
            elt = self.bytesbuff[self.byteidx]
        except IndexError:
            # that's the end, my friend
            raise EndOfBufferError()

        # detect python3
        if isinstance(elt, int):
            # p3
            byte = bytes([elt])
        else:
            # p2
            byte = bytes(elt)
        self.byteidx = self.byteidx + 1
        return byte

    def parse_line_from_buffer(self):
        """Read one line from buffer (end at \n or EOS).
        May raise EndOfBufferError if you try to read one more time after
        the end."""
        line = bytes()

        # this may send an uncatched EndOfBufferError exception
        byte = self.read_one_byte()

        while byte:
            line = line + byte
            if byte == b'\n':
                # line terminated
                return line
            else:
                try:
                    byte = self.read_one_byte()
                except EndOfBufferError:
                    # here exception is catched and line truncated to
                    # end of buffer instead of \n
                    return line

    def extract_size_from_buffer(self, size):
        "Extract given bytes from the internal buffer and move the read index."
        data = bytes()
        # FIXME: if speed is a problem, and currently it's not a problem,
        # there's certainly better way to read than byte after byte ...
        # But this parser is not made for speed
        while size > 0:
            try:
                byte = self.read_one_byte()
            except EndOfBufferError:
                raise PrematureEndOfStream()
            data = data + byte
            size = size - 1
        return data

    def extract_chunk_from_buffer(self, size):
        """Extract given bytes from the internal buffer and move the read index.
        returned data may be shorter if EOS is reached. Note that the chunk
        really ends at the next EOL after this size. So we extract some more
        bytes."""
        data = self.extract_size_from_buffer(size)
        # The chunk content is now extracted, read the next chunk part
        data = data + self.parse_line_from_buffer()
        return data

    def setError(self, msgidx, critical=True):
        self.errors[msgidx] = True
        if critical:
            self.valid = False
        self.error = True
