FAQ
=====

Can I run only a subset of the tests
-------------------------------------

Yes, you can either directly run a test script (one of :code:`httpwookiee/client/tests*`
or :code:`httpwookie/server/tests*` files), or use :code:`-m` and :code:`-M`
options on :code:`httpwookiee.py` to filter on tests files names or test class
names (respectively).

This is higly recommended.

You have the  :code:`-t` switch to limit execution of tests by numbers.

Do not hesitate, also, to run the scripts with :code:`-V` (verbose output) and
:code:`-n` (no cache mode, direct output), especially
on the first tests, to ensure everything works as excepted (server is
responding, expected content can be found, you used the right hostname, etc).

There're a lot of files, where do I start, where are the *fuzz* scripts?
------------------------------------------------------------------------

Real fuzzing stuff, used to test HTTP servers and ReverseProxy are in
:code:`./httpwookie/client/tests_*.py` (for the server-test stuff) and
:code:`./httpwookie/server/tests_*.py` (for the Reverse Proxy stuff, where
this script is both the client side and the final backend side).

If you do not see any files there (or not many) it's because most of the tests
are not yet published.
This can happen when we wait for security fixs on the vendor side.
Usually some other scripts can be
found on :code:`./httpwookie/staging/[client|server]/tests_*.py`, but maybe not
on the public release.

