#!/usr/bin/env python
# -*- coding: utf-8 -*-


class NoServerThreadResponse(Exception):
    pass


class BadServerThreadResponse(Exception):
    pass


class BadEncodingException(Exception):
    pass


# py2 fix
class ConnectionResetError(OSError):
    pass
