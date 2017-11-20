#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Internal Tests
#
from httpwookiee.http.parser.requests import Requests
from httpwookiee.http.parser.responses import Responses
import unittest
import sys


class Test_Request_Repr(unittest.TestCase):

    def __init__(self, methodName="runTest"):
        super(Test_Request_Repr, self).__init__(methodName)
        self.maxDiff = 5000

    def getStatus(self, format=None):
        return ''

    def getGravity(self, human=False):
        if not human:
            return 0
        else:
            b'Unknown'

    def test_regular_request(self):
        "Test regular request output"

        request = (b"GET /foo HTTP/1.0\r\n"
                   b"Host: example.com\r\n"
                   b"Header1: value1\r\n"
                   b"Header2: value2\r\n"
                   b"Content-Length: 18\r\n"
                   b"\r\n"
                   b"This is the body\r\n")

        req = Requests().parse(request)
        obtained = str(req).split(u'\n')
        should = [u'-1 Requests-',
                  u'---',
                  u' [Req. 1st line]',
                  u'[GET]<SP> [/foo]<SP> HTTP/[1][.][0] [[CR][LF]]',
                  u' [Req. Headers]',
                  u'[HOST] [:]<SP> [example.com] [[CR][LF]]',
                  u'[HEADER1] [:]<SP> [value1] [[CR][LF]]',
                  u'[HEADER2] [:]<SP> [value2] [[CR][LF]]',
                  u'[CONTENT-LENGTH] [:]<SP> [18] [[CR][LF]]',
                  u' [Req. Body] (size 18)']
        if sys.version_info[0] < 3:
            # python2
            should.append(u'This is the body\r')
            should.append(u'')
        else:
            should.append(u"b'This is the body\\r\\n'"),
        should.append(u' ++++++++++++++++++++++++++++++++++++++')
        should.append(u'')
        should.append(u'---')
        self.assertEqual(should, obtained)

    def test_request_version09(self):
        "Test request output for http 0.9"

        request = (b"GET /foo\r\n"
                   b"Hello, how are you?\r\n"
                   b"\r\n")

        req = Requests().parse(request)
        obtained = str(req).split(u'\n')
        should = [(u'******INVALID Requests STREAM <'
                   u' Has invalid Message;>******'),
                  u'-1 Requests-',
                  u'---',
                  u'****INVALID Request < Bad First line in Request;>****',
                  u' [Req. 1st line]']
        if sys.version_info[0] < 3:
            should.append(u'**(raw):GET /foo\r'),
            should.append(u'**'),
        else:
            should.append(u"**(raw):b'GET /foo\\r\\n'**"),

        should.append(u'**INVALID FIRST LINE < Maybe an HTTP/0.9 request;>**')
        should.append(u'[GET]<SP> [/foo] HTTP/[0][.][9] [[CR][LF]]')
        should.append(u' [Req. Headers]')

        should.append(u' [Req. Body] (size 23)')
        if sys.version_info[0] < 3:
            # python2
            should.append(u'Hello, how are you?\r')
            should.append(u'\r')
            should.append(u'')
        else:
            should.append(u"b'Hello, how are you?\\r\\n\\r\\n'"),
        should.append(u' ++++++++++++++++++++++++++++++++++++++')
        should.append(u'')
        should.append(u'---')
        self.assertEqual(should, obtained)

    def test_request_bad_first_line_1(self):
        "Test various bad first lines."

        request = (b"GET\00/foo HTTP/1.1\r\n"
                   b"\r\n")
        req = Requests().parse(request)
        obtained = str(req).split(u'\n')

        should = [(u'******INVALID Requests STREAM <'
                   u' Has invalid Message;>******'),
                  u'-1 Requests-',
                  u'---',
                  u'****INVALID Request < Bad First line in Request;>****',
                  u' [Req. 1st line]']
        if sys.version_info[0] < 3:
            should.append(u'**(raw):GET\x00/foo HTTP/1.1\r'),
            should.append(u'**'),
        else:
            should.append(u"**(raw):b'GET\\x00/foo HTTP/1.1\\r\\n'**"),
        should.append((u'**INVALID FIRST LINE < Bad character detected;'
                       u' Invalid Request method; Maybe an HTTP/0.9 request;'
                       u' Message should be Rejected;>**'))
        should.append((u'[GET<Err><Err><Err><Err><Err>]<SP>'
                       u' [<Err>TTP/1.1] HTTP/[0][.][9] [[CR][LF]]'))
        should.append(u' [Req. Headers]')
        should.append(u' [Req. Body] (size 2)')
        if sys.version_info[0] < 3:
            # python2
            should.append(u'\r')
            should.append(u'')
        else:
            should.append(u"b'\\r\\n'"),
        should.append(u' ++++++++++++++++++++++++++++++++++++++')
        should.append(u'')
        should.append(u'---')
        self.assertEqual(should, obtained)

    def test_request_bad_first_line_2(self):
        "Test various bad first lines."

        request = (b"GET /foo\x0cHTTP/-1.1\r\n"
                   b"\r\n")
        req = Requests().parse(request)
        obtained = str(req).split(u'\n')

        should = [(u'******INVALID Requests STREAM <'
                   u' Has invalid Message;>******'),
                  u'-1 Requests-',
                  u'---',
                  u'****INVALID Request < Bad First line in Request;>****',
                  u' [Req. 1st line]']
        if sys.version_info[0] < 3:
            should.append(u'**(raw):GET /foo\x0cHTTP/-1.1\r'),
            should.append(u'**'),
        else:
            should.append(u"**(raw):b'GET /foo\\x0cHTTP/-1.1\\r\\n'**"),
        should.append((u'**INVALID FIRST LINE < Bad character detected;'
                       u' Bad space on request; Maybe an HTTP/0.9 request;'
                       u' Message should be Rejected;>**'))
        should.append((u'[GET]<SP> [/foo]<BS> HTTP/[0][.][9] []'))
        should.append(u' [Req. Headers]')
        should.append(u' [Req. Body] (size 2)')
        if sys.version_info[0] < 3:
            # python2
            should.append(u'\r')
            should.append(u'')
        else:
            should.append(u"b'\\r\\n'"),
        should.append(u' ++++++++++++++++++++++++++++++++++++++')
        should.append(u'')
        should.append(u'---')
        self.assertEqual(should, obtained)

    def test_request_absolute_first_line(self):
        "Test absolute uris in first lines."

        # regular absolute domain
        request = (b"GET http://example.com/foo HTTP/1.1\r\n"
                   b"\r\n")
        req = Requests().parse(request)
        obtained = str(req).split(u'\n')

        should = [u'-1 Requests-',
                  u'---',
                  u' [Req. 1st line]',
                  (u'[GET]<SP> <[http://][example.com]>[/foo]<SP> '
                   u'HTTP/[1][.][1] [[CR][LF]]'),
                  u' [Req. Headers]',
                  u' [Req. Body] (size 0)']
        if sys.version_info[0] < 3:
            should.append(u''),
        else:
            should.append(u"b''"),
        should.append(u' ++++++++++++++++++++++++++++++++++++++')
        should.append(u'')
        should.append(u'---')
        self.assertEqual(should, obtained)

        # absolute domain: empty domain (with https)
        request = (b"GET https:// HTTP/1.1\r\n"
                   b"\r\n")
        req = Requests().parse(request)
        obtained = str(req).split(u'\n')

        should = [(u'******INVALID Requests STREAM <'
                   u' Has invalid Message;>******'),
                  u'-1 Requests-',
                  u'---',
                  u'****INVALID Request < Bad First line in Request;>****',
                  u' [Req. 1st line]']
        should.append((u'**INVALID FIRST LINE < Empty domain in absolute uri;'
                       u' Empty location;>**'))
        should.append((u'[GET]<SP> <[https://][<Err>]>[<Err>]<SP> '
                       u'HTTP/[1][.][1] [[CR][LF]]'))
        should.append(u' [Req. Headers]')
        should.append(u' [Req. Body] (size 0)')
        if sys.version_info[0] < 3:
            should.append(u'')
        else:
            should.append(u"b''"),
        should.append(u' ++++++++++++++++++++++++++++++++++++++')
        should.append(u'')
        should.append(u'---')
        self.assertEqual(should, obtained)

        # absolute domain: empty domain v2, with 0.9
        request = (b"GET http:///\r\n")
        req = Requests().parse(request)
        obtained = str(req).split(u'\n')

        should = [(u'******INVALID Requests STREAM <'
                   u' Has invalid Message;>******'),
                  u'-1 Requests-',
                  u'---',
                  u'****INVALID Request < Bad First line in Request;>****',
                  u' [Req. 1st line]']
        if sys.version_info[0] < 3:
            should.append(u'**(raw):GET http:///\r')
            should.append(u"**")
        else:
            should.append(u"**(raw):b'GET http:///\\r\\n'**")
        should.append((u'**INVALID FIRST LINE < Empty domain in absolute uri;'
                       u' Maybe an HTTP/0.9 request;>**'))
        should.append((u'[GET]<SP> <[http://][<Err>]>[/] '
                       u'HTTP/[0][.][9] [[CR][LF]]'))
        should.append(u' [Req. Headers]')
        should.append(u' [Req. Body] (size 0)')
        if sys.version_info[0] < 3:
            should.append(u'')
        else:
            should.append(u"b''"),
        should.append(u' ++++++++++++++++++++++++++++++++++++++')
        should.append(u'')
        should.append(u'---')
        self.assertEqual(should, obtained)

        # absolute domain: bad chars
        request = (b"GET http://-example\x0e.com/bar HTTP/1.1\r\n"
                   b"\r\n")
        req = Requests().parse(request)
        obtained = str(req).split(u'\n')

        should = [(u'******INVALID Requests STREAM <'
                   u' Has invalid Message;>******'),
                  u'-1 Requests-',
                  u'---',
                  u'****INVALID Request < Bad First line in Request;>****',
                  u' [Req. 1st line]']
        should.append((u'**INVALID FIRST LINE < Bad character in domain;'
                       u' Message should be Rejected;>**'))
        should.append((u'[GET]<SP> <[http://][<Err>example<Err>.com]>'
                       u'[/bar]<SP> HTTP/[1][.][1] [[CR][LF]]'))
        should.append(u' [Req. Headers]')
        should.append(u' [Req. Body] (size 0)')
        if sys.version_info[0] < 3:
            should.append(u'')
        else:
            should.append(u"b''"),
        should.append(u' ++++++++++++++++++++++++++++++++++++++')
        should.append(u'')
        should.append(u'---')
        self.assertEqual(should, obtained)

    def test_request_multiline_headers(self):
        "Test multiline headers output"

        request = (b"GET /foo HTTP/1.0\r\n"
                   b"Host: example.com\r\n"
                   b"H1: v1\r\n"
                   b" H2: v2\r\n"
                   b" H3: v3\r\n"
                   b"foo: bar bar\r\n"
                   b"H4:\r\n"
                   b" H5:v5\r\n"
                   b"\r\n")

        req = Requests().parse(request)
        obtained = str(req).split(u'\n')
        should = [u'-1 Requests-',
                  u'---',
                  u'****BAD Request < Has invalid Header;>****',

                  u' [Req. 1st line]',
                  u'[GET]<SP> [/foo]<SP> HTTP/[1][.][0] [[CR][LF]]',

                  u' [Req. Headers]',
                  u'[HOST] [:]<SP> [example.com] [[CR][LF]]',

                  u'**BAD HEADER < Optional Multiline Header merged;>**',
                  (u'[H1] [:]<SP> [v1<SP>H2:<SP>v2<SP>H3:<SP>v3]'
                   u' [[CR][LF]]'),

                  u'[FOO] [:]<SP> [bar<SP>bar] [[CR][LF]]',

                  u'**BAD HEADER < Optional Multiline Header merged;>**',
                  (u'[H4] [:]<SP> [<SP>H5:v5]'
                   u' [[CR][LF]]'),

                  u' [Req. Body] (size 0)']
        if sys.version_info[0] < 3:
            # python2
            should.append(u'')
        else:
            should.append(u"b''"),
        should.append(u' ++++++++++++++++++++++++++++++++++++++')
        should.append(u'')
        should.append(u'---')
        self.assertEqual(should, obtained)

    def test_request_bad_headers(self):
        "Test some invalid headers analysis and messages"

        request = (b"GET /foo HTTP/1.0\r\n"
                   b" H2: v2\r\n"
                   b" H3: v3\r\n"
                   b"Host: example.com\r\n"
                   b"Header1: value1\r\n"
                   b"\x07Foo: Bar\rB\r\n"
                   b"Foo2: Bar\r\rB\r\n"
                   b": zog1\r\n"
                   b"Zog2 Zog:zog \r\n"
                   b"Zog2b\t\r Zog:zog \r\n"
                   b"Zog2c\t \r  :zog \r\n"
                   b"Zog3 : zog\r\n"
                   b"Zog4: zog \r\n"
                   b"Zog5\t:zog \r\n"
                   b"Zog6:\tzog \r\n"
                   b"Zog7:zog\t\r\n"
                   b"Zo\0g8: zog \r\n"
                   b"Zog9:\0zog\r\n"
                   b"Zog10:zog\0\r\n"
                   b"Zog11:zog\r\r\n"
                   b"Zog12:zog\n"
                   b"\r\n")

        req = Requests().parse(request)
        obtained = str(req).split(u'\n')

        should = [(u'******INVALID Requests STREAM '
                   u'< Has invalid Message;>******'),
                  u'-1 Requests-',
                  u'---',

                  (u'****INVALID Request <'
                   u' Has first header in the optional folding format;'
                   u' Has invalid Header;>****'),

                  u' [Req. 1st line]',
                  u'[GET]<SP> [/foo]<SP> HTTP/[1][.][0] [[CR][LF]]',

                  u' [Req. Headers]',

                  u'**BAD HEADER < Optional Multiline Header detected;>**',
                  u'<SP>[] []<SP> [H2:<SP>v2] [[CR][LF]]',
                  u'**BAD HEADER < Optional Multiline Header detected;>**',
                  u'<SP>[] []<SP> [H3:<SP>v3] [[CR][LF]]',

                  u'[HOST] [:]<SP> [example.com] [[CR][LF]]',
                  u'[HEADER1] [:]<SP> [value1] [[CR][LF]]',

                  (u'**INVALID HEADER < Bad space separator;'
                   u' Invalid character in header name;>**'),
                  u'[<Err>FOO] [:]<SP> [Bar<BS>B] [[CR][LF]]',

                  (u'**BAD HEADER < Bad space separator;'
                   u' Multiple CR detected;>**'),
                  u'[FOO2] [:]<SP> [Bar<BS><BS>B] [[CR][LF]]',

                  u'**INVALID HEADER < Empty header name;>**',
                  u'[] [:]<SP> [zog1] [[CR][LF]]',

                  u'**BAD HEADER < Invalid character in header name; '
                  u'Space in header suffix;>**',
                  u'[ZOG2<ErrSP>ZOG] [:] [zog] <SP>[[CR][LF]]',

                  u'**BAD HEADER < Bad space separator; '
                  u'Invalid character in header name; '
                  u'Space in header suffix;>**',
                  u'[ZOG2B<BS><BS><ErrSP>ZOG] [:] [zog] <SP>[[CR][LF]]',

                  u'**INVALID HEADER < Bad space separator; '
                  u'Invalid character in header name; '
                  u'Space before separator; '
                  u'Space in header suffix;>**',
                  u'[ZOG2C] <BS><ErrSP><BS><ErrSP><ErrSP>[:]'
                  u' [zog] <SP>[[CR][LF]]',

                  u'**INVALID HEADER < Invalid character in header name; '
                  u'Space before separator;>**',
                  u'[ZOG3] <ErrSP>[:]<SP> [zog] [[CR][LF]]',

                  u'**BAD HEADER < Space in header suffix;>**',
                  u'[ZOG4] [:]<SP> [zog] <SP>[[CR][LF]]',

                  (u'**INVALID HEADER < Bad space separator;'
                   u' Space before separator; Space in header suffix;>**'),
                  u'[ZOG5] <BS>[:] [zog] <SP>[[CR][LF]]',

                  (u'**BAD HEADER < Bad space separator;'
                   u' Space in header suffix;>**'),
                  u'[ZOG6] [:]<BS> [zog] <SP>[[CR][LF]]',

                  (u'**BAD HEADER < Space in header suffix;>**'),
                  u'[ZOG7] [:] [zog] <SP>[[CR][LF]]',

                  (u'**INVALID HEADER < Invalid character in header name;'
                   u' Space in header suffix;>**'),
                  u'[ZO<Err>G8] [:]<SP> [zog] <SP>[[CR][LF]]',

                  u'[ZOG9] [:] [\x00zog] [[CR][LF]]',
                  u'[ZOG10] [:] [zog\x00] [[CR][LF]]',

                  u'**BAD HEADER < Multiple CR detected;>**',
                  u'[ZOG11] [:] [zog] [[CR][CR][LF]]',

                  u'**BAD HEADER < Line end is LF and not CRLF;>**',
                  u'[ZOG12] [:] [zog] [[LF]]',


                  u' [Req. Body] (size 0)']
        if sys.version_info[0] < 3:
            # python2
            should.append(u'')
        else:
            should.append(u"b''"),
        should.append(u' ++++++++++++++++++++++++++++++++++++++')
        should.append(u'')
        should.append(u'---')
        self.assertEqual(should, obtained)

    def test_request_bad_chunks(self):
        "Test chunks output"

        request = (b"GET /foo HTTP/1.0\r\n"
                   b"Host: example.com\r\n"
                   b"Transfer-Encoding: chunked\r\n"
                   b"\r\n"
                   b"000000008\r\n"
                   b"12345678\r\n"
                   b"04\r\n"
                   b"abcdefghij\r\n"
                   b"5\r\n"
                   b"abcde\r\n"
                   b"1; ZORG\r\n"
                   b"Z\r\n"
                   b"0\r\n"
                   b"\r\n")

        req = Requests().parse(request)
        obtained = str(req).split(u'\n')

        if sys.version_info[0] < 3:
            # python2
            raw8 = (u"**(raw):000000008\\r\\n**"
                    u"**BAD CHUNK < Bad chunk size;>**")
        else:
            raw8 = (u"**(raw):b'000000008\\r\\n'**"
                    u"**BAD CHUNK < Bad chunk size;>**")
        should = [u'-1 Requests-',
                  u'---',
                  (u'****BAD Request < Has bad Chunk; '
                   'Has extra Chunk data;>****'),

                  u' [Req. 1st line]',
                  u'[GET]<SP> [/foo]<SP> HTTP/[1][.][0] [[CR][LF]]',

                  u' [Req. Headers]',
                  u'[HOST] [:]<SP> [example.com] [[CR][LF]]',
                  u'[TRANSFER-ENCODING] [:]<SP> [chunked] [[CR][LF]]',

                  u' [Req. Chunks] (5)',
                  raw8,
                  u'[08 (8)] [[CR][LF]]',
                  u'[04 (4)] [[CR][LF]]',
                  u'[05 (5)] [[CR][LF]]',
                  u'[01 (1)] ;[ ZORG] [[CR][LF]]',
                  u'[LAST CHUNK] [0 (0)] [[CR][LF]]',
                  u' [Req. Body] (size 18)']
        if sys.version_info[0] < 3:
            # python2
            should.append(u'12345678abcdabcdeZ')
        else:
            should.append(u"b'12345678abcdabcdeZ'"),

        should.append(u' ++++++++++++++++++++++++++++++++++++++')
        should.append(u'')
        should.append(u'---')
        self.assertEqual(should, obtained)

        # 2nd set
        request = (b"GET /bar HTTP/1.0\r\n"
                   b"Host: example.com\r\n"
                   b"Transfer-Encoding: chunked\r\n"
                   b"\r\n"
                   b" 8\r\n"
                   b"12345678\r\n"
                   b"0004\r\n"
                   b"abcd\r\n"
                   b"6\n"
                   b"abcdef\n"
                   b"0\r\n"
                   b"\r\n")

        if sys.version_info[0] < 3:
            # python2
            raw8 = (u'**(raw): 8\\r\\n**'
                    u'**BAD CHUNK < Bad chunk start;>**')
            raw6 = (u"**(raw):6\\n****BAD CHUNK < "
                    u"Line end is LF and not CRLF;>**")
        else:
            raw8 = (u'**(raw):b\' 8\\r\\n\'**'
                    u'**BAD CHUNK < Bad chunk start;>**')
            raw6 = (u"**(raw):b'6\\n'****BAD CHUNK < "
                    u"Line end is LF and not CRLF;>**")
        req = Requests().parse(request)
        obtained = str(req).split(u'\n')
        should = [u'-1 Requests-',
                  u'---',
                  (u'****BAD Request < Has bad Chunk; '
                   u'Has extra Chunk data;>****'),

                  u' [Req. 1st line]',
                  u'[GET]<SP> [/bar]<SP> HTTP/[1][.][0] [[CR][LF]]',

                  u' [Req. Headers]',
                  u'[HOST] [:]<SP> [example.com] [[CR][LF]]',
                  u'[TRANSFER-ENCODING] [:]<SP> [chunked] [[CR][LF]]',

                  u' [Req. Chunks] (4)',
                  raw8,
                  u'[08 (8)] [[CR][LF]]',
                  u'[04 (4)] [[CR][LF]]',
                  raw6,
                  u'[06 (6)] [[LF]]',
                  u'[LAST CHUNK] [0 (0)] [[CR][LF]]',
                  u' [Req. Body] (size 18)']
        if sys.version_info[0] < 3:
            # python2
            should.append(u'12345678abcdabcdef')
        else:
            should.append(u"b'12345678abcdabcdef'"),

        should.append(u' ++++++++++++++++++++++++++++++++++++++')
        should.append(u'')
        should.append(u'---')
        self.assertEqual(should, obtained)
        # TODO: space before size
        # TODO: crap in chunk size

    def test_request_bad_expect(self):
        "Test bad expect rejection message"

        request = (b"GET /foo HTTP/1.0\r\n"
                   b"Host: example.com\r\n"
                   b"Expect: something\r\n"
                   b"\r\n")

        req = Requests().parse(request)
        obtained = str(req).split(u'\n')

        if sys.version_info[0] < 3:
            # python2
            raw = (u'')
        else:
            raw = (u"b''")
        should = [(u'******INVALID Requests STREAM < '
                   u'Has invalid Message;>******'),
                  u'-1 Requests-',
                  u'---',
                  (u'****INVALID Request < Bad Expect Header;'
                   '>****'),

                  u' [Req. 1st line]',
                  u'[GET]<SP> [/foo]<SP> HTTP/[1][.][0] [[CR][LF]]',

                  u' [Req. Headers]',
                  u'[HOST] [:]<SP> [example.com] [[CR][LF]]',
                  u'[EXPECT] [:]<SP> [something] [[CR][LF]]',
                  u' [Req. Body] (size 0)',
                  raw]

        should.append(u' ++++++++++++++++++++++++++++++++++++++')
        should.append(u'')
        should.append(u'---')
        self.assertEqual(should, obtained)

    def test_request_expect_100_continue(self):
        "Test messages for interim responses"

        request = (b"GET /foo HTTP/1.0\r\n"
                   b"Host: example.com\r\n"
                   b"Expect: 100-continue\r\n"
                   b"\r\n")

        req = Requests().parse(request)
        obtained = str(req).split(u'\n')

        if sys.version_info[0] < 3:
            # python2
            raw = (u'')
        else:
            raw = (u"b''")
        should = [u'-1 Requests-',
                  u'---',
                  u' [Req. 1st line]',
                  u'[GET]<SP> [/foo]<SP> HTTP/[1][.][0] [[CR][LF]]',
                  u' [Req. Headers]',
                  u'[HOST] [:]<SP> [example.com] [[CR][LF]]',
                  u'[EXPECT] [:]<SP> [100-continue] [[CR][LF]]',
                  u' [Req. Body] (size 0)',
                  raw]
        should.append(u' ++++++++++++++++++++++++++++++++++++++')
        should.append(u'')
        should.append(u'---')

        response = (b"HTTP/1.1 100 Continue\r\n"
                    b"\r\n"
                    b"HTTP/1.1 204 No Content\r\n"
                    b"\r\n")

        req = Responses().parse(response)
        obtained = str(req).split(u'\n')

        should = [u'-1 Responses-',
                  u'---',
                  u' ** Interim responses detected **',
                  u'',
                  u'INTERIM RESPONSE:',
                  u' [Resp. 1st line]',
                  u'HTTP/[1][.][1] [100] [Continue] [[CR][LF]]',
                  u' [Resp. Headers]',
                  u' [Resp. Body] (size 0)',
                  raw,
                  u' ++++++++++++++++++++++++++++++++++++++',
                  u'',
                  u' [Resp. 1st line]',
                  u'HTTP/[1][.][1] [204] [No Content] [[CR][LF]]',
                  u' [Resp. Headers]',
                  u' [Resp. Body] (size 0)',
                  raw]

        should.append(u' ++++++++++++++++++++++++++++++++++++++')
        should.append(u'')
        should.append(u'---')
        self.assertEqual(should, obtained)
