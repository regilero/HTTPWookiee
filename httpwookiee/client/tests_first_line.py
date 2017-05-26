#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
from httpwookiee.config import ConfigFactory
from httpwookiee.core.tools import Tools
from httpwookiee.core.base import BaseTest
from httpwookiee.core.result import TextStatusResult
from httpwookiee.core.testrunner import WookieeTestRunner
from httpwookiee.core.testloader import WookieeTestLoader

import inspect
import sys
# ###################################### TESTS #########################


class AbstractFirstLineSeparators(BaseTest):
    """Test Bad Space separator at various places on first line of request.

    (see setUp() method for local config).

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

    From this we see that most prefix things should be read:
     - as METHOD elements (on the fist line), and generate 501 Not Implemented
     - as authorized for robustness (like CRCRCRLF before the message, but
       not several LF and not a single CR)
    And inside the first line we see that TAB, VTAB, FF or CR (or SP+FF,
    SP+HTAB,HTAB+SP, VTAB+SP, VTAB+FF, FF+VTAB+SP+VATB, etc.) could be
    considered as SP for robustness, but not as any other form of character.
    Problem of this 'could', is that official separator in first line is SP,
    not HTAB / SP. And this sentence about lenient parsing is true, who is
    right to consider htab as part of the location and sending an http/0.9
    response or to consider it as an SP and send an HTTP.1.1 response...
    Everybody is right from the RFC, but let's see how many different
    interpretation we have.

    For the location, whe ave absolute-URi or absolute-path, for the path part
    it's "absolute-path?query" with:
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
    warning2:  For consistency, percent-encoded octets in the ranges of ALPHA
    (%41-%5A and %61-%7A), DIGIT (%30-%39), hyphen (%2D), period (%2E),
    underscore (%5F), or tilde (%7E) should not be created by URI
    producers and, when found in a URI, should be decoded to their
    corresponding unreserved characters by URI normalizers

    From all this there's a lot of things for proxy tests, but at least we can
    see than non-ALPHA characters like BELL or FF are not valid part of the
    location (FF could be supported as SP, BELL or NULL certainly not).
    """

    separator = None
    valid_prefix = False
    valid_suffix = False
    valid_method_suffix = False
    valid_location = False
    valid_09_location = False

    def __init__(self, *args, **kwargs):
        super(AbstractFirstLineSeparators, self).__init__(*args, **kwargs)
        # for RP mode message analysis
        self.transmission_zone = Tools.ZONE_FIRST_LINE
        self.config = ConfigFactory.getConfig()

    def setUp(self):
        # allows children to alter main behavior of all tests
        self.setLocalSettings()
        super(AbstractFirstLineSeparators, self).setUp()

    def _prepare(self):
        "Default _prepare is a simple direct call."
        pass
        # self._prepare_simple_test()

    def setLocalSettings(self):
        self.separator = Tools.NULL
        self.valid_prefix = False
        self.valid_suffix = False
        self.valid_method_suffix = False
        self.valid_location = False
        self.valid_09_location = False
        # some characters (VTAB/FF/CR) are allowed by the RFC, but in the real
        # world, good parsers will reject the message
        self.can_be_rejected = False

    def test_3010_method_separator(self):
        "Test various characters after the METHOD."
        self.real_test = "{0}_{1}".format(
            inspect.stack()[0][3],
            Tools.show_chars(self.separator))
        self.req.set_method_sep(self.separator)

        # for RP mode:
        self.transmission_map = {
            'GET{0} '.format(
                self.separator): self.STATUS_TRANSMITTED_CRAP,
            'GET{0}'.format(
                self.separator): self.STATUS_TRANSMITTED_EXACT,
            'GET ': self.STATUS_TRANSMITTED_CRAP,
        }

        # FIXME: may be an err400 in http 0.9
        # GETXXXfoo HTTP/1.1
        #  method    url       noproto
        # sending err400 in 0.9 is not plainly wrong

        # playing with the method keyword we can expect err 400
        # for every bad character...
        self._add_default_status_map(valid=self.valid_method_suffix,
                                     always_allow_rejected=True)

        # Local adjustments
        self.status_map[self.STATUS_TRANSMITTED] = self.GRAVITY_MINOR
        self.status_map[self.STATUS_TRANSMITTED_EXACT] = self.GRAVITY_MINOR

        self._end_1st_line_query()

    def test_3011_location_separator(self):
        "After the query string, valid separator or a forbidden char?"
        self.real_test = "{0}_{1}".format(
            inspect.stack()[0][3],
            Tools.show_chars(self.separator))
        self.setGravity(BaseTest.GRAVITY_CRITICAL)
        self.req.set_location_sep(self.separator)

        # for RP mode:
        self.transmission_map = {
            '{0}HTTP/1.1 H'.format(
                self.separator): self.STATUS_TRANSMITTED,
            ' HTTP/1.1 H'.format(
                self.separator): self.STATUS_TRANSMITTED_CRAP,
            ' HTTP/1.0 H'.format(
                self.separator): self.STATUS_TRANSMITTED_CRAP,
            '{0} H'.format(self.separator):  self.STATUS_TRANSMITTED_CRAP,
            '{0}HTTP/1.1\r\n'.format(
                self.separator):  self.STATUS_TRANSMITTED_EXACT,
        }

        # RFC states that some of the separators, like FF, HTAB, VT, CR
        # are allowed, but ... well, .., we should allow rejection on most
        # of theses things (that should not be an error)
        self._add_default_status_map(
            http09_allowed=self.valid_09_location,
            valid=self.valid_location,
            always_allow_rejected=self.can_be_rejected)

        # Local adjustments
        if self.separator in [Tools.BEL, Tools.BS]:
            # better to reject, but this transmission is done the right
            # way if you do not consider theses chars as spaces
            self.status_map[self.STATUS_TRANSMITTED] = self.GRAVITY_MINOR
            self.status_map[self.STATUS_TRANSMITTED_EXACT] = self.GRAVITY_MINOR
        else:
            self.status_map[self.STATUS_TRANSMITTED] = self.GRAVITY_WARNING
            self.status_map[
                self.STATUS_TRANSMITTED_EXACT] = self.GRAVITY_WARNING

        self._end_1st_line_query(http09_allowed=self.valid_09_location)

    def test_3012_location_separator_09_and_extra_proto(self):
        "After the query, valid separator or a forbidden char? Proto repeated."
        self.real_test = "{0}_{1}".format(
            inspect.stack()[0][3],
            Tools.show_chars(self.separator))
        self.setGravity(BaseTest.GRAVITY_MINOR)
        self.req.add_argument('last', 'marker')
        self.req.set_location_sep(self.separator)
        self.req.set_http_version(major=0, minor=9, force=True)
        self.req.set_first_line_suffix(u' HTTP/1.1')

        # for RP mode:
        self.transmission_map = {
            '{0}HTTP/0.9 H'.format(
                self.separator): self.STATUS_TRANSMITTED_EXACT,
            ' HTTP/O.9 H'.format(
                self.separator): self.STATUS_TRANSMITTED_CRAP,
            ' HTTP/1.0 H'.format(
                self.separator): self.STATUS_TRANSMITTED_CRAP,
            'last=marker HTTP/1.0\r\n'.format(
                self.separator):  self.STATUS_TRANSMITTED_CRAP,
            'last=marker HTTP/1.1\r\n'.format(
                self.separator):  self.STATUS_TRANSMITTED_CRAP,
        }

        self._add_default_status_map(
            valid=self.valid_location)

        # Local adjustments
        if self.separator in [Tools.BEL, Tools.BS]:
            # better to reject, but this transmission is done the right
            # way if you do not consider theses chars as spaces
            self.status_map[self.STATUS_TRANSMITTED] = self.GRAVITY_MINOR

        # local changes
        self.status_map[self.STATUS_TRANSMITTED_EXACT] = self.GRAVITY_WARNING
        self.status_map[self.STATUS_09DOWNGRADE] = self.GRAVITY_CRITICAL
        self.status_map[self.STATUS_09OK] = self.GRAVITY_CRITICAL

        self._end_1st_line_query()

    def test_3013_line_prefix(self):
        "Some characters before the query..."
        self.real_test = "{0}_{1}".format(
            inspect.stack()[0][3],
            Tools.show_chars(self.separator))
        self.setGravity(BaseTest.GRAVITY_MINOR)
        self.req.set_first_line_prefix(self.separator)

        # for RP mode:
        self.transmission_map = {
            '{0}GET'.format(
                self.separator): self.STATUS_TRANSMITTED_EXACT,
            ' GET': self.STATUS_TRANSMITTED_CRAP,
        }

        self._add_default_status_map(
            valid=self.valid_prefix,
            always_allow_rejected=self.can_be_rejected
        )

        # local changes
        self.status_map[self.STATUS_TRANSMITTED_EXACT] = self.GRAVITY_MINOR
        self.status_map[self.STATUS_TRANSMITTED] = self.GRAVITY_MINOR

        self._end_1st_line_query()

    def test_3014_line_suffix(self):
        "Let's add some garbage after the protocol."
        self.real_test = "{0}_{1}".format(
            inspect.stack()[0][3],
            Tools.show_chars(self.separator))
        self.setGravity(BaseTest.GRAVITY_WARNING)
        self.req.set_first_line_suffix(self.separator)

        # for RP mode:
        self.transmission_map = {
            ' HTTP/1.0{0}\r\n'.format(
                self.separator): self.STATUS_TRANSMITTED_EXACT,
            ' HTTP/1.1{0}\r\n'.format(
                self.separator): self.STATUS_TRANSMITTED_EXACT,
            ' HTTP/1.1 \r\n': self.STATUS_TRANSMITTED_CRAP,
        }

        self._add_default_status_map(
            valid=False)
        self._end_1st_line_query(http09_allowed=False)

    def test_3015_line_suffix_with_char(self):
        "Let's add some garbage after the protocol. With a letter after."
        self.real_test = "{0}_{1}".format(
            inspect.stack()[0][3],
            Tools.show_chars(self.separator))
        self.setGravity(BaseTest.GRAVITY_WARNING)
        self.req.set_first_line_suffix(self.separator + u'X')

        # for RP mode:
        self.transmission_map = {
            ' HTTP/1.0{0}X\r\n'.format(
                self.separator): self.STATUS_TRANSMITTED_EXACT,
            ' HTTP/1.1{0}X\r\n'.format(
                self.separator): self.STATUS_TRANSMITTED_EXACT,
            'HTTP/1.1{0}X H'.format(
                self.separator): self.STATUS_TRANSMITTED_CRAP,
            'HTTP/1.1 X\r\n': self.STATUS_TRANSMITTED_CRAP,
        }

        self._add_default_status_map(
            valid=False)
        self._end_1st_line_query(http09_allowed=False)

    def test_3016_line_suffix_with_char_H(self):
        "Nginx, for example, likes the H character"
        self.real_test = "{0}_{1}".format(
            inspect.stack()[0][3],
            Tools.show_chars(self.separator))
        self.setGravity(BaseTest.GRAVITY_WARNING)
        self.req.set_first_line_suffix(self.separator + u'H')

        # for RP mode:
        self.transmission_map = {
            ' HTTP/1.0{0}H\r\n'.format(
                self.separator): self.STATUS_TRANSMITTED_EXACT,
            ' HTTP/1.1{0}H\r\n'.format(
                self.separator): self.STATUS_TRANSMITTED_EXACT,
            'HTTP/1.1{0}H H'.format(
                self.separator): self.STATUS_TRANSMITTED_CRAP,
            'HTTP/1.1 H\r\n': self.STATUS_TRANSMITTED_CRAP,
        }

        self._add_default_status_map(
            valid=False)
        self._end_1st_line_query(http09_allowed=False)

    def test_3017_line_suffix_with_double_HTTP11(self):
        "Ending first line with two times the protocol"
        self.real_test = "{0}_{1}".format(
            inspect.stack()[0][3],
            Tools.show_chars(self.separator))
        self.req.set_first_line_suffix(self.separator + u'HTTP/1.1')

        # for RP mode:
        self.transmission_map = {
            'HTTP/1.1{0}HTTP/1.1\r\n'.format(
                self.separator): self.STATUS_TRANSMITTED_EXACT,
            'HTTP/1.0{0}HTTP/1.0\r\n'.format(
                self.separator): self.STATUS_TRANSMITTED_CRAP,
            'HTTP/1.0{0}HTTP/1.1\r\n'.format(
                self.separator): self.STATUS_TRANSMITTED_CRAP,
            'HTTP/1.1{0}HTTP/1.0\r\n'.format(
                self.separator): self.STATUS_TRANSMITTED_CRAP,
        }

        self._add_default_status_map(
            valid=False)
        self._end_1st_line_query(http09_allowed=False)

    def test_3018_location_separator_and_extra_proto(self):
        "After the query, valid separator or a forbidden char? Proto repeated."
        self.real_test = "{0}_{1}".format(
            inspect.stack()[0][3],
            Tools.show_chars(self.separator))
        self.setGravity(BaseTest.GRAVITY_MINOR)
        self.req.add_argument('last', 'marker')
        self.req.set_location_sep(self.separator)
        self.req.set_http_version(major=1, minor=1, force=True)
        self.req.set_first_line_suffix(u' HTTP/1.1')

        # for RP mode:
        self.transmission_map = {
            '{0}HTTP/1.1 H'.format(
                self.separator): self.STATUS_TRANSMITTED_EXACT,
            ' HTTP/1.1 H'.format(
                self.separator): self.STATUS_TRANSMITTED_CRAP,
            ' HTTP/1.0 H'.format(
                self.separator): self.STATUS_TRANSMITTED_CRAP,
            'last=marker HTTP/1.0\r\n'.format(
                self.separator):  self.STATUS_TRANSMITTED_CRAP,
            'last=marker HTTP/1.1\r\n'.format(
                self.separator):  self.STATUS_TRANSMITTED_CRAP,
        }

        self._add_default_status_map(
            valid=self.valid_location)

        # Local adjustments
        if self.separator in [Tools.BEL, Tools.BS]:
            # better to reject, but this transmission is done the right
            # way if you do not consider theses chars as spaces
            self.status_map[self.STATUS_TRANSMITTED] = self.GRAVITY_MINOR

        # local changes
        self.status_map[self.STATUS_TRANSMITTED_EXACT] = self.GRAVITY_MINOR
        self.status_map[self.STATUS_09DOWNGRADE] = self.GRAVITY_CRITICAL
        self.status_map[self.STATUS_09OK] = self.GRAVITY_CRITICAL

        self._end_1st_line_query()


