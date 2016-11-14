#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Internal Tests
#
from httpwookiee.core.base import BaseTest
from httpwookiee.core.tools import Tools
# from httpwookiee.core.exceptions import BadEncodingException


class Test_Internal_Server(BaseTest):

    def test_wookiee(self):
        wlocation = self.get_wookiee_location()
        self.req.set_location(wlocation, random=True)
        self._end_almost_regular_query()
        self.assertEqual(self.status,
                         self.STATUS_WOOKIEE,
                         'Wookiee response is Expected, strange.')

    def test_bad_utf8(self):
        dlocation = '{0}&{1}{2}=badutf8'.format(self.get_default_location(),
                                                Tools.BYTES_SPECIAL_REPLACE,
                                                Tools.BYTES_SPECIAL_REPLACE)
        self.req.record_bytes_to_send(Tools.UTF8_OVERLONG_CR)
        self.req.record_bytes_to_send(Tools.UTF8_OVERLONG_LF)
        self.req.set_location(dlocation, random=True)
        self._end_expected_error()
