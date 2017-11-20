#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
from httpwookiee.config import ConfigFactory
from httpwookiee.core.tools import Tools, get_rand
from httpwookiee.core.exceptions import BadEncodingException
from time import sleep
import six


class Request:

    def __init__(self, wookiee_id=0, host=None):
        self.config = ConfigFactory.getConfig()
        self.headers = [{
            'name': u'\u0058\u002d\u0042\u006c\u006F' +
                    u'\u0063\u006b\u002d\u004d\u0065',
            'value': u'\u0070l\u0065\u0061\u0073\u0065' +
                     u'\x20@ spambot_irc + select union',
            'sep': u': ',
            'eol': Tools.CRLF}]
        self.wookiee_id = wookiee_id
        if host is not None:
            self.host = host
        else:
            self.host = self.config.get('SERVER_HOST')
        self.first_line_prefix = u''
        self.method = u'GET'
        self.method_sep = Tools.SP
        self.location = self.config.get('SERVER_DEFAULT_LOCATION')
        self.has_query_string = False
        self.query_string = u''
        self.location_sep = Tools.SP
        self.protocol = u'HTTP'
        self.protocol_sep = u'/'
        self.version_09 = False
        self.version_major = u'1'
        self.version_sep = u'.'
        self.version_minor = u'1'
        self.first_line_suffix = u''
        self.first_line_eof = Tools.CRLF
        self.body = u''
        self.chunks = []
        self.chunked = False
        self.end_of_chunks = True
        self.suffix = u''  # Tools.CRLF
        self.add_host = True
        self.add_header(u'User-Agent',
                        u'script-httpwookiee @ spambot_irc + select union')
        self.add_header(u'X-Wookiee',
                        str(self.wookiee_id))
        self.crop_rendering = False
        self.is_delayed = False
        self.delayed = []
        self.delayed_parsed = False
        self._strange_bytes_records = []

    def set_method(self, method):
        self.method = method

    def set_method_sep(self, separator):
        self.method_sep = separator

    def set_location_sep(self, separator):
        self.location_sep = separator

    def set_first_line_prefix(self, content):
        self.first_line_prefix = content

    def set_first_line_suffix(self, content):
        self.first_line_suffix = content

    def set_http_version(self, major=1, minor=1, force=False):
        if major == 0 and minor == 9 and not force:
            self.version_09 = True
        else:
            self.set_major_version(major)
            self.set_minor_version(minor)

    def set_major_version(self, content):
        self.version_major = content

    def set_minor_version(self, content):
        self.version_minor = content

    def add_suffix(self, content):
        self.suffix += content

    def add_argument(self, name, value):
        self.has_query_string = True
        sep = u'&'
        if self.query_string == u'':
            sep = u''
        self.query_string += u'{0}{1}={2}'.format(sep, name, value)

    def set_location(self, location, random=False):
        self.location = location
        if random:
            self.add_argument(get_rand(), get_rand())

    def add_chunk(self,
                  chunk_body,
                  chunk_size=None,
                  chunk_sep=u';',
                  chunk_ext=u'',
                  chunk_header_eol=Tools.CRLF,
                  chunk_eol=Tools.CRLF):
        self.chunked = True
        if chunk_size is None:
            chunk_size = len(chunk_body)
            chunk_size = hex(chunk_size)[2:]
        if chunk_ext == u'':
            chunk_sep = u''
        record = {u'size': chunk_size,
                  u'delayed': False,
                  u'sep': chunk_sep,
                  u'ext': chunk_ext,
                  u'header_eol': chunk_header_eol,
                  u'body': chunk_body,
                  u'eol': chunk_eol}
        self.chunks.append(record)

    def add_delayed_chunk(self,
                          chunk_body,
                          chunk_size=None,
                          chunk_sep=u';',
                          chunk_ext=u'',
                          chunk_header_eol=Tools.CRLF,
                          chunk_eol=Tools.CRLF,
                          delay=1):
        self.chunked = True
        if chunk_size is None:
            chunk_size = len(chunk_body)
            chunk_size = hex(chunk_size)[2:]
        if chunk_ext == u'':
            chunk_sep = u''
        record = {u'delay': delay,
                  u'delayed': True,
                  u'size': chunk_size,
                  u'sep': chunk_sep,
                  u'ext': chunk_ext,
                  u'header_eol': chunk_header_eol,
                  u'body': chunk_body,
                  u'eol': chunk_eol}
        self.is_delayed = True
        self.chunks.append(record)

    def mangle(self):
        "Remove all but first line, and even first line EOL."
        self.crop_rendering = True

    def _render_first_line(self):
        if self.has_query_string:
            location = "{0}?{1}".format(self.location, self.query_string)

        if self.version_09:
            out = u'{0}{1}{2}{3}{4}'.format(self.first_line_prefix,
                                            self.method,
                                            self.method_sep,
                                            location,
                                            self.first_line_suffix)
        else:
            out = u'{0}{1}{2}{3}{4}'.format(self.first_line_prefix,
                                            self.method,
                                            self.method_sep,
                                            location,
                                            self.location_sep)
            out += u'{0}{1}{2}{3}{4}{5}'.format(self.protocol,
                                                self.protocol_sep,
                                                self.version_major,
                                                self.version_sep,
                                                self.version_minor,
                                                self.first_line_suffix)
        out += self.first_line_eof
        return out

    def add_header(self,
                   name,
                   value,
                   sep=u': ',
                   eol=Tools.CRLF,
                   replace=False):
        record = {'name': name,
                  'sep': sep,
                  'value': value,
                  'eol': eol}
        if replace:
            found = False
            for index, header in enumerate(self.headers):
                if header['name'] == name:
                    found = True
                    self.headers[index] = record
            if not found:
                self.headers.append(record)
        else:
            self.headers.append(record)

    def _render_body(self):
        out = u''
        if not self.chunked:
            out += self.body
        else:
            for chunk in self.chunks:
                chk = u'{0}{1}{2}{3}{4}{5}'.format(chunk[u'size'],
                                                   chunk[u'sep'],
                                                   chunk[u'ext'],
                                                   chunk[u'header_eol'],
                                                   chunk[u'body'],
                                                   chunk[u'eol'])
                if not chunk[u'delayed']:
                    out += chk
            if not self.is_delayed:
                out += self._render_last_chunk()
        return out

    def _render_last_chunk(self):
        out = u''
        # TODO : custom last chunk + also Trailers
        if self.end_of_chunks:
            out += u'0{0}{1}'.format(Tools.CRLF, Tools.CRLF)
        return out

    def _parse_delayed(self):
        if not self.delayed_parsed:
            if self.chunked:
                for chunk in self.chunks:
                    if chunk[u'delayed']:
                        chk = u'{0}{1}{2}{3}{4}{5}'.format(
                            chunk[u'size'],
                            chunk[u'sep'],
                            chunk[u'ext'],
                            chunk[u'header_eol'],
                            chunk[u'body'],
                            chunk[u'eol'])
                        self.delayed.append((chunk[u'delay'], chk))
            self.delayed.reverse()
            self.delayed_parsed = True

    def _render_headers(self):
        out = u''

        if not self.crop_rendering:
            for header in self.headers:
                out += self._render_header(header)
            # headers separator
            out += Tools.CRLF
        else:
            out += u'Mangle: nocrlf'
        return out

    def _render_header(self, header):
        out = header['name']
        out += header['sep']
        out += header['value']
        out += header['eol']
        return out

    def __str__(self):
        "Render request String, as a valid python String"
        if self.add_host:
            self.add_header(u'Host', self.host, replace=True)

        out = self._render_first_line()

        out += self._render_headers()

        if not self.crop_rendering:

            out += self._render_body()

            out += self.suffix

        return out

    def record_bytes_to_send(self, sbytes):
        for sbyte in [sbytes[i:i + 1] for i in range(len(sbytes))]:
            self._strange_bytes_records.append(sbyte)

    def getBytesStream(self):
        "Render request String, but as bytes, which may contain invalid stuff"
        ustr = six.text_type(self)
        # from there we might be able to extract it as full ascii
        try:
            out = ustr.encode('ascii')
        except UnicodeEncodeError:
            # If we try to use characters which transletes to multy bytes chars
            # we'll need to fix the size computations.
            # There's a system in place which allows perfect binary crap for
            # multibytes using BYTES_SPECIAL_REPLACE & record_bytes_to_send,
            # this allows strange multibytes that a regular .encode('utf-8')
            # would not allow.
            raise BadEncodingException('Our requests should only '
                                       'use ascii or binary specific tricks.')
        # Now replace the strange bytes
        for sbyte in self._strange_bytes_records:
            if six.PY2:
                out = out.replace(six.binary_type(Tools.BYTES_SPECIAL_REPLACE),
                                  sbyte,
                                  1)
            else:
                out = out.replace(six.binary_type(Tools.BYTES_SPECIAL_REPLACE,
                                                  'ascii'),
                                  sbyte,
                                  1)
        return out

    def getDelayedOutput(self):
        "render delayed chunks as bytes"

        self._parse_delayed()
        if len(self.delayed) > 0:
            (delay, out) = self.delayed.pop()
        if len(self.delayed) == 0:
            out += self._render_last_chunk()
            self.is_delayed = False
        sleep(delay)
        # FIXME: add support for BYTES_SPECIAL_REPLACE in delayed chunks?
        # FIXME: yes, currently we are stuck with ascii on bodies, we do not
        # handle our requests bodies as real binary streams
        out = six.binary_type(out, 'ascii')
        return out
