#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
from httpwookiee.http.parser.messages import Messages
from httpwookiee.http.parser.response import Response


class Responses(Messages):

    # ERROR_HAS_INVALID_INTERIM = 'Has invalid Interim Response'
    # ERROR_HAS_BAD_INTERIM = 'Has bad Interim Response'

    def __init__(self):
        super(Responses, self).__init__()
        self.name = u'Responses'
        self.interim_responses = []

    def _getMessage(self):
        return Response()

    def __getattr__(self, item):
        # redirect direct access to responses
        if item is 'responses':
            return self.messages
        else:
            raise AttributeError('unknown {0} attribute'.format(item))

    def check_message_status(self, msg):
        if msg is not False:
            if msg.is_interim_response():
                self.interim_responses.append(msg)
                # if not msg.valid:
                #     # print(msg)
                #     self.setError(self.ERROR_HAS_INVALID_INTERIM)
                # elif msg.error:
                #     # print(msg)
                #     self.setError(self.ERROR_HAS_BAD_INTERIM, critical=False)
            else:
                if len(self.interim_responses) > 0:
                    # stacked Interim responses goes to this real message
                    msg.interim_responses = list(self.interim_responses)
                    self.interim_responses = []

                self.count = self.count + 1
                self.messages.append(msg)
                if not msg.valid:
                    # print(msg)
                    self.setError(self.ERROR_HAS_INVALID_MESSAGE)
                elif msg.error:
                    # print(msg)
                    self.setError(self.ERROR_HAS_BAD_MESSAGE, critical=False)
            self.parsed_idx = self.byteidx
        else:
            self.setError(self.ERROR_HAS_INVALID_MESSAGE)
