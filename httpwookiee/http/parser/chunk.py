#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
import string
from httpwookiee.core.tools import Tools
from httpwookiee.http.parser.line import Line
from httpwookiee.http.parser.exceptions import PrematureEndOfStream
import sys


class Chunk(Line):

    # STATUS_START = 0
    STATUS_SIZE_START = 1
    STATUS_SIZE = 2
    STATUS_AFTER_SIZE = 3
    STATUS_TRAILER = 4
    # STATUS_AFTER_CR = 15
    # STATUS_END = 16

    ERROR_BAD_CHUNK_HEADER = 'Bad chunk header'
    ERROR_BAD_CHUNK_START = 'Bad chunk start'
    ERROR_BAD_CHUNK_SIZE = 'Bad chunk size'
    ERROR_BAD_TRAILER = 'Bad trailer part'
    ERROR_EXTRA_CHARACTERS = 'Has some extra characters'

    def __str__(self):
        out = ''
        if self.error:
            if sys.version_info[0] < 3:
                # python2
                out += "**(raw):{0}**".format(
                    self.raw.replace('\r', '\\r').replace('\n', '\\n'))
            else:
                out += "**(raw):{0}**".format(self.raw)
            if not self.valid:
                out += "**INVALID CHUNK <"
            else:
                out += "**BAD CHUNK <"
            for error, value in Tools.iteritems(self.errors):
                out += " {0};".format(error)
            out += ">**\n"
        if self.is_last_chunk:
            out += "[LAST CHUNK] "
        if self.size == b'':
            out += '--unkown size--'
        else:
            if self.has_trailer:
                out += "[{0} ({1})] ;[{2}] [{3}]\n".format(
                    self.size,
                    int(self.size, 16),
                    self.trailer,
                    self.eof)
            else:
                out += "[{0} ({1})] [{2}]\n".format(
                    self.size,
                    self.real_size,
                    self.eof)
        return out

    def __init__(self):
        super(Chunk, self).__init__()
        self.size = u'0'
        self.real_size = 0
        self.nb_zero_prefix = 0
        self.has_trailer = False
        self.trailer = u''
        self.is_last_chunk = False

    def _add_size_char(self, char, start=False):
        if '0' == char and start:
            self.nb_zero_prefix += 1
            self.is_last_chunk = True
            if self.nb_zero_prefix > 5:
                # may be an int truncation attempt
                self.setError(self.ERROR_BAD_CHUNK_SIZE,
                              critical=False)
            return self.STATUS_SIZE_START
        else:
            self.is_last_chunk = False
            self.size += char
            # TODO: check for python overflow
            self.real_size = int(self.size, 16)
            return self.STATUS_SIZE

    def step_start(self, char):
        if ' ' == char or '\t' == char:
            # spaces before name
            self.setError(self.ERROR_BAD_CHUNK_START, critical=False)
            return self.STATUS_START
        if char in string.hexdigits:
            return self._add_size_char(char, start=True)
        self.setError(self.ERROR_BAD_CHUNK_HEADER)
        self.setError(self.ERROR_BAD_CHUNK_SIZE)
        return self.STATUS_END

    def step_size_start(self, char):
        if char in string.hexdigits:
            return self._add_size_char(char, start=True)
        if ' ' == char:
            return self.STATUS_AFTER_SIZE
        if '\t' == char:
            self.setError(self.ERROR_BAD_SPACE, critical=False)
            return self.STATUS_AFTER_SIZE
        if ';' == char:
            return self.STATUS_TRAILER
        if '\r' == char:
            self.eof += u'[CR]'
            return self.STATUS_AFTER_CR
        if '\n' == char:
            self.setError(self.ERROR_LF_WITHOUT_CR, critical=False)
            self.eof += u'[LF]'
            return self.STATUS_END
        # other chars are bad
        self.setError(self.ERROR_BAD_CHUNK_HEADER)
        return self.STATUS_END

    def step_size(self, char):
        if char in string.hexdigits:
            return self._add_size_char(char)
        if ' ' == char:
            return self.STATUS_AFTER_SIZE
        if '\t' == char:
            self.setError(self.ERROR_BAD_SPACE, critical=False)
            return self.STATUS_AFTER_SIZE
        if ';' == char:
            return self.STATUS_TRAILER
        if '\r' == char:
            self.eof += u'[CR]'
            return self.STATUS_AFTER_CR
        if '\n' == char:
            self.setError(self.ERROR_LF_WITHOUT_CR, critical=False)
            self.eof += u'[LF]'
            return self.STATUS_END
        # other chars are bad
        self.setError(self.ERROR_BAD_CHUNK_HEADER)
        return self.STATUS_END

    def step_after_size(self, char):
        if ';' == char:
            return self.STATUS_TRAILER
        if ' ' == char or '\t' == char:
            if '\t' == char:
                self.setError(self.ERROR_BAD_SPACE, critical=False)
            self.setError(self.ERROR_EXTRA_CHARACTERS, critical=False)
            return self.STATUS_AFTER_SIZE
        if '\r' == char:
            self.eof += u'[CR]'
            return self.STATUS_AFTER_CR
        if '\n' == char:
            self.setError(self.ERROR_LF_WITHOUT_CR, critical=False)
            self.eof += u'[LF]'
            return self.STATUS_END
        # other chars are bad
        self.setError(self.ERROR_BAD_CHUNK_HEADER)
        return self.STATUS_END

    def step_read_trailer(self, char):
        if '\r' == char:
            self.eof += u'[CR]'
            return self.STATUS_AFTER_CR
        if '\n' == char:
            self.setError(self.ERROR_LF_WITHOUT_CR, critical=False)
            self.eof += u'[LF]'
            return self.STATUS_END
        self.has_trailer = True
        self.trailer += char
        return self.STATUS_TRAILER

    def tokenize(self):
        status = self.STATUS_START
        automat = {self.STATUS_START: 'step_start',
                   self.STATUS_SIZE_START: 'step_size_start',
                   self.STATUS_SIZE: 'step_size',
                   self.STATUS_AFTER_SIZE: 'step_after_size',
                   self.STATUS_TRAILER: 'step_read_trailer',
                   self.STATUS_AFTER_CR: 'step_wait_for_lf',
                   self.STATUS_END: 'step_end'}
        while self.STATUS_END != status:
            try:
                char = self.read_char()
            except IndexError:
                raise PrematureEndOfStream
            if status not in automat:
                raise ValueError('Status {0} is not managed in {1}'.format(
                    status, self.__class__.__name__))
            # print('char:<<<<{0}>>>, step: {1}'.format(char, automat[status]))
            status = getattr(self, automat[status])(char)

    def setError(self, msgidx, critical=True):
        self.errors[msgidx] = True
        if critical:
            self.valid = False
        self.error = True