If you want to read some interesting stuff, you may look at the :code:`tests`
subdirectory, where you can find the internal tests of this program, the
:code:`http/parser` stuff, with an implementation of an HTTP server where most
HTTP errors are analyzed (or that's the goal, at least).

Check also the docker tests on the test subdirectory, teher's a section on the
README for usage.

It's not working, it states, 'read the FAQ'
--------------------------------------------

Yes, there is a settings that must be set in your configuration file.

Read the Warning section on the Readme.rst file.

Help me understand the debug output
------------------------------------

So here's a commented output::

    name & class of  | [test_crlf_line_prefix] (httpwookiee.server.tests_first_line.TestCarriageReturnFirstLineProxy)
    the test & status|   .............................................................................. ... --> =None=
    ---- Initial Setup of the Test --------------
    First our backend| <-- BACKEND> order received Order: CLEANUP hfmoko
    HTTP Server rece-| <-- BACKEND> order received Order: BEHAVIOR hfmoko [[Behavior:
    -ive his conf.   |  * Accept INVALID Request
                     |  * Keep conn alive on errors
                     |  * Echo query to thread message canal
                     | ]]
    Then the HTTP    | --> # Connecting to Host: dummy-host2.example.com IP: 127.0.0.1 PORT: 8081
    client establish | --> # socket ok
    TCP/IP conn.     | --> # client connection established.
    ----- Now starting to send/receive-----------
                     | --> # SENDING (226) =====>
    That's the 'bad' | --> [CR][LF]
    query sent.      | GET /proxy/?khihbm=cgip3b&httpw=--jdc4ch-- HTTP/1.1[CR][LF]
    In this example  | X-Block-Me: please @ spambot_irc + select union[CR][LF]
    just a \r\n set  | User-Agent: script-httpwookiee @ spambot_irc + select union[CR][LF]
    before the query.| X-Wookiee: 139722243628280[CR][LF]
    This is allowed  | Host: dummy-host2.example.com[CR][LF]
    by the RFC.      | [CR][LF]
                     |
    - socket send    | --> # ====================>
      (loop, if msg  | --> # ...
      is big)        | --> # ...
    - socket read    | <-- # <==== READING <===========
    ----- receiving something on the backend side ----
    - backend proc   | <-- BACKEND> # New Connection from ('127.0.0.1', 47818) assigned to WRK1
    - raw query      | <-- BACKEND WRK1> b'GET /proxy/?khihbm=cgip3b&httpw=--jdc4ch-- HTTP/1.1\r\nHost: 127.0.0.1:8282\r\nX-Block-Me: please @ spambot_irc + select union\r\nUser-Agent: script-httpwookiee @ spambot_irc + select union\r\nX-Wookiee: 139722243628280\r\nX-Forwarded-For:     127.0.0.1\r\nX-Forwarded-Host:               | dummy-host2.example.com\r\nX-Forwarded-Server: dummy-host2.example.com\r\nConnection: Keep-Alive\r\n\r\n'
    - Analyze raw qry| [GET]<SP> [/proxy/]?[khihbm=cgip3b&httpw=--jdc4ch--]<SP> HTTP/[1][.][1] [[CR][LF]]
    and extract      |  [Req. Headers]
    tokens as well as| [HOST] [:]<SP> [127.0.0.1:8282] [[CR][LF]]
    various syntax   | [X-BLOCK-ME] [:]<SP> [please<SP>@<SP>spambot_irc<SP>+<SP>select<SP>union] [[CR][LF]]
    errors (critical | [USER-AGENT] [:]<SP> [script-httpwookiee<SP>@<SP>spambot_irc<SP>+<SP>select<SP>union] [[CR][LF]]
    or not). This is | [X-WOOKIEE] [:]<SP> [139722243628280] [[CR][LF]]
    received by our  | [X-FORWARDED-FOR] [:]<SP> [127.0.0.1] [[CR][LF]]
    server thread,   | [X-FORWARDED-HOST] [:]<SP> [dummy-host2.example.com] [[CR][LF]]
    incoming from the| [X-FORWARDED-SERVER] [:]<SP> [dummy-host2.example.com] [[CR][LF]]
    tested reverse   | [CONNECTION] [:]<SP> [Keep-Alive] [[CR][LF]]
    proxy.           |  [Req. Body] (size 0)
                     | b''
                     |  ++++++++++++++++++++++++++++++++++++++
                     |
    - backend now    | ---
    sending a        | --> BACKEND WRK1> # echoing queries to thread out_queue
    response:        | --> BACKEND WRK1> HTTP/1.1 200 OK
    (content depends | Content-Length: 26
    on behavior defi-| Content-Type: text/html; charset=iso-8859-1
    -ned on the test | Connection: keep-alive
    initialization   |
                     | Hello, World!
                     | It works!
                     |
    ----- read loop on client side ----
    - read loop      | <-- # ...
                     | <-- # ...
    - read end       | <-- # read timeout(0.2), nothing more is coming
                     | <-- # <====FINAL RESPONSE===============
    - raw response   | <-- HTTP/1.1 200 OK
    from tested      | Date: Mon, 22 Aug 2016 13:43:08 GMT
    proxy.           | Server: Apache/2.5.0-dev (Unix)
                     | Content-Length: 26
                     | Content-Type: text/html; charset=iso-8859-1
                     |
                     | Hello, World!
                     | It works!
                     |
    ----- backend to client (echo) ----
    - Analyze of  re-| <-- -1 Requests-
    -quest transmited| ---
    from backend     |  [Req. 1st line]
    thread to the    | [GET]<SP> [/proxy/]?[khihbm=cgip3b&httpw=--jdc4ch--]<SP> HTTP/[1][.][1] [[CR][LF]]
    main script.     |  [Req. Headers]
    So the script can| [HOST] [:]<SP> [127.0.0.1:8282] [[CR][LF]]
    check for potent-| [X-BLOCK-ME] [:]<SP> [please<SP>@<SP>spambot_irc<SP>+<SP>select<SP>union] [[CR][LF]]
    -ial transmission| [USER-AGENT] [:]<SP> [script-httpwookiee<SP>@<SP>spambot_irc<SP>+<SP>select<SP>union] [[CR][LF]]
    of the bad syntax| [X-WOOKIEE] [:]<SP> [139722243628280] [[CR][LF]]
    or detect any    | [X-FORWARDED-FOR] [:]<SP> [127.0.0.1] [[CR][LF]]
    other error.     | [X-FORWARDED-HOST] [:]<SP> [dummy-host2.example.com] [[CR][LF]]
                     | [X-FORWARDED-SERVER] [:]<SP> [dummy-host2.example.com] [[CR][LF]]
                     | [CONNECTION] [:]<SP> [Keep-Alive] [[CR][LF]]
                     |  [Req. Body] (size 0)
    No transmission  | b''
    of errors here.  |  ++++++++++++++++++++++++++++++++++++++
                     |
    ----- end of client side read/write socket ----
                     | ---
    - end of client  | --> # closing client connection.
    socket           | --> -1 Responses-
                     | ---
    - Analyze of     |  [Resp. 1st line]
    response(s).     | HTTP/[1][.][1] [200] [OK] [[CR][LF]]
                     |  [Resp. Headers]
                     | [DATE] [:]<SP> [Mon,<SP>22<SP>Aug<SP>2016<SP>13:43:08<SP>GMT] [[CR][LF]]
                     | [SERVER] [:]<SP> [Apache/2.5.0-dev<SP>(Unix)] [[CR][LF]]
                     | [CONTENT-LENGTH] [:]<SP> [26] [[CR][LF]]
                     | [CONTENT-TYPE] [:]<SP> [text/html;<SP>charset=iso-8859-1] [[CR][LF]]
                     |  [Resp. Body] (size 26)
                     | b'Hello, World!\r\nIt works!\r\n'
                     |  ++++++++++++++++++++++++++++++++++++++
                     |
    result of        | ---
    analysis and test| -accepted-    [ok]
    final status.    |
