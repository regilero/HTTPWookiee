#!/usr/bin/env python
# -*- coding: utf-8 -*-


class Version():

    MAJOR = 0
    MINOR = 8
    SUBRELEASE = 0
    STATUS = 'alpha'

    def __str__(self):
        return "HttpWookiee Version {0}.{1}.{2} ({3})".format(
            self.MAJOR,
            self.MINOR,
            self.SUBRELEASE,
            self.STATUS)
