#!/usr/bin/env python
# -*- coding: utf-8 -*-


class Behavior(object):

    accept_invalid_request = None
    add_wookiee_response = None
    keep_alive_on_error = None
    wookiee_stream_position = None
    ignore_content_length = None
    echo_query = None
    echo_incomplete_query = None
    alt_content = None

    def __init__(self):
        self.accept_invalid_request = False
        self.add_wookiee_response = False
        # note that having pos 1 makes no sense
        self.wookiee_stream_position = 2
        self.keep_alive_on_error = False
        self.ignore_content_length = False
        self.echo_query = False
        self.echo_incomplete_query = False
        self.alt_content = False

    def setRegularDefaults(self):
        "Settings for a regular HTTP server."
        self.accept_invalid_request = False
        self.add_wookiee_response = False
        self.keep_alive_on_error = False
        self.ignore_content_length = False
        self.echo_query = False
        self.echo_incomplete_query = False
        self.alt_content = False

    def __str__(self):
        out = "Behavior: \n"
        if self.accept_invalid_request:
            out += " * Accept INVALID Request\n"
        if self.keep_alive_on_error:
            out += " * Keep conn alive on errors\n"
        if self.ignore_content_length:
            out += " * Ignore Content-Length headers\n"
        if self.add_wookiee_response:
            out += " * Add Wookiee Response (pos {0})\n".format(
                self.wookie_stream_position)
        if self.echo_query:
            out += " * Echo query to thread message canal\n"
        if self.echo_incomplete_query:
            out += " * Echo Incomplete query stream to thread message canal\n"
        if self.alt_content:
            out += " * ok response contains non default expected content\n"
        return out
