#!/usr/bin/env python
# -*- coding: utf-8 -*-


class Info(object):

    status = None
    data = None
    id = None

    INFO_PONG = 0
    INFO_OK = 1
    INFO_REJECT = 2
    INFO_DONE = 3
    INFO_DATA = 4
    INFO_PARTIAL_DATA = 5

    def __init__(self, status, id=None, data=None):
        self.status = status
        self.data = data
        if id is None:
            self.id = 0
        else:
            self.id = id

    def getStatus(self):
        return self.status

    def getId(self):
        return self.id

    def getData(self):
        return self.data

    def __str__(self):
        out = "Info: "
        if Info.INFO_PONG == self.status:
            out += "PONG"
        elif Info.INFO_OK == self.status:
            out += "OK"
        elif Info.INFO_REJECT == self.status:
            out += "REJECTED"
        elif Info.INFO_DONE == self.status:
            out += "DONE"
        elif Info.INFO_DATA == self.status:
            out += "DATA! [[{0}]]".format(self.data)
        elif Info.INFO_PARTIAL_DATA == self.status:
            out += "PARTIAL DATA! [[{0}]]".format(self.data)
        return out
