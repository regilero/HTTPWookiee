#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
from httpwookiee.http.parser.messages import Messages
from httpwookiee.http.parser.response import Response


class Responses(Messages):

    def __init__(self):
        super(Responses, self).__init__()
        self.name = u'Responses'

    def _getMessage(self):
        return Response()

    def __getattr__(self, item):
        # redirect direct access to responses
        if item is 'responses':
            return self.messages
        else:
            raise AttributeError('unknown {0} attribute'.format(item))