class TestNullFirstLineSeparators(AbstractFirstLineSeparators):
    """Test Bad Space separator at various places on first line of request.

    This overriden implementation uses the NULL \x00 character."""

    def setLocalSettings(self):
        self.separator = Tools.NULL
        self.valid_prefix = False
        self.valid_suffix = False
        self.valid_method_suffix = False
        self.valid_location = False
        self.valid_09_location = False
        self.can_be_rejected = True


class TestFormFeedFirstLineSpaceSeparators(AbstractFirstLineSeparators):
    """Test Bad Space separator at various places on first line of request.

    This overriden implementation uses the FormFeed character."""

    def setLocalSettings(self):
        self.separator = Tools.FF
        self.valid_prefix = False
        self.valid_suffix = False
        self.valid_method_suffix = True
        self.valid_location = False
        self.valid_09_location = False
        self.can_be_rejected = True


class TestVerticalTabFirstLineSpaceSeparators(AbstractFirstLineSeparators):
    """Test Bad Space separator at various places on first line of request.

    This overriden implementation uses the Vertical tab character."""

    def setLocalSettings(self):
        self.separator = Tools.VTAB
        self.valid_prefix = False
        self.valid_suffix = False
        self.valid_method_suffix = True
        self.valid_location = False
        self.valid_09_location = False
        self.can_be_rejected = True


