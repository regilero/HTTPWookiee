#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
from httpwookiee.core.tools import Tools
from httpwookiee.http.parser.exceptions import PrematureEndOfStream


class Line(object):
    """Line based parser (CR/LF or LF terminated line state parser)"""

    STATUS_START = 0
    STATUS_READING_START = 13
    STATUS_READING = 14
    STATUS_AFTER_CR = 15
    STATUS_END = 16

    ERROR_PREMATURE_EOL = 'Premature end of line'
    ERROR_LF_WITHOUT_CR = 'Line end is LF and not CRLF'
    ERROR_BAD_SPACE = 'Bad space separator'
    ERROR_BAD_CHARACTER = 'Bad character detected'
    ERROR_SHOULD_BE_REJECTED = 'Message should be Rejected'
    ERROR_MULTIPLE_CR = 'Multiple CR detected'
    ERROR_BAD_UTF8 = 'Bad Utf-8 characters detected'

    def __init__(self):
        self.valid = True
        self.error = False
        self.errors = {}
        self.value_prefix = u''
        self.value = u''
        self.eof = u''
        self.readidx = 0

    def parse(self, line):
        self.raw = line
        self.tokenize()
        return self

    def read_char(self):
        elt = self.raw[self.readidx]
        # detect python3
        if isinstance(elt, int):
            if elt in [192, 141, 138]:
                self.setError(self.ERROR_BAD_UTF8, critical=False)
            # py 3
            char = chr(elt)
        else:
            # py 2
            char = elt
            if char in ['\xC0', '\x8D', '\x8A']:
                # our bad utf-8 tests may crash python 2
                char = Tools.BYTES_SPECIAL_REPLACE
                self.setError(self.ERROR_BAD_UTF8, critical=False)
        self.readidx = self.readidx + 1
        return char

    def _is_space(self, char, str_attr, extended=True, critical=False):
        """check various bad and good spaces.

        -----------------------
        RFC 7230 3.5. Message Parsing Robustness
        In the interest of robustness, a server that is expecting to receive
        and parse a request-line SHOULD ignore at least one empty line (CRLF)
        received prior to the request-line.

        Although the line terminator for the start-line and header fields is
        the sequence CRLF, a recipient MAY recognize a single LF as a line
        terminator and ignore any preceding CR.
        Although the request-line and status-line grammar rules require that
        each of the component elements be separated by a single SP octet,
        recipients MAY instead parse on whitespace-delimited word boundaries
        and, aside from the CRLF terminator, treat any form of whitespace as
        the SP separator while ignoring preceding or trailing whitespace;
        such whitespace includes one or more of the following octets: SP,
        HTAB, VT (%x0B), FF (%x0C), or bare CR.  However, lenient parsing can
        result in security vulnerabilities if there are multiple recipients
        of the message and each has its own unique interpretation of
        robustness (see Section 9.5).

        When a server listening only for HTTP request messages, or processing
        what appears from the start-line to be an HTTP request message,
        receives a sequence of octets that does not match the HTTP-message
        grammar aside from the robustness exceptions listed above, the server
        SHOULD respond with a 400 (Bad Request) response.
        -----------------------
        So here we check for TAB, VTAB, and CR as pseudo-valid BS separators
        (BS means Bad Space).
        given str_attr local attribute is feed with '<BS>' or '<SP>' value
        """
        charlist = [Tools.TAB]
        if extended:
            charlist.append(Tools.VTAB)
            charlist.append(Tools.FF)
            charlist.append(Tools.CR)
        if char in charlist:
            self.setError(self.ERROR_BAD_SPACE, critical=critical)
            setattr(self, str_attr, getattr(self, str_attr) + u'<BS>')
            return True
        if char == Tools.SP:
            setattr(self, str_attr, getattr(self, str_attr) + u'<SP>')
            return True
        return False

    def _is_lf_or_crlf(self, char):
        """Check for End of line, which may be LF or CRLF or CRCRLF, etc.
        The right one is CRLF; LF or (CR)*LF are 'minor' wrong endings.
        CR alone is not a valid EOL and will return False (see _is_space).
        """
        if char == Tools.CR:
            if not self.eof == u'':
                self.setError(self.ERROR_MULTIPLE_CR, critical=False)
            self.eof += u'[CR]'
            # memorize the real read index, in case we do not find any LF
            next_index = self.readidx
            try:
                next_char = self.read_char()
            except IndexError:
                raise PrematureEndOfStream
            if self._is_lf_or_crlf(next_char):
                # Ok, this was a CRLF or (CR)*LF
                return True
            else:
                # hack back the read index
                self.readidx = next_index
                # and our eof memory
                self.eof = u''
                return False

        if char == Tools.LF:
            # Victory, LF found, end of line!
            if self.eof == u'':
                self.setError(self.ERROR_LF_WITHOUT_CR, critical=False)
            self.eof += u'[LF]'
            # this is the only way to end recursion with True
            return True

        return False

    def _is_forbidden(self, char, in_uri=False, in_domain=False):
        """Some characters are always bad, on most places, easy detection.

        Some chars are forbidden in uri, and that's more complex:
        absolute-path = 1*( "/" segment )
        segment = <segment, see [RFC3986], Section 3.3> => segment = *pchar
        query = <query, see [RFC3986], Section 3.4> : *( pchar / "/" / "?" )
        pchar = unreserved / pct-encoded / sub-delims / ":" / "@"
        unreserved  = ALPHA / DIGIT / "-" / "." / "_" / "~"
        sub-delims    = "!" / "$" / "&" / "'" / "(" / ")"
                     / "*" / "+" / "," / ";" / "="
        rfc2234 ALPHA:  %x41-5A / %x61-7A   ; A-Z / a-z
        rfc2234 DIGIT:  =  %x30-39 ; 0-9
        warning: '#' mark the end of query
        warning2:  For consistency, percent-encoded octets in the ranges of
        ALPHA (%41-%5A and %61-%7A), DIGIT (%30-%39), hyphen (%2D),
        period (%2E), underscore (%5F), or tilde (%7E) should not be created
        by URI producers and, when found in a URI, should be decoded to their
        corresponding unreserved characters by URI normalizers

        Warnings are not handled here. We just filter characters which are
        nowhere on this list
        """
        ordval = ord(char)
        # ALPHA
        if 0x61 <= ordval <= 0x7A or 0x41 <= ordval <= 0x5A:
            return False
        # DIGIT
        if 0x30 <= ordval <= 0x39:
            return False
        # @see also _is_space(char)
        # "/"(47) / ":"(58) /  "SP"(32) / "HTAB"(9) / "VTAB"(11) /
        # "FF"(12) / "CR"(13) / "LF"(10)
        if ordval in [9, 10, 11, 12, 13, 32, 47, 58, 64]:
            if in_domain:
                return True
            return False

        if in_domain:
                #  "-"(45) / "."(46)
                if ordval in [45, 46]:
                    return False
        else:
            if in_uri:
                # '%'(37) / "@"(64) / "-"(45) / "."(46) / "_"(95) / "~"(126) /
                # "!"(33) / "$"(36) / "&"(38) / "'"(39) / "("(40) / ")"(41) /
                # "*"(42) / "+"(43) / ","(44) / ";"(59) / "="(61) / "?"(63)
                if ordval in [33, 36, 37, 38, 39, 40, 41, 42, 43,
                              44, 45, 46, 59, 61, 63, 64, 95, 126]:
                    return False

        # well, wtf are you, something like NULL?
        return True

    def step_start(self, char):
        # fake parser, we got directly on value reading, by default
        return self.step_reading_start(char)

    def step_reading_start(self, char):
        "Default Value pre-reading, where SP and BS are ignored."
        if self._is_space(char, 'value_prefix', extended=False):
            # ignore starting spaces
            return self.STATUS_READING_START

        if self._is_lf_or_crlf(char):
            # Not the right place for a line termination
            self.setError(self.ERROR_PREMATURE_EOL)
            return self.STATUS_END

        self.value += char
        return self.STATUS_READING

    def step_read_value(self, char):
        "Default value reading, everything is allowed, waiting for LF or CRLF."
        if self._is_lf_or_crlf(char):
            return self.STATUS_END

        self.value += char
        return self.STATUS_READING

    # @deprecated
    def step_wait_for_lf(self, char):
        if '\n' == char:
            self.eof += u'[LF]'
            return self.STATUS_END
        else:
            # well in fact it was not the end
            # this is allowed for multi lines headers
            self.value += u'[CR]' + char
            self.eof = u''
            return self.STATUS_READING_START

    def tokenize(self):
        """This is a fake one, use it as a model"""
        status = self.STATUS_START
        automat = {self.STATUS_START: 'step_start',
                   self.STATUS_READING_START: 'step_reading_start',
                   self.STATUS_READING: 'step_read_value',
                   self.STATUS_AFTER_CR: 'step_wait_for_lf',
                   self.STATUS_END: 'step_end'}
        while self.STATUS_END != status:
            try:
                char = self.read_char()
            except IndexError:
                raise PrematureEndOfStream
                break
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
