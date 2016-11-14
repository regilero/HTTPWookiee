#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# from httpwookiee.config import ConfigFactory
from httpwookiee.config import Register
from httpwookiee.core.base import BaseTest
from httpwookiee.core.tools import Tools
from httpwookiee.http.request import Request
from httpwookiee.core.result import TextStatusResult
from httpwookiee.core.testrunner import WookieeTestRunner
from httpwookiee.core.testloader import WookieeTestLoader

import inspect
import sys
# ###################################### TESTS #########################


class AbstractTestChunks(BaseTest):
    """Test various hack on Tranfer-Encoding: chunked.

    """

    def __init__(self, *args, **kwargs):
        super(AbstractTestChunks, self).__init__(*args, **kwargs)
        # for RP mode message analysis
        self.transmission_zone = Tools.ZONE_HEADERS
        self.send_mode = self.SEND_MODE_UNIQUE

    def test_2000_preflight_regular_chunked_get(self):
        """Let's start by a regular GET with chunked body

        """
        self.real_test = "{0}".format(inspect.stack()[0][3])
        self.setGravity(self.GRAVITY_MINOR)
        self.req.set_method('GET')
        self.req.add_header('Transfer-Encoding', 'chunked')
        self.req.add_header('Content-Type',
                            'application/x-www-form-urlencoded')
        self.req.add_chunk('Hello')
        self.req.add_chunk('World')
        self._end_almost_regular_query()
        Register.flag('get_chunk_{0}'.format(self.reverse_proxy_mode),
                      (self.status == self.STATUS_ACCEPTED))
        self.assertIn(self.status,
                      [self.STATUS_ACCEPTED, self.STATUS_ERR405],
                      'Bad response status {0}'.format(self.status))

    def test_2001_preflight_regular_chunked_post(self):
        """If get is not good, try POST for chunked queries.

        """
        self.real_test = "{0}".format(inspect.stack()[0][3])
        self.setGravity(self.GRAVITY_MINOR)

        self.req.set_method('POST')
        self.req.add_header('Transfer-Encoding', 'chunked')
        self.req.add_header('Content-Type',
                            'application/x-www-form-urlencoded')
        self.req.add_chunk('Hello')
        self.req.add_chunk('World')
        self._end_almost_regular_query()
        Register.flag('post_chunk_{0}'.format(self.reverse_proxy_mode),
                      (self.status == self.STATUS_ACCEPTED))
        self.assertIn(self.status,
                      [self.STATUS_ACCEPTED, self.STATUS_ERR405],
                      'Bad response status {0}'.format(self.status))

    def test_2002_preflight_regular_chunked_double_query(self):
        """We make two chunked queries with a third query inside, no tricks

        The goal is to ensure we really have 2 responses. Makes other failing
        stuff more important (else it means the chunk algo is completly broken)
        """
        self.real_test = "{0}".format(inspect.stack()[0][3])
        self.setGravity(self.GRAVITY_MINOR)
        self.req.add_header('Transfer-Encoding', 'chunked')
        self.req.add_header('Content-Type',
                            'application/x-www-form-urlencoded')

        method = self._get_valid_chunk_method()
        self.req.set_method(method)

        # req2 is not a real query, just the chunked body of req1
        self.req2 = Request(id(self))
        self.req2.method = method
        wlocation = self.get_wookiee_location()
        self.req2.set_location(wlocation, random=True)
        req2 = str(self.req2)
        self.req.add_chunk(req2)

        self.req3 = Request(id(self))
        self.req3.set_location(self.req.location, random=True)

        self.req3.set_method(method)

        req3 = str(self.req3)

        # Yes, not the nicest way to make a pipeline, but it should work.
        # we'll have a pipeline and our client will not temporise the
        # output.
        self.req.add_suffix(req3)

        self._end_almost_regular_query(expected_number=2)

        if not self.status == self.STATUS_ACCEPTED:
            Register.flag('chunk_brain', False)

        if self.STATUS_SPLITTED == self.status:
            Register.flag('chunk_brain', False)
            self.setGravity(self.GRAVITY_CRITICAL)

        self.assertIn(self.status,
                      [self.STATUS_ACCEPTED],
                      'Bad response status {0}'.format(self.status))

    def test_2010_preflight_chunked_and_content_length(self):
        """Mix both Content-Length and chunked, could be rejected (or not).

        This is not plainly wrong, so it can still be accepted, but
        if it is not rejected chunked has priority on Content-Length.
        """
        self.real_test = "{0}".format(inspect.stack()[0][3])
        self.setGravity(self.GRAVITY_MINOR)

        method = self._get_valid_chunk_method()
        self.req.set_method(method)

        self.req.add_header('Transfer-Encoding', 'chunked')
        self.req.add_header('Content-Type',
                            'application/x-www-form-urlencoded')

        # like in other tests, req2 is not really used by our client
        # but just used to build req1's body
        self.req2 = Request(id(self))
        self.req2.method = method
        wlocation = self.get_wookiee_location()
        self.req2.set_location(wlocation, random=True)
        req2 = str(self.req2)
        # Adding a valid Content-Length header (right size)
        # it's size of req2 + CRLF to end chunk + size of end-of-chunks (5)
        # + size of first chunk size and crlf (4)
        self.req.add_header('Content-Length', str(len(req2) + 9))
        self.req.add_chunk(req2)

        self._add_default_status_map(
            valid=False)
        # local additions
        self.status_map[self.STATUS_ACCEPTED] = self.GRAVITY_MINOR
        self.status_map[self.STATUS_TRANSMITTED] = self.GRAVITY_CRITICAL

        # for RP mode:
        self.transmission_map = {
            'Content-Length: 0': self.STATUS_TRANSMITTED_CRAP,
        }

        # we send only 1 query (with a body).
        # but if C-L has the priority this will be 2 queries
        # Note that this query MAY be completly valid, but it is safer
        # if it is rejected (so it's really a minor issue
        self._end_expected_error(expected_number=1)
        Register.flag('chunk_and_cl_{0}'.format(self.reverse_proxy_mode),
                      (self.status not in [self.STATUS_ACCEPTED,
                                           self.STATUS_TRANSMITTED,
                                           self.STATUS_SPLITTED,
                                           self.STATUS_WOOKIEE]))

    def test_2011_chunked_and_wrong_content_length(self):
        """Use chunk+Content length with a wrong Content Length.

        This is not plainly wrong, so it can still be accepted, but
        if it is not rejected chunked has priority on Content-Length.

        If Content-Length has the priority this can be a piece of a
        splitting attack.
        """
        self.real_test = "{0}".format(inspect.stack()[0][3])

        self.setGravity(self.GRAVITY_MINOR)
        if not Register.hasFlag('chunk_and_cl_{0}'.format(
                self.reverse_proxy_mode)):
            self.skipTest("Preflight invalidated all chunk+CL queries.")
        method = self._get_valid_chunk_method()
        self.req.method = method

        self.req.add_header('Transfer-Encoding', 'chunked')
        self.req.add_header('Content-Type',
                            'application/x-www-form-urlencoded')

        # like in other tests, req2 is not really used by our client
        # but just used to build req1's body
        self.req2 = Request(id(self))
        self.req2.method = method
        wlocation = self.get_wookiee_location()
        self.req2.set_location(wlocation, random=True)
        # this will cover the 0\r\n\r\n end-of-chunks regular markup
        # from query1 that will be present after query2 when embedded
        self.req2.add_header('Content-Length', '5')
        req2 = str(self.req2)

        self.req.add_chunk(req2)

        # Adding a wrong content length which only covers the chunk size
        # and first crlf of first chunk.
        size_of_first_chunk = len(req2)
        first_chunk_attr = hex(size_of_first_chunk)[2:]
        size_of_first_chunk_size = len(str(first_chunk_attr))
        wrong_length = size_of_first_chunk_size+2
        self.req.add_header('Content-Length', str(wrong_length))

        self._add_default_status_map(
            valid=False)
        # local additions
        self.status_map[self.STATUS_ACCEPTED] = self.GRAVITY_MINOR
        self.status_map[self.STATUS_TRANSMITTED] = self.GRAVITY_CRITICAL

        # for RP mode:
        self.transmission_map = {
            'Content-Length: 5': self.STATUS_TRANSMITTED_CRAP,
        }
        # we send only 1 query (with a body).
        # but if C-L has the priority this will be 2 queries
        self._end_expected_error(expected_number=1)

    def test_2012_preflight_wrong_content_length_and_chunked(self):
        """Mix both Content-Length and chunked (inv), may be rejected.

        This is not plainly wrong, so it can still be accepted, but
        if it is not rejected chunked has priority on Content-Length.
        This one is like the previous one, but headers order is inverted.
        """
        self.real_test = "{0}".format(inspect.stack()[0][3])
        self.setGravity(self.GRAVITY_MINOR)

        method = self._get_valid_chunk_method()
        self.req.set_method(method)

        # like in other tests, req2 is not really used by our client
        # but just used to build req1's body
        self.req2 = Request(id(self))
        self.req2.method = method
        wlocation = self.get_wookiee_location()
        self.req2.set_location(wlocation, random=True)
        # this will cover the 0\r\n\r\n end-of-chunks regular markup
        # from query1 that will be present after query2 when embedded
        self.req2.add_header('Content-Length', '5')
        req2 = str(self.req2)

        # Adding a wrong content length which only covers the chunk size
        # and first crlf of first chunk.
        size_of_first_chunk = len(req2)
        first_chunk_attr = hex(size_of_first_chunk)[2:]
        size_of_first_chunk_size = len(str(first_chunk_attr))
        wrong_length = size_of_first_chunk_size+2
        self.req.add_header('Content-Length', str(wrong_length))
        self.req.add_chunk(req2)

        self.req.add_header('Transfer-Encoding', 'chunked')
        self.req.add_header('Content-Type',
                            'application/x-www-form-urlencoded')

        self._add_default_status_map(
            valid=False)
        # local additions
        self.status_map[self.STATUS_ACCEPTED] = self.GRAVITY_MINOR
        self.status_map[self.STATUS_TRANSMITTED] = self.GRAVITY_CRITICAL

        # for RP mode:
        self.transmission_map = {
            'Content-Length: 0': self.STATUS_TRANSMITTED_CRAP,
        }

        # we send only 1 query (with a body).
        # but if C-L has the priority this will be 2 queries
        # Note that this query MAY be completly valid, but it is safer
        # if it is rejected (so it's really a minor issue
        self._end_expected_error(expected_number=1)
        Register.flag('cl_and_chunk_{0}'.format(self.reverse_proxy_mode),
                      (self.status not in [self.STATUS_ACCEPTED,
                                           self.STATUS_TRANSMITTED,
                                           self.STATUS_SPLITTED,
                                           self.STATUS_WOOKIEE]))

    def test_2020_bad_chunked_transfer_encoding(self):
        """chunk not used as last marker in Transfer-Encoding header.

        """
        self.real_test = "{0}".format(inspect.stack()[0][3])
        self.setGravity(self.GRAVITY_MINOR)

        method = self._get_valid_chunk_method()
        self.req.method = method
        # chunk MUST be the last marker
        self.req.add_header('Transfer-Encoding', 'chunked, zorg')
        self.req.add_header('Content-Type',
                            'application/x-www-form-urlencoded')
        self.req.add_chunk('Hello')
        self.req.add_chunk('World')
        self._end_expected_error()

    def test_2021_chunked_header_hidden_by_NULL(self):
        """Transfer-Encoding header splitted by a NULL char.

        """
        self.real_test = "{0}".format(inspect.stack()[0][3])
        method = self._get_valid_chunk_method()
        self.req.set_method(method)
        self.setGravity(self.GRAVITY_CRITICAL)
        self.req.add_header('Transfer-{0}: 42{1}Encoding'.format(
                                Tools.NULL,
                                Tools.CRLF),
                            'chunked',
                            sep=':')
        self.req.add_header('Content-Type',
                            'application/x-www-form-urlencoded')
        self.req2 = Request(id(self))
        self.req2.method = method
        wlocation = self.get_wookiee_location()
        self.req2.set_location(wlocation, random=True)
        req2 = Tools.CRLF + str(self.req2)
        self.req.add_header('Content-Length', str(len(req2)))
        # by forcing chunk_size to 0 we will detect splitters
        # as they will apply the chunked mode and req2 wont be a body anymore
        self.req.add_chunk(req2, chunk_size=0)
        self.req.end_of_chunks = False

        self._add_default_status_map(
            valid=False)
        # local additions
        self.status_map[self.STATUS_ACCEPTED] = self.GRAVITY_MINOR
        self.status_map[self.STATUS_TRANSMITTED] = self.GRAVITY_CRITICAL

        # for RP mode:
        self.transmission_map = {
            'Content-Length: 0': self.STATUS_TRANSMITTED_CRAP,
            'Transfer-{0}: 42'.format(
                Tools.NULL): self.STATUS_TRANSMITTED,
        }
        self._end_expected_error(expected_number=1)

    def test_2022_chunked_header_hidden_by_bad_eol_1(self):
        """Use chunk+Content length, but chunk header should be invalid.

        """
        self.real_test = "{0}".format(inspect.stack()[0][3])
        method = self._get_valid_chunk_method()
        self.req.set_method(method)

        self.setGravity(self.GRAVITY_CRITICAL)

        self.req.add_header('Dummy',
                            'Header{0}{1}Transfer-Encoding:chunked'.format(
                                Tools.CR,
                                ''),
                            sep=':')
        self.req.add_header('Content-Type',
                            'application/x-www-form-urlencoded')

        self.req2 = Request(id(self))
        self.req2.method = method
        wlocation = self.get_wookiee_location()
        self.req2.set_location(wlocation, random=True)
        req2 = Tools.CRLF + str(self.req2)
        self.req.add_header('Content-Length', str(len(req2)))
        # by forcing chunk_size to 0 we will detect splitters
        # as they will apply the chunked mode and req2 wont be a body anymore
        self.req.add_chunk(req2, chunk_size=0)
        self.req.end_of_chunks = False

        self._add_default_status_map(
            valid=False)
        # local additions
        self.status_map[self.STATUS_ACCEPTED] = self.GRAVITY_MINOR
        self.status_map[self.STATUS_TRANSMITTED] = self.GRAVITY_CRITICAL

        # for RP mode:
        self.transmission_map = {
            'Content-Length: 0': self.STATUS_TRANSMITTED_CRAP,
            'Dummy: Header\r'
            'Transfer-Encoding:chunked': self.STATUS_TRANSMITTED,
            'Dummy: Header\r'
            'Transfer-Encoding: chunked': self.STATUS_TRANSMITTED,
        }

        self._end_expected_error(expected_number=1)

    def test_2023_chunked_header_hidden_by_bad_eol_2(self):
        """Use chunk+Content length, but chunk header should be invalid.

        """
        self.real_test = "{0}".format(inspect.stack()[0][3])

        method = self._get_valid_chunk_method()
        self.req.set_method(method)

        self.setGravity(self.GRAVITY_CRITICAL)

        self.req.add_header('Dummy',
                            'Header{0}{1}Transfer-Encoding:chunked'.format(
                                Tools.CR,
                                Tools.SP),
                            sep=':')
        self.req.add_header('Content-Type',
                            'application/x-www-form-urlencoded')

        self.req2 = Request(id(self))
        self.req2.method = method
        wlocation = self.get_wookiee_location()
        self.req2.set_location(wlocation, random=True)
        req2 = Tools.CRLF + str(self.req2)
        self.req.add_header('Content-Length', str(len(req2)))
        # by forcing chunk_size to 0 we will detect splitters
        # as they will apply the chunked mode and req2 wont be a body anymore
        self.req.add_chunk(req2, chunk_size=0)
        self.req.end_of_chunks = False

        self._add_default_status_map(
            valid=False)
        # local additions
        self.status_map[self.STATUS_ACCEPTED] = self.GRAVITY_MINOR
        self.status_map[self.STATUS_TRANSMITTED] = self.GRAVITY_CRITICAL

        # for RP mode:
        self.transmission_map = {
            'Content-Length: 0': self.STATUS_TRANSMITTED_CRAP,
            'Dummy: Header\r '
            'Transfer-Encoding:chunked': self.STATUS_TRANSMITTED,
            'Dummy: Header\r '
            'Transfer-Encoding: chunked': self.STATUS_TRANSMITTED,
        }

        self._end_expected_error(expected_number=1)

    def test_2024_chunked_header_hidden_by_bad_eol_3(self):
        """Use chunk+Content length, but chunk header should be invalid.

        The query should be rejected, or only apply Content-Lenght.
        If Content-Length is applied.
        """
        self.real_test = "{0}".format(inspect.stack()[0][3])

        method = self._get_valid_chunk_method()
        self.req.set_method(method)

        self.setGravity(self.GRAVITY_CRITICAL)

        self.req.add_header('Dummy',
                            'Header{0}{1}Transfer-Encoding:chunked'.format(
                                Tools.CR,
                                'Z'),
                            sep=':')
        self.req.add_header('Content-Type',
                            'application/x-www-form-urlencoded')

        self.req2 = Request(id(self))
        self.req2.method = method
        wlocation = self.get_wookiee_location()
        self.req2.set_location(wlocation, random=True)
        req2 = Tools.CRLF + str(self.req2)

        self.req.add_header('Content-Length', str(len(req2)))
        # by forcing chunk_size to 0 we will detect splitters
        # as they will apply the chunked mode and req2 wont be a body anymore
        self.req.add_chunk(req2, chunk_size=0)
        self.req.end_of_chunks = False

        self._add_default_status_map(
            valid=False)
        # local additions
        self.status_map[self.STATUS_ACCEPTED] = self.GRAVITY_MINOR
        self.status_map[self.STATUS_TRANSMITTED] = self.GRAVITY_CRITICAL

        # for RP mode:
        self.transmission_map = {
            'Content-Length: 0': self.STATUS_TRANSMITTED_CRAP,
            'Dummy: Header\rZ'
            'Transfer-Encoding:chunked': self.STATUS_TRANSMITTED,
            'Dummy: Header\rZ'
            'Transfer-Encoding: chunked': self.STATUS_TRANSMITTED,
            '\nZTransfer-Encoding:chunked': self.STATUS_TRANSMITTED_CRAP,
            '\nZ Transfer-Encoding:chunked': self.STATUS_TRANSMITTED_CRAP,
        }

        self._end_expected_error(expected_number=1)

    def test_2030_chunked_size_truncation(self):
        """Try an int truncation on the chunk size.

        """
        self.real_test = "{0}".format(inspect.stack()[0][3])

        method = self._get_valid_chunk_method()
        self.req.set_method(method)

        self.setGravity(self.GRAVITY_CRITICAL)
        self.req.add_header('Transfer-Encoding', 'chunked')
        self.req.add_header('Content-Type',
                            'application/x-www-form-urlencoded')

        self.req2 = Request(id(self))
        self.req2.method = method
        wlocation = self.get_wookiee_location()
        self.req2.set_location(wlocation, random=True)
        # this will cover the 0\r\n\r\n end-of-chunks regular markup
        # from query1 that will be present after query2 when embedded
        self.req2.add_header('Content-Length', '5')
        req2 = str(self.req2)

        something = '{0}{1}'.format(
            Tools.CRLF,
            req2)
        # Apache issue, truncation in hexadecimal chunk size, final size is 0
        # for Apache, so the rest of the chunk is interpreted as a trailer (if
        # any). This means an end of query.
        # we add 4 chars to cover the chunk size of second header +CRLF
        # chunk_size = 0000000...00000004e
        # which will be read as chunk_size = 00000000000000000000000000000
        chunk_size = "0" * 33 + hex(len(something))[2:]
        self.req.add_chunk(something, chunk_size=chunk_size)

        self._add_default_status_map(
            valid=True,
            always_allow_rejected=True)
        # local additions
        # here transmission is valid, but some actr may split on this syntax
        # so it would be better to fix the 00000... prefix syntax
        self.status_map[self.STATUS_TRANSMITTED_CRAP] = self.GRAVITY_WARNING

        # for RP mode:
        self.transmission_zone = Tools.ZONE_CHUNK_SIZE
        self.transmission_map = {
            '000000000000000000000000': self.STATUS_TRANSMITTED_CRAP,
        }
        # this is a valid query in fact.
        # so we should not expect an error (but 2 responses would be very bad)
        self._end_regular_query(expected_number=1, can_be_rejected=False)