class TestBackSpaceFirstLineSpaceSeparators(AbstractFirstLineSeparators):
    """Test Bad Space separator at various places on first line of request.

    This overriden implementation uses the BackSpace character."""

    def setLocalSettings(self):
        self.separator = Tools.BS
        self.valid_prefix = False
        self.valid_suffix = False
        self.valid_method_suffix = False
        self.valid_location = False
        self.valid_09_location = True
        self.can_be_rejected = True


class TestBellFirstLineSpaceSeparators(AbstractFirstLineSeparators):
    """Test Bad Space separator at various places on first line of request.

    This overriden implementation uses the Bell character."""

    def setLocalSettings(self):
        self.separator = Tools.BEL
        self.valid_prefix = False
        self.valid_suffix = False
        self.valid_method_suffix = False
        self.valid_location = False
        self.valid_09_location = True
        self.can_be_rejected = True


class TestTabFirstLineSpaceSeparators(AbstractFirstLineSeparators):
    """Test Bad Space separator at various places on first line of request.

    This overriden implementation uses the Tab character."""

    def setLocalSettings(self):
        self.separator = Tools.TAB
        self.valid_prefix = False
        self.valid_suffix = False
        self.valid_method_suffix = True
        self.valid_location = False
        self.valid_09_location = False
        # we keep TAB as valid seperator, maybe we should not...
        self.can_be_rejected = False


