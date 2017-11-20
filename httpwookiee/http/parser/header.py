#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
import string
from httpwookiee.core.tools import Tools
from httpwookiee.http.parser.line import Line
from httpwookiee.http.parser.exceptions import PrematureEndOfStream


class Header(Line):

    # STATUS_START = 0
    STATUS_NAME = 1
    STATUS_AFTER_SP = 2
    # STATUS_READING_START = 13
    # STATUS_READING = 14
    # STATUS_AFTER_CR = 15
    # STATUS_END = 16
    STATUS_READING_QUOTED_PAIR = 17
    STATUS_READING_LOST_QUOTED_PAIR = 18
    STATUS_READING_QUOTED_STRING = 19

    ERROR_EMPTY_NAME = 'Empty header name'
    ERROR_SPACE_BEFORE_SEP = 'Space before separator'
    ERROR_SPACE_AT_EOL = 'Space in header suffix'
    ERROR_INVALID_CHAR_IN_NAME = 'Invalid character in header name'
    ERROR_MULTILINE_OPTIONAL = 'Optional Multiline Header detected'
    ERROR_WAS_MULTILINE_OPTIONAL = 'Optional Multiline Header merged'
    ERROR_EOL_INSIDE_QUOTES = 'End of line before end of quotes'
    ERROR_QUOTED_PAIR_WITHOUT_QUOTES = 'Quoted pair syntax without quotes'

    def __str__(self):
        out = ''
        if self.error:
            if not self.valid:
                out += "**INVALID HEADER <"
            else:
                out += "**BAD HEADER <"
            for error, value in Tools.iteritems(self.errors):
                out += " {0};".format(error)
            out += ">**\n"
        out += "{0}[{1}] {2}[{3}]{4} [{5}] {6}[{7}]\n".format(
            self.header_prefix,
            self.header,
            self.separator_prefix,
            self.separator,
            self.value_prefix,
            self.value,
            self.value_suffix,
            self.eof)
        return out

    def __init__(self):
        super(Header, self).__init__()
        self.header_prefix = u''
        self.header = u''
        self.separator_prefix = u''
        self.separator = u''
        self.value_suffix = u''
        # internal temp storage
        self.stacked_repr_str = u''

    def merge_value(self, other_h):
        """merge this header value with another header (multiline headers)

        Long after the end of parsing the header, parsing the next line,
        and ops_fold multiline header was detected. This headers is now coming
        back with this one the be merged as the value part.
        We need to catch errors on the value header and mix it with the current
        one.
        """
        if self.value == u'':
            if other_h.value_prefix != u'':
                self.value_prefix = u'{0}{1}{2}'.format(self.value_prefix,
                                                        self.value_suffix,
                                                        other_h.value_prefix)
                self.value = u'{0}{1}'.format(other_h.value_prefix,
                                              other_h.value)
        else:
            self.value = u'{0}{1}{2}{3}'.format(self.value,
                                                self.value_suffix,
                                                other_h.value_prefix,
                                                other_h.value)
        self.suffix = other_h.value_suffix
        self.eof = other_h.eof
        for error, value in Tools.iteritems(other_h.errors):
            if error != self.ERROR_MULTILINE_OPTIONAL:
                self.setError(error, critical=False)
        self.setError(self.ERROR_WAS_MULTILINE_OPTIONAL, critical=False)
        if not other_h.valid:
            self.valid = False

    def step_start(self, char):

        if self._is_space(char,
                          'header_prefix',
                          extended=False,
                          critical=True):
            # Well, <SP> as header prefix is the mark of the official obs-fold
            # obs-fold       = CRLF 1*( SP / HTAB )
            # so we are in fact in a multiline header!
            self.setError(self.ERROR_MULTILINE_OPTIONAL, critical=False)
            self.value_prefix += '<SP>'
            return self.STATUS_READING_START

        if self._is_lf_or_crlf(char):
            # Not the right place for a line termination
            self.setError(self.ERROR_PREMATURE_EOL)
            return self.STATUS_END

        if ':' == char:
            self.setError(self.ERROR_EMPTY_NAME)
            self.separator += char
            return self.STATUS_READING_START

        return self._add_header_char(char)

    def _add_header_char(self, char):
        """subroutine for step_start and step_name"""
        # All visible ascii chars are allowed
        # do not use string.printable as this includes FF, BEL and CR, etc
        chars = string.digits + string.ascii_letters + string.punctuation + ' '
        if ((char not in chars) or
                (char in Tools.NO_TOKEN_CHARS_VALUES)):
            self.setError(self.ERROR_INVALID_CHAR_IN_NAME)
            self.header += '<Err>'
        else:
            self.header += char.upper()
        return self.STATUS_NAME

    def step_name(self, char):
        "This is the header name."
        if self._is_lf_or_crlf(char):
            # Not the right place for a line termination
            self.setError(self.ERROR_PREMATURE_EOL)
            return self.STATUS_END

        # Note that SP is also a bad space in header name
        if Tools.TAB == char or Tools.CR == char:
            self.setError(self.ERROR_BAD_SPACE, critical=False)
            self.stacked_repr_str = '<BS>'
            return self.STATUS_AFTER_SP
        if Tools.SP == char:
            self.setError(self.ERROR_INVALID_CHAR_IN_NAME, critical=False)
            self.stacked_repr_str = '<ErrSP>'
            return self.STATUS_AFTER_SP

        if ':' == char:
            self.separator += char
            return self.STATUS_READING_START

        return self._add_header_char(char)

    def step_after_space(self, char):
        """Either we are working with separator prefix or inside the name.

        """
        if self._is_lf_or_crlf(char):
            # Not the right place for a line termination
            self.setError(self.ERROR_PREMATURE_EOL)
            return self.STATUS_END

        if ':' == char:
            self.separator += char
            # bad spaces before the separator.
            # https://tools.ietf.org/html/rfc7230#section-3.2.4
            self.setError(self.ERROR_SPACE_BEFORE_SEP, critical=True)
            self.separator_prefix = self.stacked_repr_str
            self.stacked_repr_str = u''
            return self.STATUS_READING_START

        if Tools.TAB == char or Tools.CR == char:
            self.setError(self.ERROR_BAD_SPACE, critical=False)
            self.stacked_repr_str += '<BS>'
            return self.STATUS_AFTER_SP
        if Tools.SP == char:
            self.setError(self.ERROR_INVALID_CHAR_IN_NAME, critical=False)
            self.stacked_repr_str += '<ErrSP>'
            return self.STATUS_AFTER_SP

        # Ok, this was just a (bad) space in the Header name
        self.header += self.stacked_repr_str
        self.stacked_repr_str = u''
        self.header += char.upper()
        return self.STATUS_NAME

    def step_reading_start(self, char):
        "Value pre-reading, where SP and BS are ignored."

        if self._is_lf_or_crlf(char):
            # empty header value, let's say it's allowed
            # as it could in fact also be a multiline header
            return self.STATUS_END

        if (Tools.TAB == char or Tools.CR == char):
            self.setError(self.ERROR_BAD_SPACE, critical=False)
            self.value_prefix += '<BS>'
            return self.STATUS_READING_START
        if Tools.SP == char:
            self.value_prefix += '<SP>'
            return self.STATUS_READING_START

        return self._add_value_char(char)

    def step_read_value(self, char):
        "Default value reading, everything is allowed, waiting for LF or CRLF."
        if self._is_lf_or_crlf(char):
            # all things done, but let's check if we had some space suffix
            # on previous run of this function
            if self.stacked_repr_str != u'':
                self.value_suffix = self.stacked_repr_str
                # TODO: FIXME: what is this???? where are the previous spaces??
                self.setError(self.ERROR_SPACE_AT_EOL, critical=False)
            return self.STATUS_END

        if (Tools.VTAB == char or Tools.CR == char or Tools.FF == char):
            self.setError(self.ERROR_BAD_SPACE, critical=False)
            self.stacked_repr_str += '<BS>'
            return self.STATUS_READING
        if (Tools.SP == char or Tools.TAB == char):
            self.stacked_repr_str += '<SP>'
            return self.STATUS_READING

        for achar in self.stacked_repr_str:
            self.value += achar
        self.stacked_repr_str = u''
        return self._add_value_char(char)

    def step_read_qstring(self, char):
        "TODO: FIXME: work in progress..."

        # TODO: apply difference of char list allowed in quoted
        # and unquoted strings
        if self._is_lf_or_crlf(char):
            self.setError(self.ERROR_EOL_INSIDE_QUOTES, critical=False)
            # all things done, but let's check if we had some space suffix
            # on previous run of this function
            # if self.stacked_repr_str != u'':
            #     self.value_suffix = self.stacked_repr_str
            #     todo: ??
            #     self.setError(self.ERROR_SPACE_AT_EOL, critical=False)
            return self.STATUS_END

        # TODO if u'\\' == char:
        # You can backslash-escape all literal space and tab characters inside
        # a quoted string, so $' \t' becomes $'\\ \\ \\\t' (or, if you want a
        # more visual representation, ··→ becomes "\·\·\→"),
        # and newlines and other control characters are just lost
        #
        # qdtext         = any TEXT except " and \

        return self._add_value_char(char, qstring=True)

    def _add_value_char(self, char, qstring=False):
        if u'\\' == char:
            if qstring:
                return self.STATUS_READING_QUOTED_PAIR
            else:
                self.setError(self.ERROR_QUOTED_PAIR_WITHOUT_QUOTES,
                              critical=False)
                return self.STATUS_READING_LOST_QUOTED_PAIR
        if u'"' == char:
            self.value += char
            if qstring:
                return self.STATUS_READING
            else:
                return self.STATUS_READING_QUOTED_STRING
        self.value += char
        if qstring:
            return self.STATUS_READING_QUOTED_STRING
        else:
            return self.STATUS_READING

    def step_read_lost_qpair(self, char):
        "TODO: FIXME: work in progress..."
        octet = ord(char)
        char = chr(octet)
        return self.step_read_value(char)

    def step_read_qpair(self, char):
        "TODO: FIXME: work in progress..."
        octet = ord(char)
        char = chr(octet)
        return self.step_read_qstring(char)

    def tokenize(self):
        status = self.STATUS_START
        automat = {self.STATUS_START: 'step_start',
                   self.STATUS_NAME: 'step_name',
                   self.STATUS_AFTER_SP: 'step_after_space',
                   self.STATUS_READING_START: 'step_reading_start',
                   self.STATUS_READING: 'step_read_value',
                   self.STATUS_READING_QUOTED_PAIR: 'step_read_qpair',
                   self.STATUS_READING_LOST_QUOTED_PAIR: 'step_read_lost_'
                                                         'qpair',
                   self.STATUS_READING_QUOTED_STRING: 'step_read_qstring',
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