class TestChunks(AbstractTestChunks):
    pass


class AbstractChunksOverflow(BaseTest):

    def __init__(self, *args, **kwargs):
        super(AbstractChunksOverflow, self).__init__(*args, **kwargs)
        # for RP mode message analysis
        self.transmission_zone = Tools.ZONE_HEADERS
        self.send_mode = self.SEND_MODE_UNIQUE

    def setUp(self):
        # allows children to alter main behavior of all tests
        self.setLocalSettings()
        super(AbstractChunksOverflow, self).setUp()

    def setLocalSettings(self):
        "You should overwrite this one."
        self.nb = 65535

    def test_2040_chunked_size_overflow(self):
        """Try an int overflow on the chunk size

        """
        self.real_test = "{0}_{1}".format(inspect.stack()[0][3],
                                          self.nb)

        method = self._get_valid_chunk_method()
        self.req.set_method(method)

        self.setGravity(self.GRAVITY_CRITICAL)
        self.req.add_header('Transfer-Encoding', 'chunked')
        self.req.add_header('Content-Type',
                            'application/x-www-form-urlencoded')

        self.req2 = Request(id(self))
        self.req2.method = method
        wlocation = self.get_wookiee_location()
        self.req2.set_location(wlocation, random=True)
        # this will cover the 0\r\n\r\n end-of-chunks regular markup
        # from query 1 that will be present after query2 when embedded
        self.req2.add_header('Content-Length', '5')
        req2 = str(self.req2)

        # we add 4 chars to cover the chunk size of second header +CRLF
        chunk_size = hex(self.nb)[2:]
        self.req.add_chunk(Tools.CRLF + req2, chunk_size=chunk_size)

        self._add_default_status_map(
            valid=False)
        # local additions
        # here accepting a chunked query with crap in chunk size attribute
        # is always quite strange
        self.status_map[self.STATUS_ACCEPTED] = self.GRAVITY_WARNING
        self.status_map[self.STATUS_TRANSMITTED] = self.GRAVITY_CRITICAL

        # for RP mode:
        self.transmission_map = {
            '\r\n{0}\r\n'.format(chunk_size): self.STATUS_TRANSMITTED,
            'Content-Length: {0}\r\n'.format(
                self.nb): self.STATUS_TRANSMITTED_CRAP,
            'Content-Length:{0}\r\n'.format(
                self.nb): self.STATUS_TRANSMITTED_CRAP,
        }

        self._end_expected_error(expected_number=1)

    def test_2041_chunked_size_overflow_with_trailers(self):
        """Try an int overflow on the chunk size, add trailer headers.

        """
        self.real_test = "{0}_{1}".format(inspect.stack()[0][3],
                                          self.nb)

        method = self._get_valid_chunk_method()
        self.req.set_method(method)

        self.setGravity(self.GRAVITY_CRITICAL)
        self.req.add_header('Transfer-Encoding', 'chunked')
        self.req.add_header('Content-Type',
                            'application/x-www-form-urlencoded')
        self.req.add_header('Trailer', 'Zorglub')

        self.req2 = Request(id(self))
        self.req2.method = method
        wlocation = self.get_wookiee_location()
        self.req2.set_location(wlocation, random=True)
        # this will cover the 0\r\n\r\n end-of-chunks regular markup
        # from query 1 that will be present after query2 when embedded
        self.req2.add_header('Content-Length', '5')
        req2 = str(self.req2)

        # We add 4 chars to cover the chunk size of second header +CRLF
        chunk_size = hex(self.nb)[2:]
        trailers = u'Zorglub: Bulgroz\r\nContent-Length:42\r\n'
        bad_chunk = '{0}{1}{2}'.format(trailers,
                                       Tools.CRLF,
                                       req2)
        self.req.add_chunk(bad_chunk, chunk_size=chunk_size)

        self._add_default_status_map(
            valid=False)
        # local additions
        # here accepting a chunked query with crap in chunk size attribute
        # is always quite strange
        self.status_map[self.STATUS_ACCEPTED] = self.GRAVITY_WARNING
        self.status_map[self.STATUS_TRANSMITTED] = self.GRAVITY_CRITICAL

        # for RP mode:
        self.transmission_map = {
            '\r\n{0}\r\n'.format(chunk_size): self.STATUS_TRANSMITTED,
            'Content-Length: {0}\r\n'.format(
                self.nb): self.STATUS_TRANSMITTED_CRAP,
            'Content-Length:{0}\r\n'.format(
                self.nb): self.STATUS_TRANSMITTED_CRAP,
            # Content-Length header in trailers is not forbidden
            # but at least it should have no consequences, so we should
            # not find it in the headers.
            'Content-Length:42\r\n': self.STATUS_TRANSMITTED_CRAP,
            'Content-Length: 42\r\n': self.STATUS_TRANSMITTED_CRAP,
        }

        self._end_expected_error(expected_number=1)

    def test_2042_chunked_size_overflow_with_delayed_chunks(self):
        """Try an int overflow on the chunk size, add trailer headers.

        """
        self.real_test = "{0}_{1}".format(inspect.stack()[0][3],
                                          self.nb)

        method = self._get_valid_chunk_method()
        self.req.set_method(method)

        self.setGravity(self.GRAVITY_CRITICAL)
        self.req.add_header('Transfer-Encoding', 'chunked')
        self.req.add_header('Content-Type',
                            'application/x-www-form-urlencoded')
        self.req.add_header('Trailer', 'Zorglub')

        self.req2 = Request(id(self))
        self.req2.method = method
        wlocation = self.get_wookiee_location()
        self.req2.set_location(wlocation, random=True)
        self.req2.add_header('Content-Length', '5')
        req2 = str(self.req2)

        chunk_size = hex(self.nb)[2:]
        bad_chunk = ''
        self.req.add_chunk(bad_chunk, chunk_size=chunk_size, chunk_eol=u'')
        self.req.add_delayed_chunk(req2, delay=0.5)
        self.req.add_delayed_chunk(req2, delay=2)

        self._add_default_status_map(
            valid=False)
        # local additions
        # here accepting a chunked query with crap in chunk size attribute
        # is always quite strange
        self.status_map[self.STATUS_ACCEPTED] = self.GRAVITY_WARNING
        self.status_map[self.STATUS_TRANSMITTED] = self.GRAVITY_CRITICAL

        # for RP mode:
        self.transmission_map = {
            '\r\n{0}\r\n'.format(chunk_size): self.STATUS_TRANSMITTED,
            'Content-Length: {0}\r\n'.format(
                self.nb): self.STATUS_TRANSMITTED_CRAP,
            'Content-Length:{0}\r\n'.format(
                self.nb): self.STATUS_TRANSMITTED_CRAP,
        }

        self._end_expected_error(expected_number=1)
#
#
# class TestChunksOverflow256(AbstractChunksOverflow):
#
#    def setLocalSettings(self):
#        self.nb = 256


class TestChunksOverflow65536(AbstractChunksOverflow):

    def setLocalSettings(self):
        self.nb = 65536


class TestChunksOverflow4294967296(AbstractChunksOverflow):

    def setLocalSettings(self):
        self.nb = 4294967296


class TestChunksOverflow18446744073709551616(AbstractChunksOverflow):

    def setLocalSettings(self):
        self.nb = 18446744073709551616


if __name__ == '__main__':
    tl = WookieeTestLoader(debug=True)
    testSuite = tl.loadTestsFromModule(sys.modules[__name__])
    # without stream forced here python 2.7 is failing
    WookieeTestRunner(resultclass=TextStatusResult,
                      verbosity=2,
                      buffer=True,
                      stream=sys.stderr).run(testSuite)