class TestCRSpaceFirstLineSpaceSeparators(AbstractFirstLineSeparators):
    """Test Bad Space separator at various places on first line of request.

    This overriden implementation uses the CR+SP characters."""

    def setLocalSettings(self):
        self.separator = "{0}{1}".format(Tools.CR, Tools.SP)
        self.valid_prefix = False
        self.valid_suffix = False
        self.valid_method_suffix = False
        self.valid_location = False
        self.valid_09_location = False
        self.can_be_rejected = True


class AbstractCarriageReturnFirstLineSpaceSeparators(
        AbstractFirstLineSeparators):

    def test_3020_multiple_cr_line_prefix(self):
        # TODO: this is maybe allowed, but we do not have any LF here...
        self.separator = u'\r\r\r\r\r'
        self.real_test = "{0}_{1}".format(
            inspect.stack()[0][3],
            Tools.show_chars(self.separator))
        self.setGravity(BaseTest.GRAVITY_MINOR)
        self.req.set_first_line_prefix(self.separator)
        # for RP mode:
        self.transmission_map = {
            '{0}GET'.format(
                self.separator): self.STATUS_TRANSMITTED_EXACT,
            ' GET': self.STATUS_TRANSMITTED_CRAP,
        }
        self._add_default_status_map(
            valid=False,
            always_allow_rejected=True)
        self._end_1st_line_query(http09_allowed=False)

    def test_3021_crlf_line_prefix(self):
        self.separator = u'\r\n'
        self.real_test = "{0}_{1}".format(
            inspect.stack()[0][3],
            Tools.show_chars(self.separator))
        self.setGravity(BaseTest.GRAVITY_MINOR)
        self.req.set_first_line_prefix(self.separator)
        # for RP mode:
        self.transmission_map = {
            '{0}GET'.format(
                self.separator): self.STATUS_TRANSMITTED_EXACT,
            ' GET': self.STATUS_TRANSMITTED_CRAP,
        }
        self._add_default_status_map(
            valid=True,
            always_allow_rejected=False)  # this is allowed in RFC
        self._end_1st_line_query(http09_allowed=False)

    def test_3022_multiple_crlf_line_prefix(self):
        self.separator = u'\r\n\r\n\r\n\r\n\r\n'
        self.real_test = "{0}_{1}".format(
            inspect.stack()[0][3],
            Tools.show_chars(self.separator))
        self.setGravity(BaseTest.GRAVITY_MINOR)
        self.req.set_first_line_prefix(self.separator)
        # for RP mode:
        self.transmission_map = {
            '{0}GET'.format(
                self.separator): self.STATUS_TRANSMITTED_EXACT,
            ' GET': self.STATUS_TRANSMITTED_CRAP,
        }
        self._add_default_status_map(
            valid=True,
            always_allow_rejected=True)
        self._end_1st_line_query(http09_allowed=False)

    def test_3023_crcrcrlf_line_prefix(self):
        self.separator = u'\r\r\r\r\r\n'
        self.real_test = "{0}_{1}".format(
            inspect.stack()[0][3],
            Tools.show_chars(self.separator))
        self.setGravity(BaseTest.GRAVITY_MINOR)
        self.req.set_first_line_prefix(self.separator)
        # for RP mode:
        self.transmission_map = {
            '{0}GET'.format(
                self.separator): self.STATUS_TRANSMITTED_EXACT,
            ' GET': self.STATUS_TRANSMITTED_CRAP,
        }
        self._add_default_status_map(
            valid=True,
            always_allow_rejected=True)
        self._end_1st_line_query(http09_allowed=False)


