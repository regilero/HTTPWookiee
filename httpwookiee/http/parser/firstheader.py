#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
from httpwookiee.core.tools import Tools
from httpwookiee.http.parser.line import Line
from httpwookiee.http.parser.exceptions import PrematureEndOfStream


class FirstRequestHeader(Line):
    # STATUS_START = 0
    STATUS_METHOD = 1
    STATUS_AFTER_METHOD = 2
    STATUS_AFTER_METHOD_SEP = 3
    STATUS_ABS_LOCATION_DOMAIN_START = 4
    STATUS_ABS_LOCATION_DOMAIN = 5
    STATUS_LOCATION = 6
    STATUS_QUERY_STRING = 7
    STATUS_AFTER_URL_SEP = 8
    STATUS_PROTO = 9
    STATUS_AFTER_MAJOR = 10
    STATUS_AFTER_VERSION_SEP = 11
    STATUS_AFTER_MINOR = 12
    # STATUS_READING_START = 13
    # STATUS_READING = 14
    # STATUS_AFTER_CR = 15
    # STATUS_END = 16
    STATUS_WAITING_FOR_SPACE = 90

    # ERROR_SHOULD_BE_REJECTED = 'Request should be Rejected'
    ERROR_MAYBE_09 = 'Maybe an HTTP/0.9 request'
    ERROR_BAD_SPACE_PREFIX = 'Bad space prefix on request'
    ERROR_BAD_SPACE = 'Bad space on request'
    ERROR_BAD_SUFFIX = 'Bad suffix content'
    ERROR_INVALID_METHOD = 'Invalid Request method'
    ERROR_BAD_VERSION = 'Bad HTTP Version'
    ERROR_BAD_DOMAIN_CHARACTER = 'Bad character in domain'
    ERROR_EMPTY_DOMAIN = 'Empty domain in absolute uri'
    ERROR_EMPTY_LOCATION = 'Empty location'

    def __init__(self):
        super(FirstRequestHeader, self).__init__()
        self.method = u''
        self.method_sep = u''
        self.has_absolute_uri = False
        self.proto = u''
        self.domain = u''
        self.location = u''
        self.query_string = u''
        self.has_args = False
        self.url_sep = u''
        self.version_major = 0
        self.version_sep = u''
        self.version_minor = 0
        self.prefix = u''
        self.suffix = u''
        self.reject = False
        # internal temp storage of where we are while waiting for spaces
        self.stacked_status = None
        self.stacked_repr_str = None

    def __str__(self):
        out = ''
        if self.error:
            if self.ERROR_MAYBE_09 in self.errors:
                out += "**(raw):{0}**\n".format(self.raw)
            if not self.valid:
                out += "**INVALID FIRST LINE <"
            else:
                out += "**BAD FIRST LINE <"
            for error, value in Tools.iteritems(self.errors):
                out += " {0};".format(error)
            out += ">**\n"
        out += "{0}[{1}]{2} ".format(self.prefix, self.method, self.method_sep)
        if self.has_absolute_uri:
            out += "<[{0}][{1}]>".format(self.proto, self.domain)
        out += "[{0}]".format(self.location)
        if self.has_args:
            out += "?[{0}]".format(self.query_string)
        out += "{0} HTTP/[{1}][{2}][{3}]".format(
            self.url_sep,
            self.version_major,
            self.version_sep,
            self.version_minor)
        out += " {0}[{1}]\n".format(
            self.suffix,
            self.eof)
        return out

    def _http09(self):
        self.setError(self.ERROR_MAYBE_09)
        self.version_major = 0
        self.version_sep = u'.'
        self.version_minor = 9
        return self.STATUS_END

    def _bad_request(self):
        self.setError(self.ERROR_SHOULD_BE_REJECTED)
        self.reject = True

    def step_start(self, char):
        """filter on valid method names, here we start by first letter from
        GET/HEAD/POST/PUT/DELETE/TRACE/CONNECT/OPTIONS"""
        if char in ['G', 'H', 'P', 'D', 'T', 'C', 'O']:
            self.method += char
            return self.STATUS_METHOD

        # anything else is a bad request (a classical parser should stop here)
        self._bad_request()

        # we do not check for CRLF, this is handled in messages sperators,
        # before the first line parsing
        if self._is_space(char, 'prefix'):
            # Space prefix before method, is very bad, but we can keep trying
            self.method += u'<BS>'
            return self.STATUS_START

        if self._is_forbidden(char):
            self.setError(self.ERROR_BAD_CHARACTER)

        self.method = u'<Err>'
        # wait for a space to go through next step
        self.stacked_status = self.STATUS_AFTER_METHOD_SEP
        self.stacked_repr_str = 'method_sep'
        return self.STATUS_WAITING_FOR_SPACE

    def step_wait_for_space(self, char):
        'We have a waiting status in stacked_status, waiting for a space.'

        if self._is_lf_or_crlf(char):
            # Not the right place for a line termination
            self.setError(self.ERROR_PREMATURE_EOL)
            return self.STATUS_END

        if self._is_space(char, self.stacked_repr_str):
            return self.stacked_status

        if self._is_forbidden(char):
            self.setError(self.ERROR_BAD_CHARACTER)
            self._bad_request()

        # looping
        return self.STATUS_WAITING_FOR_SPACE

    def step_method(self, char):
        """We already have the first letter of the method from
        GET/HEAD/POST/PUT/DELETE/TRACE/CONNECT/OPTIONS.
        check for other chars"""

        if self._is_lf_or_crlf(char):
            # Not the right place for a line termination
            self.setError(self.ERROR_PREMATURE_EOL)
            return self.STATUS_END

        if self._is_space(char, 'method_sep'):
            self.method += u'<Err>'
            return self.STATUS_AFTER_METHOD_SEP

        # GET
        if self.method == u'G':
            try:
                char2 = self.read_char()
            except IndexError:
                raise PrematureEndOfStream
            if u"E" == char and u"T" == char2:
                self.method = u'GET'
                return self.STATUS_AFTER_METHOD

        # PUT/POST
        if self.method == u'P':
            try:
                char2 = self.read_char()
            except IndexError:
                raise PrematureEndOfStream
            if u"U" == char and u"T" == char2:
                self.method = u'PUT'
                return self.STATUS_AFTER_METHOD
            try:
                char3 = self.read_char()
            except IndexError:
                raise PrematureEndOfStream
            if u"O" == char and u"S" == char2 and u"T" == char3:
                self.method = u'POST'
                return self.STATUS_AFTER_METHOD

        # HEAD
        if self.method == u'H':
            try:
                char2 = self.read_char()
                char3 = self.read_char()
            except IndexError:
                raise PrematureEndOfStream
            if u"E" == char and u"A" == char2 and u"D" == char3:
                self.method = u'HEAD'
                return self.STATUS_AFTER_METHOD

        # DELETE
        if self.method == u'D':
            try:
                char2 = self.read_char()
                char3 = self.read_char()
                char4 = self.read_char()
                char5 = self.read_char()
            except IndexError:
                raise PrematureEndOfStream
            if (u"E" == char and u"L" == char2 and u"E" == char3
                    and u"T" == char4 and u"E" == char5):
                self.method = u'DELETE'
                return self.STATUS_AFTER_METHOD

        # TRACE
        if self.method == u'T':
            try:
                char2 = self.read_char()
                char3 = self.read_char()
                char4 = self.read_char()
            except IndexError:
                raise PrematureEndOfStream
            if (u"R" == char and u"A" == char2 and u"C" == char3
                    and u"E" == char5):
                self.method = u'TRACE'
                return self.STATUS_AFTER_METHOD

        # CONNECT
        if self.method == u'C':
            try:
                char2 = self.read_char()
                char3 = self.read_char()
                char4 = self.read_char()
                char5 = self.read_char()
                char6 = self.read_char()
            except IndexError:
                raise PrematureEndOfStream
            if (u"O" == char and u"N" == char2 and u"N" == char3
                    and u"E" == char4 and u"C" == char5 and u"T" == char6):
                self.method = u'CONNECT'
                return self.STATUS_AFTER_METHOD

        # OPTIONS
        if self.method == u'O':
            try:
                char2 = self.read_char()
                char3 = self.read_char()
                char4 = self.read_char()
                char5 = self.read_char()
                char6 = self.read_char()
            except IndexError:
                raise PrematureEndOfStream
            if (u"P" == char and u"T" == char2 and u"I" == char3
                    and u"O" == char4 and u"N" == char5 and u"S" == char6):
                self.method = u'OPTIONS'
                return self.STATUS_AFTER_METHOD

        # Well at least we can say we do not understand this method
        # so now we will wait for a space
        self.method += u'<Err>'
        self.setError(self.ERROR_INVALID_METHOD)

        if self._is_forbidden(char):
            self.setError(self.ERROR_BAD_CHARACTER)
            self._bad_request()

        # wait for a space to go through next step
        self.stacked_status = self.STATUS_AFTER_METHOD_SEP
        self.stacked_repr_str = 'method_sep'
        return self.STATUS_WAITING_FOR_SPACE

    def step_after_method(self, char):
        'method is just terminated, need a separator.'
        if self._is_lf_or_crlf(char):
            # Not the right place for a line termination
            self.setError(self.ERROR_PREMATURE_EOL)
            return self.STATUS_END

        if self._is_space(char, 'method_sep'):
            return self.STATUS_AFTER_METHOD_SEP

        if self._is_forbidden(char):
            self.setError(self.ERROR_BAD_CHARACTER)
            self._bad_request()
            self.setError(self.ERROR_INVALID_METHOD)
            self.method += u'<Err>'
            return self.STATUS_AFTER_METHOD

        # anything else? well not something expected
        self.method += u'<Err>'
        self.setError(self.ERROR_INVALID_METHOD)
        return self.STATUS_AFTER_METHOD

    def step_after_method_sep(self, char):
        'we have at least one separator already.'
        if self._is_space(char, 'method_sep'):
            # too much separators, that's not an error
            return self.STATUS_AFTER_METHOD_SEP

        # GET http://... absolute uri mode
        if char == u'h':
            try:
                backup_index = self.readidx
                char2 = self.read_char()
                char3 = self.read_char()
                char4 = self.read_char()
                char5 = self.read_char()
                char6 = self.read_char()
                char7 = self.read_char()
                char8 = self.read_char()
                if u't' == char2 and u't' == char3 and u'p' == char4:
                    if (u's' == char5
                            and u':' == char6
                            and u'/' == char7
                            and u'/' == char8):
                        self.has_absolute_uri = True
                        self.proto = u'https://'
                        return self.STATUS_ABS_LOCATION_DOMAIN_START
                    if u':' == char5 and u'/' == char6 and u'/' == char7:
                        self.has_absolute_uri = True
                        self.proto = u'http://'
                        # we've read one extra char
                        self.readidx = self.readidx - 1
                        return self.STATUS_ABS_LOCATION_DOMAIN_START
                    # no? then it's not absolute uri
                    # do nothing and let this function go to the end
                    # with bad character handling
                    # back to the real read index
                    self.readidx = backup_index
            except IndexError:
                raise PrematureEndOfStream
                # back to the real read index
                self.readidx = backup_index

        if char == u'/':
            self.has_absolute_uri = False
            self.location = char
            return self.STATUS_LOCATION

        if self._is_forbidden(char, in_uri=True):
            self.setError(self.ERROR_BAD_CHARACTER)
            self._bad_request()
            # we should not continue, but let's assume this is a <bad> location
            self.location = u'<Err>'
            return self.STATUS_LOCATION

        # anything else? well not something expected
        self.location += u'<Err>'
        self.setError(self.ERROR_BAD_CHARACTER)
        return self.STATUS_LOCATION

    def step_abs_location_domain_start(self, char):
        'Start reading a domain name on an absolute uri.'
        # FIXME: detect http://user:pass@domain syntax

        if self._is_lf_or_crlf(char):
            # That's a strange http/0.9 query
            # requesting an 'http:' directory
            self.has_absolute_uri = False
            self.location = self.proto
            self.proto = u''
            self.location = u'<Err>'
            self.setError(self.ERROR_EMPTY_LOCATION)
            return self._http09()

        if u'/' == char:
            self.domain += u'<Err>'
            self.setError(self.ERROR_EMPTY_DOMAIN)
            self.location = char
            return self.STATUS_LOCATION

        if self._is_space(char, 'url_sep'):
            self.domain += u'<Err>'
            self.setError(self.ERROR_EMPTY_DOMAIN)
            self.location = u'<Err>'
            self.setError(self.ERROR_EMPTY_LOCATION)
            return self.STATUS_AFTER_URL_SEP

        # '-' and '.' are valid, but not as starting chars
        if u'-' == char:
            self.domain += u'<Err>'
            self.setError(self.ERROR_BAD_DOMAIN_CHARACTER)
            return self.STATUS_ABS_LOCATION_DOMAIN
        if u'.' == char:
            self.domain += u'<Err>'
            self.setError(self.ERROR_BAD_DOMAIN_CHARACTER)
            return self.STATUS_ABS_LOCATION_DOMAIN
        if self._is_forbidden(char, in_domain=True):
            self.setError(self.ERROR_BAD_DOMAIN_CHARACTER)
            self._bad_request()
            self.domain += u'<Err>'
            return self.STATUS_ABS_LOCATION_DOMAIN

        self.domain += char
        return self.STATUS_ABS_LOCATION_DOMAIN

    def step_abs_location_domain(self, char):
        'Reading a domain name on an absolute uri.'

        if self._is_lf_or_crlf(char):
            # That's a basic http/0.9 query
            return self._http09()

        if self._is_space(char, 'url_sep'):
            self.domain += u'<Err>'
            self.location = u'<Err>'
            self.setError(self.ERROR_EMPTY_LOCATION)
            return self.STATUS_AFTER_URL_SEP

        if u'/' == char:
            # FIXME: detect validity of domain with at least one dot
            self.location = char
            return self.STATUS_LOCATION

        if self._is_forbidden(char, in_domain=True):
            self.setError(self.ERROR_BAD_DOMAIN_CHARACTER)
            self._bad_request()
            self.domain += u'<Err>'
            return self.STATUS_ABS_LOCATION_DOMAIN

        self.domain += char
        return self.STATUS_ABS_LOCATION_DOMAIN

    def step_location(self, char):
        'we should already have the first "/" of the location.'
        if self._is_lf_or_crlf(char):
            # That's a basic http/0.9 query
            return self._http09()

        # TODO: for location and QS, detect percent encoded chars that should
        # not be percent encoded

        if self._is_space(char, 'url_sep'):
            return self.STATUS_AFTER_URL_SEP

        if self._is_forbidden(char, in_uri=True):
            self.setError(self.ERROR_BAD_CHARACTER)
            self._bad_request()
            self.location += u'<Err>'
            return self.STATUS_LOCATION

        if char == u'?':
            self.has_args = True
            return self.STATUS_QUERY_STRING

        self.location += char
        return self.STATUS_LOCATION

    def step_query_string(self, char):
        'After the "?" in uri.'
        if self._is_lf_or_crlf(char):
            # That's a basic http/0.9 query
            return self._http09()

        if self._is_space(char, 'url_sep'):
            return self.STATUS_AFTER_URL_SEP

        if self._is_forbidden(char, in_uri=True):
            self.setError(self.ERROR_BAD_CHARACTER)
            self._bad_request()
            self.query_string += u'<Err>'
            return self.STATUS_QUERY_STRING

        # note that with HTML5 you can have HTMl numerical ref in query string
        # like : "&#931;" or &#x03A3;

        self.query_string += char
        return self.STATUS_QUERY_STRING

    def step_after_url_sep(self, char):
        'We have at least one separator after the url.'
        if self._is_lf_or_crlf(char):
            # That's a basic http/0.9 query
            return self._http09()

        if self._is_space(char, 'url_sep'):
            # multiple separators
            return self.STATUS_AFTER_URL_SEP

        if self._is_forbidden(char):
            self.setError(self.ERROR_BAD_CHARACTER)
            self._bad_request()
            self.url_sep += u'<Err>'
            return self.STATUS_AFTER_URL_SEP

        if char == u'H':
            return self.STATUS_PROTO
        else:
            # mmmmmh, starting an unknown protocol? no, keep there.
            self.url_sep += u'<Err>'
            return self.STATUS_AFTER_URL_SEP

    def step_proto(self, char):
        'We already have the "H" character, need TTP/<digit>'
        if self._is_lf_or_crlf(char):
            # That's a basic http/0.9 query
            return self._http09()
        try:
            char2 = self.read_char()
            char3 = self.read_char()
            char4 = self.read_char()
            char5 = self.read_char()
            for achar in [char2, char3, char4, char5]:
                if self._is_forbidden(achar):
                    self.setError(self.ERROR_BAD_CHARACTER)
                    self._bad_request()
                    return self._http09()
        except IndexError:
            raise PrematureEndOfStream
        if u"T" == char and u"T" == char2 and u"P" == char3 and u"/" == char4:
            if char5.isdigit():
                self.version_major = char5
                return self.STATUS_AFTER_MAJOR
            else:
                self.setError(self.ERROR_BAD_VERSION)
                return self._http09()
        # Else it's bad
        return self._http09()

    def step_after_major(self, char):
        if self._is_lf_or_crlf(char):
            return self._http09()
        if '.' == char:
            self.version_sep = char
            return self.STATUS_AFTER_VERSION_SEP
        if self._is_forbidden(char):
            self.setError(self.ERROR_BAD_CHARACTER)
            self._bad_request()
            return self._http09()
        if char.isdigit():
            # yep, but you known you only have 1 digit allowed, so you should
            # not be there in fact. At least we won't record it, no int
            # overflow to handle for us.
            self.setError(self.ERROR_BAD_VERSION)
            return self.STATUS_AFTER_MAJOR
        # anything else is a bad response
        return self._http09()

    def step_after_version_sep(self, char):
        if self._is_lf_or_crlf(char):
            return self._http09()
        if self._is_forbidden(char):
            self.setError(self.ERROR_BAD_CHARACTER)
            self._bad_request()
            return self._http09()
        if char.isdigit():
            self.version_minor = int(char)
            return self.STATUS_AFTER_MINOR
        # anything else is a bad response
        return self._http09()

    def step_after_minor(self, char):
        if self._is_lf_or_crlf(char):
            return self.STATUS_END
        if self._is_forbidden(char):
            self.setError(self.ERROR_BAD_CHARACTER)
            self.suffix += '<Err>'
            self._bad_request()
            return self.STATUS_END
        # Space after protocol is NOT regular
        # if self._is_space(char, 'suffix'):
        #    return self.STATUS_AFTER_MINOR
        self.setError(self.ERROR_BAD_SUFFIX)
        self.suffix += char
        return self.STATUS_AFTER_MINOR

    def tokenize(self):
        status = self.STATUS_START
        automat = {self.STATUS_START: 'step_start',
                   self.STATUS_METHOD: 'step_method',
                   self.STATUS_AFTER_METHOD: 'step_after_method',
                   self.STATUS_AFTER_METHOD_SEP: 'step_after_method_sep',
                   self.STATUS_ABS_LOCATION_DOMAIN_START:
                       'step_abs_location_domain_start',
                   self.STATUS_ABS_LOCATION_DOMAIN: 'step_abs_location_domain',
                   self.STATUS_LOCATION: 'step_location',
                   self.STATUS_QUERY_STRING: 'step_query_string',
                   self.STATUS_AFTER_URL_SEP: 'step_after_url_sep',
                   self.STATUS_PROTO: 'step_proto',
                   self.STATUS_AFTER_MAJOR: 'step_after_major',
                   self.STATUS_AFTER_VERSION_SEP: 'step_after_version_sep',
                   self.STATUS_AFTER_MINOR: 'step_after_minor',
                   self.STATUS_WAITING_FOR_SPACE: 'step_wait_for_space',
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
            # print('char:<<<<{0}({1})>>>, step: {2}'.format(char,
            #                                               ord(char),
            #                                               automat[status]))
            status = getattr(self, automat[status])(char)


class FirstResponseHeader(Line):

    # STATUS_START = 0
    STATUS_PROTO = 1
    STATUS_AFTER_PROTO = 2
    STATUS_AFTER_MAJOR = 3
    STATUS_AFTER_VERSION_SEP = 4
    STATUS_AFTER_MINOR = 5
    STATUS_CODE_START = 6
    STATUS_CODE = 7
    # STATUS_READING_START = 13
    # STATUS_READING = 14
    # STATUS_AFTER_CR = 15
    # STATUS_END = 16

    ERROR_MAYBE_09 = 'Maybe an HTTP/0.9 response'
    ERROR_BAD_SPACE_PREFIX = 'Bad space prefix on response'
    ERROR_BAD_SPACE = 'Bad space on response'
    ERROR_INVALID_CODE = 'Invalid Response code'

    def __init__(self):
        super(FirstResponseHeader, self).__init__()
        self.code = 999
        self.version_major = 0
        self.version_sep = u''
        self.version_minor = 0

    def __str__(self):
        out = ''
        if self.error:
            if self.ERROR_MAYBE_09 in self.errors:
                out += "**(raw):{0}**".format(self.raw)
            if not not self.valid:
                out += "**INVALID FIRST LINE <"
            else:
                out += "**BAD FIRST LINE <"
            for error, value in Tools.iteritems(self.errors):
                out += " {0};".format(error)
            out += ">**\n"
        out += "HTTP/[{0}][{1}][{2}] [{3}] [{4}] [{5}]\n".format(
            self.version_major,
            self.version_sep,
            self.version_minor,
            self.code,
            self.value,
            self.eof)
        return out

    def _http09(self):
        self.setError(self.ERROR_MAYBE_09)
        self.version_major = 0
        self.version_sep = u'.'
        self.version_minor = 9
        return self.STATUS_END

    def step_start(self, char):
        if 'H' == char:
            return self.STATUS_PROTO
        if ' ' == char or '\t' == char:
            # spaces before name
            self.setError(self.ERROR_BAD_SPACE_PREFIX)
            return self.STATUS_START
        if '\t' == char:
            # spaces before name
            self.setError(self.ERROR_BAD_SPACE_PREFIX)
            return self.STATUS_START
        # anything else is a bad response
        return self._http09()

    def step_proto(self, char):
        # We already have 'H', we check for "TTP/"
        if 'T' == char:
            try:
                char2 = self.read_char()
                char3 = self.read_char()
                char4 = self.read_char()
            except IndexError:
                raise PrematureEndOfStream
            if "T" == char2 and "P" == char3 and "/" == char4:
                return self.STATUS_AFTER_PROTO
        # anything else is a bad response
        return self._http09()

    def step_after_proto(self, char):
        if char.isdigit():
            self.version_major = int(char)
            return self.STATUS_AFTER_MAJOR
        # anything else is a bad response
        return self._http09()

    def step_after_major(self, char):
        if '.' == char:
            self.version_sep = char
            return self.STATUS_AFTER_VERSION_SEP
        # anything else is a bad response
        return self._http09()

    def step_after_version_sep(self, char):
        if char.isdigit():
            self.version_minor = int(char)
            return self.STATUS_AFTER_MINOR
        # anything else is a bad response
        return self._http09()

    def step_after_minor(self, char):
        if ' ' == char:
            return self.STATUS_CODE_START
        if '\t' == char:
            self.setError(self.ERROR_BAD_SPACE)
            return self.STATUS_CODE_START
        # anything else is a bad response
        return self._http09()

    def step_read_code_start(self, char):
        if ' ' == char or '\t' == char:
            self.setError(self.ERROR_BAD_SPACE)
            return self.STATUS_CODE_START
        if char.isdigit():
            self.code = int(char)
            return self.STATUS_CODE
        # anything else is a bad response
        return self._http09()

    def step_read_code(self, char):
        if ' ' == char:
            return self.STATUS_READING_START
        if '\t' == char:
            self.setError(self.ERROR_BAD_SPACE)
            return self.STATUS_READING_START
        if '\r' == char:
            self.eof += u'[CR]'
            return self.STATUS_AFTER_CR
        if '\n' == char:
            self.setError(self.ERROR_LF_WITHOUT_CR, critical=False)
            self.eof += u'[LF]'
            return self.STATUS_END
        if char.isdigit():
            self.code = self.code * 10 + int(char)
            if self.code > 999:
                self.setError(self.ERROR_INVALID_CODE)
                # prevent long ints from overflowing
                self.code = 999
            return self.STATUS_CODE
        # anything else is a bad response
        return self._http09()

    def tokenize(self):
        status = self.STATUS_START
        automat = {self.STATUS_START: 'step_start',
                   self.STATUS_PROTO: 'step_proto',
                   self.STATUS_AFTER_PROTO: 'step_after_proto',
                   self.STATUS_AFTER_MAJOR: 'step_after_major',
                   self.STATUS_AFTER_VERSION_SEP: 'step_after_version_sep',
                   self.STATUS_AFTER_MINOR: 'step_after_minor',
                   self.STATUS_CODE_START: 'step_read_code_start',
                   self.STATUS_CODE: 'step_read_code',
                   self.STATUS_READING_START: 'step_reading_start',
                   self.STATUS_READING: 'step_read_value',
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
