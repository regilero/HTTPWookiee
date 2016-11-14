#!/usr/bin/env python
# -*- coding: utf-8 -*-


class Order(object):

    action = None
    data = None
    id = None

    ACTION_PING = 0
    ACTION_STOP = 1
    ACTION_CLEANUP = 2
    ACTION_BEHAVIOR = 4

    def __init__(self, action, id=None, data=None):
        self.action = action
        self.data = data
        if id is None:
            self.id = 0
        else:
            self.id = id

    def getAction(self):
        return self.action

    def getData(self):
        return self.data

    def getId(self):
        return self.id

    def __str__(self):
        out = "Order: "
        if Order.ACTION_PING == self.action:
            out += "PING {0}".format(self.id)
        elif Order.ACTION_STOP == self.action:
            out += "STOP {0}".format(self.id)
        elif Order.ACTION_CLEANUP == self.action:
            out += "CLEANUP {0}".format(self.id)
        elif Order.ACTION_BEHAVIOR == self.action:
            out += "BEHAVIOR {0} [[{1}]]".format(self.id, self.data)
        return out
