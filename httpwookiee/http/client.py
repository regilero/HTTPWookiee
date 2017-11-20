#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
from httpwookiee.config import ConfigFactory
from httpwookiee.core.tools import Tools, outmsg, inmsg
from httpwookiee.http.parser.responses import Responses

import socket
import ipaddress

import ssl
import six


class ClosedSocketError(Exception):
    """Raise this when the tcp/ip connection is unexpectedly closed."""


class Client(object):
    """Main HTTP Client, HTTP request launcher."""

    hostip = None
    port = None
    host = b''
    https = False
    _sock = None
    _hostip = False

    def __init__(self, host=None, port=None, hostip=None):
        """Ensure settings are ready."""
        self.config = ConfigFactory.getConfig()
        if host is None:
            self.host = self.config.get('SERVER_HOST')
        else:
            self.host = host

        if port is None:
            self.port = self.config.getint('SERVER_PORT')
        else:
            self.port = port

        self.hostip = hostip
        if self.hostip is None and '' != self.config.get('SERVER_IP'):
            self.hostip = self.config.get('SERVER_IP')

        self.https = self.config.getboolean('SERVER_SSL')
        self._sock = None

    def __enter__(self):
        """Launch the socket opening."""
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Send a socket close."""
        return self.close()

    def open(self):
        """Open client socket connection."""
        if self.hostip is None:
            outmsg('# searching host IP (DNS) for {0} '.format(self.host))
            self.hostip = socket.getaddrinfo(self.host, self.port)[0][4][0]
        self._ci()

        try:
            if not self._hostip:
                raise Exception(u'\u0262\u0046\u0059')
            outmsg(
                '# Connecting to Host: {0} IP: {1} PORT: {2}'.format(
                    self.host, self.hostip, self.port))
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock.settimeout(10)
        except socket.error as msg:
            outmsg("[ERROR] {0}".format(str(msg)))
            raise Exception('error creating socket')

        outmsg('# socket ok')

        if self.https:
            try:

                outmsg('# Establishing SSL layer')
                self._sock = ssl.wrap_socket(self._sock,
                                             cert_reqs=ssl.CERT_NONE)
            except Exception:
                outmsg("[SSL ERROR]")
                raise Exception('error establishing SSL connection')

        try:
            self._sock.connect((self.hostip, self.port))
        except socket.error as msg:
            outmsg("[ERROR] {0}".format(str(msg)))
            raise Exception('error establishing socket connect')
        outmsg('# client connection established.')

    def close_sending(self):
        """First closing step, cut the sending part of the socket."""
        try:
            outmsg('# closing client connection send canal '
                   '(can still receive).')
            self._sock.shutdown(socket.SHUT_WR)
        except OSError:
            raise ClosedSocketError('closed socket detected on send close')

    def close(self):
        """Ensure the tcp/ip socket is really closed."""
        if self._sock is not None:
            outmsg('# closing client connection.')
            try:
                self._sock.shutdown(socket.SHUT_RDWR)
            except Exception:
                # already closed
                pass
            self._sock.close()
            self._sock = None

    def _ci(self):
        self._hostip = ipaddress.ip_address(self.hostip).is_private

    def send(self, request):
        """Send given request on the socket, support delayed emission."""
        msg = request.getBytesStream()
        msglen = len(msg)
        outmsg('# SENDING ({0}) =====>'.format(msglen))
        # here we use the not-so real format (special bytes are not
        # replaced in str(), only in getBytesStream())
        Tools.print_message(six.text_type(request), cleanup=True)
        try:
            self._socket_send(msg)
        except socket.error as errmsg:
            outmsg('#<====ABORTED COMMUNICATION WHILE'
                   ' SENDING {0}\n#{1}'.format(six.text_type(msg), errmsg))
            return
        while request.is_delayed:
            msg = request.getDelayedOutput()
            msglen = len(msg)
            outmsg('# SENDING Delayed ({0}) =====>'.format(msglen))
            # hopefully we do not use strange bytes in delayed chunks for now
            Tools.print_message(six.text_type(msg), cleanup=True)
            try:
                self._socket_send(msg)
            except socket.error as errmsg:
                outmsg('#<====ABORTED COMMUNICATION WHILE'
                       ' SENDING (delayed) '
                       '{0}\r\n#{1}'.format(six.text_type(msg),
                                            errmsg))
                return

    def read_all(self, timeout=None, buffsize=None, requests_infos=None):
        """Read all the stream, waiting for EOS, return all responses."""
        output = ''
        if timeout is None:
            timeout = float(self.config.getint(
                'CLIENT_SOCKET_READ_TIMEOUT_MS'))
            timeout = timeout / 1000
        if buffsize is None:
            buffsize = self.config.getint('CLIENT_SOCKET_READ_SIZE')
        try:
            output = self._socket_read(timeout, buffsize)

        except socket.error as msg:
            inmsg('#<====ABORTED RESPONSE WHILE READING: {0}'.format(str(msg)))

        inmsg('# <====FINAL RESPONSE===============')
        inmsg(output)
        responses = Responses().parse(output, requests_infos=requests_infos)
        return responses

    def _socket_send(self, message):
        msglen = len(message)
        totalsent = 0

        outmsg('# ====================>')

        while totalsent < msglen:
            outmsg('# ...')
            sent = self._sock.send(message[totalsent:])
            if sent == 0:
                raise RuntimeError("socket connection broken")
            totalsent = totalsent + sent

    def _socket_read(self, timeout, buffsize):

        inmsg('# <==== READING <===========')
        read = b''

        # we use blocking socket, set short timeouts if you want
        # to detect end of response streams
        if 0 == timeout:
            self._sock.settimeout(None)
        else:
            self._sock.settimeout(timeout)

        try:

            # blocking read
            data = self._sock.recv(buffsize)
            while (len(data)):
                inmsg('# ...')
                read += data
                data = self._sock.recv(buffsize)
        except socket.timeout:
            inmsg('# read timeout({0}), nothing more is coming'.format(
                timeout))
        return read
