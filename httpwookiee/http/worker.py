#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
from httpwookiee.config import ConfigFactory
from httpwookiee.core.tools import outmsg, inmsg
from httpwookiee.core.behavior import Behavior
from httpwookiee.core.info import Info
from httpwookiee.http.parser.requests import Requests
import re
import socket
import errno
try:
    from builtins import ConnectionResetError
except ImportError:
    from httpwookiee.core.exceptions import ConnectionResetError
# try:
#     import queue as Queue
# except ImportError:
#     import Queue


class Worker(object):

    request = None
    _sock = None
    _addr = None
    name = u''
    ready = True
    output = b''
    test_id = None
    behavior = None
    default_behavior = None
    test_behavior = None
    keepalive = True
    out_queue = None

    def __init__(self, name, out_queue=None):
        self.config = ConfigFactory.getConfig()
        self.name = name
        self.output = b''
        self.stream = b''
        self.keepalive = True
        self._sock = None
        self._sock_accept_reads = False
        self.out_queue = out_queue
        self.initDefaultBehavior()
        self.setReady()

    def setReady(self):
        self.ready = True
        self.keepalive = True
        self.output = b''
        self.stream = b''
        self.test_id = None
        self.test_behavior = None
        self._sock = None
        self._sock_accept_reads = False

    def initDefaultBehavior(self):
        self.default_behavior = Behavior()
        self.default_behavior.setRegularDefaults()

    def init(self, sock, address):
        self.ready = False
        self._sock = sock
        self._addr = address
        self._sock_accept_reads = True

    def close(self):
        if not self.ready:
            # this will also call setReady()
            self.close_socket()

    def inmsg(self, message):
        inmsg(message,
              prefix=u'BACKEND {0}> '.format(self.name),
              color='blue')

    def outmsg(self, message):
        outmsg(message,
               prefix=u'BACKEND {0}> '.format(self.name),
               color='yellow')

    def setTestId(self, id):
        self.test_id = id

    def setTestBehavior(self, behavior):
        self.test_behavior = behavior

    def getTestBehavior(self):
        if self.test_behavior is not None:
            return self.test_behavior
        else:
            self.default_behavior

    def close_socket_for_read(self):
        """Close the server-client socket for reads incoming from client.

        We do not completly close the socket right now to allow late reads
        in the client side. But this socket will soon be closed.
        """
        if self._sock is not None:
            self.outmsg("Closing socket for reads")
            try:
                self._sock.shutdown(socket.SHUT_RD)
            except Exception:
                # already closed
                pass
        self._sock_accept_reads = False

    def close_socket(self):
        if self._sock is not None:
            self.outmsg("Closing socket")
            try:
                self._sock.shutdown(socket.SHUT_RDWR)
            except Exception:
                # already closed
                pass
            try:
                self._sock.close()
            except Exception:
                pass
            self._sock = None
        self.setReady()

    def write_socket(self):
        if self.output is not None and self.output != b'':
            self.outmsg(self.output)
            self._sock.sendall(self.output)
            self.output = b''
            if not self.keepalive:
                self.close_socket_for_read()

    def read_socket(self):
        if not self._sock_accept_reads:
            # This is for sockets that we decided to cut readings from.
            # like after a 0.9 message
            raw = b''
        else:
            try:
                raw = self._sock.recv(self.config.getint(
                    'BACKEND_SOCK_READ_SIZE'))
            except ConnectionResetError:
                # python3
                raw = b''
            except socket.error as serr:
                # python2 support
                if serr.errno != errno.ECONNRESET:
                    # that's another problem
                    raise
                # [Errno 104] Connection reset by peer
                raw = b''
        self.inmsg(str(raw))
        if b'' == raw:
            # that's a closed socket in fact
            # using select() to catch readable sockets will also catch closed
            # sockets (closed by the client). But theses scokets will now
            # always return an empty string content. You cannot have an empty
            # string content from a readable socket if it is not a closed
            # socket.
            # If you do not close this socket right now, then... you will have
            # it in the readable sockets as vitam aeternam.
            self.close_socket()
        else:
            self.stream += raw
            self.requests = Requests().parse(self.stream)

            # DEBUG
            self.inmsg(str(self.requests))

            if self.requests.count > 0:

                self._load_testid_and_behavior()

                if self.behavior.ignore_content_length:

                    # the current response parsing is maybe wrong.
                    self.requests = Requests()
                    self.requests.parse(self.stream,
                                        compute_content_length=False)
                    self.inmsg('# Stream after removing Content Length.')
                    self.inmsg(str(self.requests))

                if self.requests.count > 0:
                    # Remove from input stream the completed requests
                    self._truncate_input_stream()

                    if self.behavior.echo_query:
                        self.echo_query()

                    # we can send a response, query is fully read
                    self.send_responses()

            else:

                self._load_testid_and_behavior(stream_mode=True)

                if self.behavior.echo_incomplete_query:
                    self.echo_input_stream()

    def _load_testid_and_behavior(self, stream_mode=False):
        if (self.test_id is not None and
                self.detect_test_from_requests(stream_mode)):
            self.behavior = self.getTestBehavior()
        else:
            # this is especially usefull for probe requests
            self.behavior = self.default_behavior

    def _truncate_input_stream(self):
        # self.requests.parsed_idx contains the last index reached with
        # a complete message
        self.stream = self.stream[self.requests.parsed_idx:]

    def echo_query(self):
        if self.out_queue is not None:
            self.outmsg('# echoing queries to thread out_queue')
            self.out_queue.put_nowait(Info(Info.INFO_DATA,
                                           id=self.test_id,
                                           data=self.requests))

    def echo_input_stream(self):
        if self.out_queue is not None:
            self.outmsg('# echoing input stream to thread out_queue')
            self.out_queue.put_nowait(Info(Info.INFO_PARTIAL_DATA,
                                           id=self.test_id,
                                           data=self.stream))

    def detect_test_from_requests(self, stream_mode=False):
        "Check in raw first line of requests for an httpwookiee test marker."
        detected = False
        if stream_mode:
            import six
            block = six.text_type(self.stream)
        else:
            block = self.requests[0].first_line.raw.decode('utf8')

        matches = re.match(r'.*httpw=--(.*)--.*',
                           block,
                           re.S)
        if matches:
            request_test_id = matches.group(1)
            if self.test_id == request_test_id:
                detected = True
        return detected

    def send_responses(self):
        """Prepare the responses stream output.
        """
        position = 1
        if self.requests.valid or self.behavior.accept_invalid_request:
            for request in self.requests:
                self.send_ok(request=request)
                if self.requests.count > 1:
                    # add an allowed extra response separator
                    self.output += b"\r\n"
                position = position + 1
                if (self.behavior.add_wookiee_response and
                        position == self.behavior.wookiee_stream_position):
                    self.send_wookiee()
                    # add an allowed extra response separator
                    self.output += b"\r\n"
                # TODO: behavior timer between wookiee and responses?
        else:
            for request in self.requests:
                if request.valid:
                    self.send_ok(request=request)
                    if self.requests.count > 1:
                        # add an allowed extra response separator
                        self.output += b"\r\n"
                else:
                    # even if asked to keep conn alive on errors, we cannot
                    # keep a conn alive after an http/0.9 request
                    # every incoming data is just crap from 1st query
                    close = ((request.http09)
                             or not(self.behavior.keep_alive_on_error))
                    self.send_400(headers=not(request.http09),
                                  close=close)
                    if close:
                        break
                position = position + 1
                if (self.behavior.add_wookiee_response and
                        position == self.behavior.wookiee_stream_position):
                    self.send_wookiee()
                    # add an allowed extra response separator
                    self.output += b"\r\n"

    def send_ok(self,
                headers=True,
                close=False,
                request=None):
        if request is not None:
            wlocation = self.config.get('BACKEND_WOOKIEE_LOCATION')
            # add support for proxies misconfigured, with no prefix path
            # support : TODO: remove
            prewlocation = '{0}{1}'.format(
                self.config.get('BACKEND_LOCATION_PREFIX'),
                self.config.get('BACKEND_WOOKIEE_LOCATION'))
            if (request.first_line.location == wlocation
                    or request.first_line.location == prewlocation):
                return self.send_wookiee()

        body = b"Hello, World!\r\nIt works!\r\n"
        if self.behavior.alt_content:
            body += self.config.get(
                'SERVER_NON_DEFAULT_LOCATION_CONTENT').encode('utf8')
        else:
            body += self.config.get(
                'SERVER_DEFAULT_LOCATION_CONTENT').encode('utf8')
        if headers:
            self.output += b"HTTP/1.1 200 OK\r\n"
            self.output += b"Content-Length: "
            self.output += str(len(body)).encode('ascii')
            self.output += b"\r\n"
            self.output += b"Content-Type: text/html; charset=utf-8\r\n"
            if close:
                self.output += b"Connection: Close\r\n"
            else:
                self.output += b"Connection: keep-alive\r\n"
            self.output += b"\r\n"
        self.output += body
        if close:
            self.keepalive = False

    def send_400(self, headers=True, close=True):
        if headers:
            self.output += b"HTTP/1.1 400 Bad Request\r\n"
            self.output += b"Content-Type: text/html; charset=utf-8\r\n"
            if close:
                self.output += b"Connection: Close\r\n"
            else:
                self.output += b"Connection: keep-alive\r\n"
            self.output += b"Content-Length: 24\r\n"
            self.output += b"\r\n"
        if close:
            self.keepalive = False
        self.output += b"400, Bad Request. GFY!\r\n"

    def send_wookiee(self, headers=True, close=False):
        wookiee = b"""<html><body>Wookiee !<hr/><pre>
       .             ``.--::-.`          //      //     .      || ||    .   .
                . `-+hdmNNNNNmdys/.     |||. || |||   .        ||//  ||
         .     .:sdNMMMMMMMMMMMMMNdo:`` ||| ||| ||| //]]  //]] || [[   /||]/||]
              :dMMMMMMMMMMMMMNNMNmNho:-:`|||| |||||||  ||||  ||||  [[|||[  |[
     .       +mMMMMMNmNNNMMNydMh+ydo:../o |||  |||  [[//  [[// ||  [[||[[//[[//
           `+MMMMMMMMmyddNdh/No/hdhssys+o+.                .
           oNMMMMMMMMNs/ymdsso-yd/::/yhdds/`                             .
          -NMMMNNNMMNNh-oNmhy:hs:..```.-/ss/.       .      .
         `sMMMMNNhymNNm:+mmd/yd+:--:/oshdys-.
  +      -mMMNNdhdmhyhNs/mmy+mmyyy+shdo/-....
         +MMmddmmNNNmdmdommyyMmho:shs/:-.````.:`        .
         +NMNNdyyysdmmNNmMNdmMm:+dy/:-::-..-../:                        .
    .   `yNNmmdddmdysdmmMMMNMMsody/+/-:/+//.```.-
        :h+:/+syhdmNNmdhmMdNMMmmhsosyddhyo+o/.` .`
       `/+/sddddmdmNNmMNmNh+ymdo/yNMMNhso++`-```                 .
       `/hhmhyhdNMdho+NMmdho/oyhdymMMmy+/:s+.`                 .  .
  .    .sNNNh+smMMMMMMdymNMNms/ohdmdhhyo+ossy:     .             +       .
       .sNNNddmdmNNMMdymMNNhhNmo/oo+/-/hyyhhoo``
       `ohdMMNmso+sNMdNMMMMMMMmyss+--+o::hNNs/.s-                 .
        /ohMMNds-+dmhymmNmNMNho/odmddyyd:omdoy+s-         .
       `::dNNNd+/dNNMNmhNdhdyhhhhhhhNMyhs/y/s+:+.
    .   `/mhdmdshdMNmm++yoooohys+/hmNMoydmo`-s+:`                 .
         smymNdyooNNNNddhddyysys+hmydMy:hho- sm.``/ooo:.
        `hhNNmdo/hmhhmmNmNNmh/ymd+:ohMNyoyy+`sm`- .hNMNs. `-+:-         .
   ``.-:/mdMNmh++dNddddh+hmod+/ohdy/oymNmmdy:oN-s.::sNy--ossho:`..`
`-+hdmNMdNmMmmhoodNshmNmommsyNs//ymmdyohMMMmo+m+Mh:soms/mMMm/`---`+yo.
hNMNmmMMmNdMNmmyyddsshyddhydodmhhso+hmd+mNmyo:hdMm-yNMMNMMNs.:h::sdMNo:
mMmdmMMMNmmdmNhmmhsy+yyhNy+my+Nhhy+:/sNohdshy`ydN+ `sMMMMNNdmmNdNMmhho+/`
MMMMMMMMMmdmhmMNmho::hyhm+:hssm+yNs:/ddshsdoo.yho+./mMMm/-+hNMMMMMMNdoo+o.
MMMMMMMMMNmddyNMd+-.+hsmy-:hohh:mm//shsdoyM+oydsydydmmm- ./-sMMMMMMMMms/oo`
MMMMMMMNMMNymmNmo/:-:+dms:ooshshNs+yh/mhmMNNymmyMMMMMMNo+ho/mMMMMMMMMNms/h:
MMMMMMNMMMddNMNs+/-/ssdmyosodydMdohNsoNNMMMMMy-:dMMMMMMMMMdMMMMMMMNMMMdys+/:
MMMMNmNMMNNNMMMdsosoomNyhdshymNNosNdyyhmMMMMy` -mmhmdmNMMMMMMMMMMNmNMMNmssoo.
MMMMmNMMMNMNMMMNshyoNMMNMNyyNMMNhyMdhNMNMMMdo`:mMMMo` -hMMMMMMMMMMNmMMmmm/:ho
MMMNmMMMMMMMMMMdyNsdNMMMMMNdmMMMmsNMMMMMMMMmmNMNNN+`:.-hMMMMMMMMMMdmNMNdMms/d/
MMMNMMMMMMNMMMMNhdmdMMMMMMMNNNMMNydNMMMMMMMMMMMMmy.s+-hMMMMMMMMMMMmhNMMdNMmyy+`
</pre></html></body>"""
        if headers:
            self.output += b"HTTP/1.1 200 OK\r\n"
            self.output += b"Content-Length: "
            self.output += str(len(wookiee)).encode('ascii')
            self.output += b"\r\n"
            self.output += b"Content-Type: text/html; charset=utf-8\r\n"
            self.output += b"X-Wookiee: True\r\n"
            if close:
                self.output += b"Connection: Close\r\n"
            else:
                self.output += b"Connection: keep-alive\r\n"
            self.output += b"\r\n"
        if close:
            self.keepalive = False

        self.output += wookiee