class TestCarriageReturnFirstLineSpaceSeparators(
        AbstractCarriageReturnFirstLineSpaceSeparators):
    """Test Bad Space separator at various places on first line of request.

    This overriden implementation uses the CR character."""

    def setLocalSettings(self):
        self.separator = Tools.CR
        self.valid_prefix = True
        self.valid_suffix = False
        self.valid_method_suffix = False
        self.valid_location = False
        self.valid_09_location = False
        self.can_be_rejected = True


class TestSpaceFirstLineSeparators(BaseTest):
    """Test Bad Space separator at various places on first line of request.

    This is a reduced version of tests that can be found on
    AbstractFirstLineSeparators variants. As space is a good separator on most
    places.
    """

    separator = None

    def __init__(self, *args, **kwargs):
        super(TestSpaceFirstLineSeparators, self).__init__(*args, **kwargs)
        self.config = ConfigFactory.getConfig()

    def setUp(self):
        self.separator = Tools.SP
        super(TestSpaceFirstLineSeparators, self).setUp()

    def test_double_space_method_separator(self):
        self.real_test = "{0}".format(inspect.stack()[0][3])
        self.req.set_method_sep(u'  ')
        self._end_regular_query()

    def test_double_space_location_separator(self):
        self.real_test = "{0}".format(inspect.stack()[0][3])
        self.req.set_location_sep(u'  ')
        self._end_regular_query()


