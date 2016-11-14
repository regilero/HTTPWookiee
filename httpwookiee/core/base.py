#!/usr/bin/env python
# -*- coding: utf-8 -*-
from httpwookiee.config import ConfigFactory, Register
from httpwookiee.http.client import Client
from httpwookiee.http.parser.response import Response
from httpwookiee.core.tools import Tools, outmsg
from httpwookiee.http.request import Request
from unittest.util import strclass
import unittest


class BaseTest(unittest.TestCase):

    GRAVITY_UNKNOWN = 0
    GRAVITY_MINOR = 1
    GRAVITY_WARNING = 2
    GRAVITY_CRITICAL = 3
    GRAVITY_OK = 4
    gravity_format = {
        GRAVITY_UNKNOWN: u'Unknown',
        GRAVITY_MINOR: u'Minor',
        GRAVITY_WARNING: u'Warning',
        GRAVITY_CRITICAL: u'Critical',
        GRAVITY_OK: u'Ok',
    }

    STATUS_UNKNOWN = 'Unknown'
    STATUS_ACCEPTED = 'Accepted'
    STATUS_REJECTED = 'Rejected'
    STATUS_ERR400 = 'Err400'
    STATUS_ERR401 = 'Err401'
    STATUS_ERR403 = 'Err403'
    STATUS_ERR404 = 'Err404'
    STATUS_ERR405 = 'Err405'
    STATUS_ERR411 = 'Err411'
    STATUS_ERR413 = 'Err413'
    STATUS_ERR414 = 'Err414'
    STATUS_ERR500 = 'Err500'
    STATUS_501_NOT_IMPLEMENTED = '501NotImpl.'
    STATUS_5032 = '502or5023'
    STATUS_505_NOT_SUPPORTED = '505'
    STATUS_SPLITTED = 'Splitted'
    STATUS_09DOWNGRADE = 'Downgrade09'
    STATUS_09OK = 'Regular09'
    STATUS_RED_301 = 'Redir301'
    STATUS_RED_302 = 'Redir302'
    STATUS_TRANSMITTED = 'Transmit'
    STATUS_TRANSMITTED_EXACT = 'Transmit+'
    STATUS_TRANSMITTED_CRAP = 'Transmit^!$#^'
    STATUS_REMOVED = 'Removed'
    STATUS_WOOKIEE = 'Wookiee'
    status_format = {
        STATUS_REJECTED: {'long': u'rejected', 'short': u'r'},
        STATUS_ERR400: {'long': u'-err400-', 'short': u'4'},
        STATUS_ERR401: {'long': u'-err401-', 'short': u'4'},
        STATUS_ERR403: {'long': u'-err403-', 'short': u'4'},
        STATUS_ERR404: {'long': u'-err404-', 'short': u'4'},
        STATUS_ERR405: {'long': u'-err405-', 'short': u'4'},
        STATUS_ERR411: {'long': u'-err411-', 'short': u'4'},
        STATUS_ERR413: {'long': u'-err413-', 'short': u'4'},
        STATUS_ERR414: {'long': u'-err414-', 'short': u'4'},
        STATUS_ERR500: {'long': u'-err500-', 'short': u'5'},
        STATUS_RED_301: {'long': u'-red301-', 'short': u'3'},
        STATUS_RED_302: {'long': u'-red302-', 'short': u'3'},
        STATUS_501_NOT_IMPLEMENTED: {'long': u'-501-ni', 'short': u'n'},
        STATUS_5032: {'long': u'-502-03', 'short': u'x'},
        STATUS_505_NOT_SUPPORTED: {'long': u'-505-ns', 'short': u'5'},
        STATUS_ACCEPTED: {'long': u'accepted', 'short': u'a'},
        STATUS_UNKNOWN: {'long': u'-unknown', 'short': u'u'},
        STATUS_SPLITTED: {'long': u'splitted', 'short': u's'},
        STATUS_09DOWNGRADE: {'long': u'-down-09', 'short': u'D'},
        STATUS_09OK: {'long': u'regular9', 'short': u'9'},
        STATUS_TRANSMITTED: {'long': u'transmit', 'short': u't'},
        STATUS_TRANSMITTED_EXACT: {'long': u'transmit', 'short': u'T'},
        STATUS_TRANSMITTED_CRAP: {'long': u'transmit', 'short': u'Z'},
        STATUS_REMOVED: {'long': u'removed-', 'short': u'R'},
        STATUS_WOOKIEE: {'long': u'wookiee-', 'short': u'W'},
    }

    SEND_MODE_UNIQUE = 0
    SEND_MODE_PIPE = 1

    use_backend_location = False
    req = None
    req1 = None
    req2 = None
    send_mode = None
    reverse_proxy_mode = False

    def __init__(self, methodName="runTest"):
        self.config = ConfigFactory.getConfig()
        self.status = self.STATUS_UNKNOWN
        self.real_test = None
        self.gravity = self.GRAVITY_UNKNOWN
        self.status_map = None
        self.transmission_zone = None
        self.transmission_map = None
        if self.send_mode is None:
            self.send_mode = self.SEND_MODE_UNIQUE
        self.use_backend_location = False
        self.reverse_proxy_mode = False
        super(BaseTest, self).__init__(methodName)
        self.addCleanup(self.CustomCleanup)

    def __str__(self):
        return "[{0}] ({1})".format(self._testMethodName,
                                    strclass(self.__class__))

    def setUp(self):
        super(BaseTest, self).setUp()
        if (not self.reverse_proxy_mode
                and self.config.getboolean('REVERSEPROXY_TESTS_ONLY')):
            self.skipTest('Only Reverse Proxy (server) tests are '
                          'allowed by config')
        self._prepare_queries()

    def setStatus(self, status):
        if status not in self.status_format.keys():
            raise ValueError('Unexpected Test status {0}'.format(status))
        self.status = status

    def getStatus(self, format=None):
        if format is None:
            return self.status
        else:
            try:
                return self.status_format[self.status][format]
            except KeyError:
                return ''

    def getGravity(self, human=False):
        if not human:
            return self.gravity
        else:
            return self.gravity_format[self.gravity]

    def setGravity(self, gravity):
        if gravity not in self.gravity_format.keys():
            raise ValueError('Unexpected Test gravity {0}'.format(gravity))
        self.gravity = gravity

    def CustomCleanup(self):
        pass
        # print('CUSTOmCleanup')

    def _prepare_queries(self):
        if self.send_mode == self.SEND_MODE_UNIQUE:
            self._prepare_simple_test()
        elif self.send_mode == self.SEND_MODE_PIPE:
            self._prepare_pipe_test()
        else:
            raise ValueError('Unknown send mode for test HTTP queries.')

    def get_default_location(self, with_prefix=None):
        if with_prefix is None:
            with_prefix = self.use_backend_location
        if with_prefix:
            return "{0}{1}".format(
                self.config.get('BACKEND_LOCATION_PREFIX'),
                self.config.get('SERVER_DEFAULT_LOCATION'))
        else:
            return self.config.get('SERVER_DEFAULT_LOCATION')

    def get_non_default_location(self, with_prefix=None):
        if with_prefix is None:
            with_prefix = self.use_backend_location
        if with_prefix:
            return "{0}{1}".format(
                self.config.get('BACKEND_LOCATION_PREFIX'),
                self.config.get('SERVER_NON_DEFAULT_LOCATION'))
        else:
            return self.config.get('SERVER_NON_DEFAULT_LOCATION')

    def get_wookiee_location(self, with_prefix=None):
        if with_prefix is None:
            with_prefix = self.use_backend_location
        if with_prefix:
            return "{0}{1}".format(
                self.config.get('BACKEND_LOCATION_PREFIX'),
                self.config.get('BACKEND_WOOKIEE_LOCATION'))
        else:
            return self.config.get('BACKEND_WOOKIEE_LOCATION')

    def _get_valid_chunk_method(self):
        if not Register.hasFlag('post_chunk_{0}'.format(
                self.reverse_proxy_mode)):
            if not Register.hasFlag('get_chunk_{0}'.format(
                    self.reverse_proxy_mode)):
                self.skipTest("Preflight invalidated all chunk queries.")
            return 'GET'
        else:
            return 'POST'

    def _prepare_simple_test(self):
        outmsg("={0}=".format(self.real_test))
        self.req = Request(id(self))
        location = self.get_default_location()
        self.req.set_location(location, random=True)

    def _prepare_pipe_test(self,
                           method1='GET',
                           method2='GET'):
        outmsg("={0}=".format(self.real_test))
        if Register.flags['keepalive'] is False:
            self.skipTest("No keepalive support.")
        if Register.flags['pipelining'] is False:
            self.skipTest("No pipelining support.")
        self.send_mode = self.SEND_MODE_PIPE
        location = self.get_default_location(
            with_prefix=self.use_backend_location)
        self.req1 = Request(id(self))
        self.req1.add_header('Connection', 'keep-alive')
        self.req1.set_location(location, random=True)
        self.req1.set_method(method1)
        self.req2 = Request(id(self))
        self.req2.set_location(location, random=True)
        self.req2.set_method(method2)

    def _hook_while_sending(self):
        pass

    def send_queries(self):
        responses = None
        if self.send_mode == self.SEND_MODE_UNIQUE:
            with Client() as csock:
                csock.send(self.req)
                responses = csock.read_all()
                self._hook_while_sending()
        elif self.send_mode == self.SEND_MODE_PIPE:
            with Client() as csock:
                # csock.send(u'{0}{1}'.format(self.req1, self.req2))
                csock.send(self.req1)
                csock.send(self.req2)
                responses = csock.read_all()
                self._hook_while_sending()
        else:
            raise ValueError('Unknown send mode for test HTTP queries.')
        outmsg(str(responses))
        return responses

    def _end_regular_query(self,
                           responses=None,
                           http09_allowed=False,
                           can_be_rejected=False,
                           expected_number=1,
                           status_map=None):
        self._end_almost_regular_query(responses,
                                       http09_allowed=http09_allowed,
                                       expected_number=expected_number,
                                       regular_expected=True,
                                       status_map=status_map)
        allowed = [self.STATUS_ACCEPTED]
        if can_be_rejected:
            # sometimes it's 'regular', but not really
            allowed.append(self.STATUS_REJECTED)
            allowed.append(self.STATUS_ERR400)
            allowed.append(self.STATUS_ERR413)
            allowed.append(self.STATUS_ERR411)
            allowed.append(self.STATUS_501_NOT_IMPLEMENTED)
            allowed.append(self.STATUS_505_NOT_SUPPORTED)
            # rfc 7230 allows 301 on bad request line
            allowed.append(self.STATUS_RED_301)
        if http09_allowed:
            allowed.append(self.STATUS_09OK)
        self.assertIn(self.status,
                      allowed,
                      'Bad response status {0} for regular query'.format(
                          self.status))

    def _end_almost_regular_query(self,
                                  responses=None,
                                  http09_allowed=False,
                                  regular_expected=False,
                                  expected_number=1,
                                  status_map=None):
        "same as _end_regular_query but without the status assertions."
        if responses is None:
            responses = self.send_queries()
        self.analysis(responses,
                      expected_number=expected_number,
                      http09_allowed=http09_allowed,
                      regular_expected=regular_expected)
        self.adjust_status_by_map(status_map)

    def _end_expected_error(self,
                            responses=None,
                            expected_number=1,
                            regular_expected=False,
                            http09_allowed=False,
                            status_map=None):
        "Bad queries test end management."
        if responses is None:
            responses = self.send_queries()
        self.analysis(responses,
                      expected_number=expected_number,
                      http09_allowed=http09_allowed,
                      regular_expected=regular_expected)
        self.adjust_status_by_map(status_map)

        self.assertNotEqual(self.status,
                            self.STATUS_WOOKIEE,
                            'Wookiee response detected,'
                            + ' this should never happen.')
        self.assertIn(self.status,
                      [self.STATUS_REJECTED,
                       self.STATUS_ERR400,
                       self.STATUS_ERR411,
                       self.STATUS_ERR413,
                       self.STATUS_ERR414,
                       # yes, too bad this is used by Tomcat for most 400
                       self.STATUS_ERR500,
                       self.STATUS_501_NOT_IMPLEMENTED,
                       self.STATUS_505_NOT_SUPPORTED],
                      'Bad response status "{0}"'.format(self.status))

    def _end_1st_line_query(self,
                            responses=None,
                            http09_allowed=False,
                            expected_number=1,
                            status_map=None):
        if responses is None:
            responses = self.send_queries()

        self.analysis(responses,
                      http09_allowed=http09_allowed,
                      regular_expected=False)

        self.adjust_status_by_map(status_map)

        allowed = []
        for status_elt, status_gravity in Tools.iteritems(self.status_map):
            if status_gravity is self.GRAVITY_OK:
                allowed.append(status_elt)
        self.assertIn(self.status,
                      allowed)

    def _add_default_status_map(self,
                                valid=False,
                                http09_allowed=False,
                                always_allow_rejected=False):
        self.status_map = {
            # this is only dangerous if any RP is a transmitter of
            # such bad queries. Should be very rare.
            self.STATUS_09DOWNGRADE: self.GRAVITY_WARNING,
            self.STATUS_09OK: self.GRAVITY_WARNING,
            # but, hey, if you are such proxy that's a very bad cleanup
            # FIXME: ensure a RP having final 0.9 response, without
            # tansmission in 0.9, is marked as critical
            self.STATUS_TRANSMITTED_EXACT: self.GRAVITY_CRITICAL,
            self.STATUS_TRANSMITTED_CRAP: self.GRAVITY_CRITICAL,
            self.STATUS_TRANSMITTED: self.GRAVITY_WARNING,
            self.STATUS_WOOKIEE: self.GRAVITY_CRITICAL,
            self.STATUS_SPLITTED: self.GRAVITY_CRITICAL,
        }

        if valid:
            self.status_map[self.STATUS_ACCEPTED] = self.GRAVITY_OK
        else:
            self.status_map[self.STATUS_ACCEPTED] = self.GRAVITY_MINOR

        if always_allow_rejected or not valid:
            self.status_map[self.STATUS_REJECTED] = self.GRAVITY_OK
            self.status_map[self.STATUS_ERR400] = self.GRAVITY_OK
            self.status_map[self.STATUS_ERR413] = self.GRAVITY_OK
            self.status_map[self.STATUS_ERR414] = self.GRAVITY_OK
            self.status_map[self.STATUS_ERR411] = self.GRAVITY_OK
            self.status_map[self.STATUS_501_NOT_IMPLEMENTED] = self.GRAVITY_OK
            self.status_map[self.STATUS_505_NOT_SUPPORTED] = self.GRAVITY_OK
            # rfc 7230 allows 301 on bad request line
            self.status_map[self.STATUS_RED_301] = self.GRAVITY_OK

        if http09_allowed:
            self.status_map[self.STATUS_09OK] = self.GRAVITY_OK
            self.status_map[self.STATUS_09DOWNGRADE] = self.GRAVITY_OK

    def adjust_status_by_map(self, status_map=None):
        "Adjust gravity of the test based on status."
        if status_map is not None:
            if self.status in status_map:
                self.setGravity(status_map[self.status])
        if self.status_map is not None:
            if self.status in self.status_map:
                if self.status_map[self.status] is not self.GRAVITY_OK:
                    self.setGravity(self.status_map[self.status])

    def analysis(self,
                 responses,
                 expected_number=1,
                 http09_allowed=False,
                 regular_expected=False):
        "Launch deep analysis of the responses status."
        self.count_responses = responses.count
        if not self.count_responses:
            self.setStatus(self.STATUS_REJECTED)
        elif self.count_responses > expected_number:
            # Splitting responses is ALWAYS Critical
            self.gravity = self.GRAVITY_CRITICAL
            self.setStatus(self.STATUS_SPLITTED)
        else:
            for response in responses:
                # Continue checking while test status is undecided or while
                # all responses are accepted
                if (self.STATUS_UNKNOWN == self.status
                        or self.STATUS_ACCEPTED == self.status):
                    self.check_for_errors(response)
                if (self.STATUS_UNKNOWN == self.status
                        or self.STATUS_ACCEPTED == self.status):
                    self.check_for_redirect(response)
                if (self.STATUS_UNKNOWN == self.status
                        or self.STATUS_ACCEPTED == self.status):
                    self.check_for_regular_content(
                        response,
                        http09_allowed=http09_allowed,
                        required=regular_expected)
                # check_for_regular_content may have set self.STATUS_09OK
                if (999 == response.code
                        and not http09_allowed
                        and self.status != self.STATUS_09OK):
                    self.setStatus(self.STATUS_09DOWNGRADE)
                    # raise AssertionError('Unauthorized HTTP/0.9 response')

    # @deprecated
    def assertBodyContainsDefaultContent(self, body):
        """Assert that the given bytes contains the default location content"""
        # we obtain an unicode string, body contains only bytes, so we need
        # to obtain a b''
        expected = self.config.get(
            'SERVER_DEFAULT_LOCATION_CONTENT').encode('utf8')
        if expected not in body:
            raise AssertionError('{0} is not present in body'.format(expected))

    def check_for_errors(self, response):

        if ((b"      -mMMNNdhdmhyhNs/mmy+mmyyy+shdo/-...." in response.body)
                and (b"``.-:/mdMNmh++dNddddh+hmod+/ohdy" in response.body)
                and (b"Wookiee !" in response.body)):
            self.setStatus(self.STATUS_WOOKIEE)

        elif Response.ERROR_HTTP09_RESPONSE in response.errors:
            if (b"400" in response.body
                    and b"Bad Request" in response.body):
                self.setStatus(self.STATUS_ERR400)
            if (b"401" in response.body
                    and b"Unauthorized" in response.body):
                self.setStatus(self.STATUS_ERR401)
            if (b"403" in response.body
                    and b"Forbidden" in response.body):
                self.setStatus(self.STATUS_ERR403)
            if (b"404" in response.body
                    and b"Not Found" in response.body):
                self.setStatus(self.STATUS_ERR404)
            if (b"405" in response.body
                    and b"Method Not Allowed" in response.body):
                self.setStatus(self.STATUS_ERR405)
            if (b"411" in response.body
                    and b"Length Required" in response.body):
                self.setStatus(self.STATUS_ERR411)
            if (b"413" in response.body
                    and b"Request Entity Too Large" in response.body):
                self.setStatus(self.STATUS_ERR413)
            if (b"414" in response.body
                    and b"Request URI too long" in response.body):
                self.setStatus(self.STATUS_ERR414)
            if (b"501" in response.body
                    and b"Not Implemented" in response.body):
                self.setStatus(self.STATUS_501_NOT_IMPLEMENTED)
            if (b"505" in response.body
                    and b"Not Supported" in response.body):
                self.setStatus(self.STATUS_505_NOT_SUPPORTED)
            if ((b"502" in response.body or b"503" in response.body)
                    and (b"Bad gateway" in response.body
                         or b"Service Unavailable" in response.body)):
                self.setStatus(self.STATUS_5032)
        else:
            if 400 == response.code:
                self.setStatus(self.STATUS_ERR400)
            if 401 == response.code:
                self.setStatus(self.STATUS_ERR401)
            if 403 == response.code:
                self.setStatus(self.STATUS_ERR403)
            if 404 == response.code:
                self.setStatus(self.STATUS_ERR404)
            if 411 == response.code:
                self.setStatus(self.STATUS_ERR411)
            if 413 == response.code:
                self.setStatus(self.STATUS_ERR413)
            if 414 == response.code:
                self.setStatus(self.STATUS_ERR414)
            if 405 == response.code:
                self.setStatus(self.STATUS_ERR405)
            if 501 == response.code:
                self.setStatus(self.STATUS_501_NOT_IMPLEMENTED)
            if 505 == response.code:
                self.setStatus(self.STATUS_505_NOT_SUPPORTED)
            if 502 == response.code:
                self.setStatus(self.STATUS_5032)
            if 503 == response.code:
                self.setStatus(self.STATUS_5032)

    def check_for_redirect(self, response):
        if Response.ERROR_HTTP09_RESPONSE in response.errors:
            if (b"301" in response.body
                    and b"Moved Permanently" in response.body):
                self.setStatus(self.STATUS_RED_301)
            elif (b"302" in response.body
                    and b"Found" in response.body):
                self.setStatus(self.STATUS_RED_302)
        else:
            if 301 == response.code:
                self.setStatus(self.STATUS_RED_301)
            elif 302 == response.code:
                self.setStatus(self.STATUS_RED_302)

    def _get_expected_content(self):
        expected = self.config.get(
            'SERVER_DEFAULT_LOCATION_CONTENT').encode('utf8')
        return expected

    def check_for_regular_content(self,
                                  response,
                                  http09_allowed=False,
                                  required=True):
        if 200 == response.code:
            self.setStatus(self.STATUS_ACCEPTED)

        expected = self._get_expected_content()
        if Response.ERROR_HTTP09_RESPONSE in response.errors:
            if expected in response.body:
                if http09_allowed:
                    self.setStatus(self.STATUS_09OK)
                else:
                    # regular content present in an http/0.9 response
                    # this is dangerous unless you really requested in 0.9 mode
                    self.setStatus(self.STATUS_09DOWNGRADE)
                    self.gravity = self.GRAVITY_CRITICAL
        else:
            if required and expected not in response.body:
                raise AssertionError('{0} is not present in body'.format(
                    expected))