class AbstractTestHTTPVersion(BaseTest):
    """Test Bad Digits variations on requested HTTP version."""

    def test_3040_http_65536_9(self):
        "Integer overflow attempt on protocol version."
        self.real_test = "{0}".format(inspect.stack()[0][3])
        self.req.set_major_version(65536)
        self.req.set_minor_version(9)
        self.req.add_argument('last', 'marker')
        # for RP mode:
        self.transmission_map = {
            ' HTTP/65536.9\r\n': self.STATUS_TRANSMITTED_EXACT,
            'HTTP/65536.9 H': self.STATUS_TRANSMITTED_CRAP,
            'last=marker\r\n': self.STATUS_TRANSMITTED_CRAP,
        }
        self._add_default_status_map(valid=False)
        # local changes
        self.status_map[self.STATUS_TRANSMITTED] = self.GRAVITY_CRITICAL
        self.status_map[self.STATUS_09OK] = self.GRAVITY_CRITICAL
        self.status_map[self.STATUS_09DOWNGRADE] = self.GRAVITY_CRITICAL
        self._end_1st_line_query(http09_allowed=False)

    def test_3041_http_0_9_explicit(self):
        "HTTP/0.9 does not exists. Should be an empty protocol."
        self.real_test = "{0}".format(inspect.stack()[0][3])
        self.req.set_major_version(0)
        self.req.set_minor_version(9)
        self.req.add_argument('last', 'marker')
        # for RP mode:
        self.transmission_map = {
            ' HTTP/0.9\r\n': self.STATUS_TRANSMITTED_EXACT,
            'HTTP/0.9 H': self.STATUS_TRANSMITTED_CRAP,
            'last=marker\r\n': self.STATUS_TRANSMITTED_CRAP,
        }
        self._add_default_status_map(valid=False)
        # local changes
        self.status_map[self.STATUS_TRANSMITTED] = self.GRAVITY_CRITICAL
        self.status_map[self.STATUS_09OK] = self.GRAVITY_CRITICAL
        self.status_map[self.STATUS_09DOWNGRADE] = self.GRAVITY_CRITICAL
        self._end_1st_line_query(http09_allowed=False)

    def test_3042_http_0_8(self):
        "HTTP/0.8 does not exists."
        self.real_test = "{0}".format(inspect.stack()[0][3])
        self.req.set_major_version(0)
        self.req.set_minor_version(8)
        self.req.add_argument('last', 'marker')
        # for RP mode:
        self.transmission_map = {
            ' HTTP/0.8\r\n': self.STATUS_TRANSMITTED_EXACT,
            'HTTP/0.8 H': self.STATUS_TRANSMITTED_CRAP,
            'last=marker\r\n': self.STATUS_TRANSMITTED_CRAP,
        }
        self._add_default_status_map(valid=False)
        # local changes
        self.status_map[self.STATUS_TRANSMITTED] = self.GRAVITY_CRITICAL
        self.status_map[self.STATUS_09OK] = self.GRAVITY_CRITICAL
        self.status_map[self.STATUS_09DOWNGRADE] = self.GRAVITY_CRITICAL
        self._end_1st_line_query(http09_allowed=False)

    def test_3043_http_minus_1_0(self):
        "HTTP/-1.0 does not exists."
        self.real_test = "{0}".format(inspect.stack()[0][3])
        self.req.set_major_version(-1)
        self.req.set_minor_version(0)
        self.req.add_argument('last', 'marker')
        # for RP mode:
        self.transmission_map = {
            ' HTTP/-1.0\r\n': self.STATUS_TRANSMITTED_EXACT,
            'HTTP/-1.0 H': self.STATUS_TRANSMITTED_CRAP,
            'HTTP/-1.1': self.STATUS_TRANSMITTED_CRAP,
            'last=marker\r\n': self.STATUS_TRANSMITTED_CRAP,
        }
        self._add_default_status_map(valid=False)
        # local changes
        self.status_map[self.STATUS_TRANSMITTED] = self.GRAVITY_CRITICAL
        self.status_map[self.STATUS_09OK] = self.GRAVITY_CRITICAL
        self.status_map[self.STATUS_09DOWNGRADE] = self.GRAVITY_CRITICAL
        self._end_1st_line_query(http09_allowed=False)

    def test_3044_http_1_nodigit(self):
        "HTTP/1.x1 does not exists."
        self.real_test = "{0}".format(inspect.stack()[0][3])
        self.req.set_major_version(1)
        self.req.set_minor_version('x1')
        self.req.add_argument('last', 'marker')
        # for RP mode:
        self.transmission_map = {
            ' HTTP/1.x1\r\n': self.STATUS_TRANSMITTED_EXACT,
            'HTTP/1.0 H': self.STATUS_TRANSMITTED_CRAP,
            'HTTP/1.1 H': self.STATUS_TRANSMITTED_CRAP,
            'HTTP/1.x1 H': self.STATUS_TRANSMITTED_CRAP,
            'last=marker\r\n': self.STATUS_TRANSMITTED_CRAP,
        }
        self._add_default_status_map(valid=False)
        # local changes
        self.status_map[self.STATUS_TRANSMITTED] = self.GRAVITY_CRITICAL
        self.status_map[self.STATUS_09OK] = self.GRAVITY_CRITICAL
        self.status_map[self.STATUS_09DOWNGRADE] = self.GRAVITY_CRITICAL
        self._end_1st_line_query(http09_allowed=False)

    def test_3045_http_version_too_much_digits(self):
        "New RFC is quite strict, DIGIT.DIGIT only, in fact."
        self.real_test = "{0}".format(inspect.stack()[0][3])
        self.req.set_major_version(11)
        self.req.set_minor_version(11)
        self.req.add_argument('last', 'marker')
        # for RP mode:
        self.transmission_map = {
            ' HTTP/11.11\r\n': self.STATUS_TRANSMITTED_EXACT,
            'HTTP/11.0': self.STATUS_TRANSMITTED_CRAP,
            '.11 H': self.STATUS_TRANSMITTED_CRAP,
            'last=marker\r\n': self.STATUS_TRANSMITTED_CRAP,
        }
        self._add_default_status_map(valid=False)
        # local changes
        self.status_map[self.STATUS_TRANSMITTED] = self.GRAVITY_CRITICAL
        self.status_map[self.STATUS_09OK] = self.GRAVITY_CRITICAL
        self.status_map[self.STATUS_09DOWNGRADE] = self.GRAVITY_CRITICAL
        self._end_1st_line_query(http09_allowed=False)


class TestHTTPVersion(AbstractTestHTTPVersion):
    pass


if __name__ == '__main__':
    tl = WookieeTestLoader(debug=True)
    testSuite = tl.loadTestsFromModule(sys.modules[__name__])
    # without stream forced here python 2.7 is failing
    WookieeTestRunner(resultclass=TextStatusResult,
                      verbosity=2,
                      buffer=True,
                      stream=sys.stderr).run(testSuite)
