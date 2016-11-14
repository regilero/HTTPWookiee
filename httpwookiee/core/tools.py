#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
from httpwookiee.config import ConfigFactory
import sys
import random
from termcolor import cprint


class Tools:

    CR = u"\r"
    URLE_CR = u'%OD'
    LF = u"\n"
    URLE_LF = u'%OA'
    CRLF = u"\r\n"
    URLE_CRLF = u'%OD%OA'
    TAB = u"\t"
    URLE_TAB = u'%09'
    VTAB = u"\v"  # \x0b vertical tab
    URLE_VTAB = u'%0B'
    FF = u"\f"    # \x0c FormFeed
    URLE_FF = u'%0C'
    BEL = u"\a"   # Bell
    URLE_BEL = u'%07'
    BS = u"\b"    # BackSpace
    URLE_BS = u'%08'
    SP = u" "
    URLE_SP = u'%20'
    NULL = u'\x00'
    URLE_NULL = u'%00'

    # Unicode line breaks
    # 000A    LF  LINE FEED                   Cc  B
    # 000D    CR  CARRIAGE RETURN             Cc  B
    # 001C    FS  INFORMATION SEPARATOR FOUR  Cc  B (UCD 3.1 FILE SEPARATOR)
    # 001D    GS  INFORMATION SEPARATOR THREE Cc  B (UCD 3.1 GROUP SEPARATOR)
    # 001E    RS  INFORMATION SEPARATOR TWO   Cc  B (UCD 3.1 RECORD SEPARATOR)
    # 0085    NEL NEXT LINE                   Cc  B (C1 Control Code)
    # 2028    LS  LINE SEPARATOR              Zl  WS  (Unicode)
    # 2029    PS  PARAGRAPH SEPARATOR         Zp  B   (Unicode)
    # The Standard ASCII control codes (C0) are in the range 00-1F.
    # LF, CR, FS, GS, RS are in ASCII, FS, GS, RS are not line breakers
    # “The separators (File, Group, Record, and Unit: FS, GS, RS and US) were
    # made to structure data, usually on a tape, in order to simulate punched
    # cards. End of medium (EM) warns that the tape (or whatever) is ending.
    # While many systems use CR/LF and TAB for structuring data, it is possible
    # to encounter the separator control characters in data that needs to be
    # structured. The separator control characters are not overloaded; there is
    # no general use of them except to separate data into structured groupings.
    # Their numeric values are contiguous with the space character, which can
    # be considered a member of the group, as a word separator.”

    # Some properties are defines as "Mandatory Line Breaks (non-tailorable)":
    # BK, CR, LF, NL

    # And the resulting list is different:
    #                                    CAT BIDI BRK
    # ------------------------------------------------------------------------
    # 000A    LF  LINE FEED                   Cc  B   LF
    # 000B    VT  LINE TABULATION             Cc  S   BK (since Unicode 5.0)
    # 000C    FF  FORM FEED                   Cc  WS  BK
    # 000D    CR  CARRIAGE RETURN             Cc  B   CR
    # 0085    NEL NEXT LINE                   Cc  B   NL (C1 Control Code)
    # 2028    LS  LINE SEPARATOR              Zl  WS  BK
    # 2029    PS  PARAGRAPH SEPARATOR         Zp  B   BK
    # ------------------------------------------------------------------------

    # Differences:
    # - VT and FF are mandatory breaks (even if "implementations are not
    # required to support the VT character")
    # - FS, GS, US are combined marks (CM): "Prohibit a line break between
    # the character and the preceding character"

    # Bad unicode or bad utf-8
    UNICODE_CHAR_WITH_LF = u'\u560a'
    BAD_UTF8 = u'\xe5\x98\n'
    URLE_UNICODE_CHAR_WITH_LF = u'%E5%98%0A'
    URLE_BAD_UTF8 = u'%E5%98%0A'

    # unicode spaces
    UNICODE_NO_BREAK_SPACE = u'\u00a0'
    UNICODE_OGHAM_SPACE_MARK = u'\u1680'
    UNICODE_EN_QUAD = u'\u2000'
    UNICODE_EM_QUAD = u'\u2001'
    UNICODE_EN_SPACE = u'\u2002'
    UNICODE_EM_SPACE = u'\u2003'
    UNICODE_THREE_PER_EM_SPACE = u'\u2004'
    UNICODE_FOUR_PER_EM_SPACE = u'\u2005'
    UNICODE_SIX_PER_EM_SPACE = u'\u2006'
    UNICODE_FIGURE_SPACE = u'\u2007'
    UNICODE_PUNCTUATION_SPACE = u'\u2008'
    UNICODE_THIN_SPACE = u'\u2009'
    UNICODE_HAIR_SPACE = u'\u200a'
    UNICODE_MEDIUM_MATHEMATICAL_SPA = u'\u205F'
    UNICODE_NARROW_NO_BREAK_SPACE = u'\u202F'
    UNICODE_IDEOGRAPHIC_SPACE = u'\u3000'
    UNICODE_ZERO_WIDTH_SPACE = u'\u200b'
    UNICODE_ZERO_WIDTH_NO_BREAK_SPACE = u'\ufeff'

    URLE_UNICODE_NO_BREAK_SPACE = u'%C2%A0'
    URLE_UNICODE_OGHAM_SPACE_MARK = u'%E1%9A%80'
    URLE_UNICODE_EN_QUAD = u'%E2%80%80'
    URLE_UNICODE_EM_QUAD = u'%E2%80%81'
    URLE_UNICODE_EN_SPACE = u'%E2%80%82'
    URLE_UNICODE_EM_SPACE = u'%E2%80%83'
    URLE_UNICODE_THREE_PER_EM_SPACE = u'%E2%80%84'
    URLE_UNICODE_FOUR_PER_EM_SPACE = u'%E2%80%85'
    URLE_UNICODE_SIX_PER_EM_SPACE = u'%E2%80%86'
    URLE_UNICODE_FIGURE_SPACE = u'%E2%80%87'
    URLE_UNICODE_PUNCTUATION_SPACE = u'%E2%80%88'
    URLE_UNICODE_THIN_SPACE = u'%E2%80%89'
    URLE_UNICODE_HAIR_SPACE = u'%E2%80%8A'
    URLE_UNICODE_MEDIUM_MATHEMATICAL_SPA = u'%E2%81%9F'
    URLE_UNICODE_NARROW_NO_BREAK_SPACE = u'%E2%80%AF'
    URLE_UNICODE_IDEOGRAPHIC_SPACE = u'%E3%80%80'
    URLE_UNICODE_ZERO_WIDTH_SPACE = u'%E2%80%8B'
    URLE_UNICODE_ZERO_WIDTH_NO_BREAK_SPACE = u'%EF%BB%BF'

    UNICODE_EXPANSION_ARABIC = u'\ufdfa'
    UTF8_EXPANSION_ARABIC = b'\xef\xb7\xba'

    # overlong chars are the ones with
    # 11000000 10------ added. that is the marker for 2 bytes UTF-8
    # + valid start of a 2 bytes second byte.
    # SHOULD not be decoded as valid utf-8
    UTF8_OVERLONG_ANTISLASH = b'\xc0\x9c'
    URLE_UTF8_OVERLONG_ANTISLASH = u'%C0%9C'
    UTF8_OVERLONG_CR = b'\xc0\x8d'
    URLE_UTF8_OVERLONG_CR = u'%C0%8D'
    UTF8_OVERLONG_LF = b'\xc0\x8a'
    URLE_UTF8_OVERLONG_LF = u'%C0%8A'

    # we use ascii 'Start of Text' byte, to be a special
    # 1 byte sized character used to be replaced at the end
    # by bytes streams
    BYTES_SPECIAL_REPLACE = u'\x02'

    CONTROL_CHARS = {u'space': SP,
                     u'carriagereturn': CR,
                     u'formfeed': FF,
                     u'htab': TAB,
                     u'vtab': VTAB,
                     u'bell': BEL,
                     u'null': NULL}
    NO_TOKEN_CHARS = {u'parenthesis_open': u'(',
                      u'parenthesis_close': u')',
                      u'comma': u',',
                      u'slash': u'/',
                      u'lower_than': u'<',
                      u'equal': u'=',
                      u'greater_than': u'>',
                      u'question_mark': u'?',
                      u'arobas': u'@',
                      u'square_open': u'[',
                      u'antislash': u'\\',
                      u'square_close': u']',
                      u'curly_open': u'{',
                      u'curly_close': u'}',
                      u'quote': u'"'}
    NO_TOKEN_CHARS_VALUES = NO_TOKEN_CHARS.values()
    TCHARS = {u'exclamation_mark': u'!',
              u'sharp': u'#',
              u'dollar': u'$',
              u'percent': u'%',
              u'and': u'&',
              u'single_quote': u"'",
              u'star': u'*',
              u'plus': u'+',
              u'minus': u'-',
              u'dot': u'.',
              u'start': u'^',
              u'underscore': u'_',
              u'backstick': u'`',
              u'pipe': u'|',
              u'tilde': u'~'}

    ZONE_FIRST_LINE = 1
    ZONE_HEADERS = 2
    ZONE_BODY = 3
    ZONE_CHUNK_SIZE = 3

    @staticmethod
    def print_message(message, cleanup=False, dir_out=True, color=None):

        config = ConfigFactory.getConfig()

        # Todo manage string escapes in case of conversion error
        if not isinstance(message, str):
            try:
                message = message.decode('ascii')
            except UnicodeDecodeError:
                message = message.decode('unicode-escape')
            except UnicodeEncodeError:
                # here with py2
                message = message.encode('unicode-escape')

        msglen = len(message)
        maxlen = config.getint('OUTPUT_MAX_MSG_SIZE')
        if (msglen > maxlen):
            message = message[0:maxlen] + u'( to be continued...)'

        if cleanup:
            message = Tools.show_chars(message)

        # import pdb; pdb.set_trace();
        if dir_out:
            if not color:
                color = 'green'
            cprint(u'-->', color, end=u' ')
        else:
            if not color:
                color = 'cyan'
            cprint(u'<--', color, end=u' ')
        cprint(message, color)
        sys.stdout.flush()

    @staticmethod
    def show_chars(message):
        message = message.replace(
            Tools.CR, u"[CR]").replace(
            Tools.TAB, u"[TAB]").replace(
            Tools.VTAB, u"[VTAB]").replace(
            Tools.FF, u"[FF]").replace(
            Tools.BEL, u"[BEL]").replace(
            Tools.BS, u"[BS]").replace(
            Tools.NULL, u"[NULL]").replace(
            Tools.LF, u"[LF]\n").replace(
            Tools.BYTES_SPECIAL_REPLACE, u"[\\xx]")
        return message

    @staticmethod
    def iteritems(dic):
        """Sorted dictionnary iterator for py 2.x and 3.x"""
        return iter(sorted(dic.items()))


def outmsg(msg, prefix=u'', color=None):
    try:
        if isinstance(msg, str):
            msg = msg.encode('utf8')
        if isinstance(prefix, str):
            prefix = prefix.encode('utf8')
    except UnicodeDecodeError:
        # python 2
        msg = '<BLIND>stream with bad utf-8 chars</BLIND>'
    Tools.print_message(prefix + msg, color=color)


def inmsg(msg, prefix=u'', color=None):
    try:
        if isinstance(msg, str):
            msg = msg.encode('utf8')
        if isinstance(prefix, str):
            prefix = prefix.encode('utf8')
    except UnicodeDecodeError:
        # python 2
        msg = '<BLIND>stream with bad utf-8 chars</BLIND>'
    Tools.print_message(prefix + msg, dir_out=False, color=color)


def get_rand():
    return u''.join(random.choice('abcdefghijklmnop548731') for _ in range(6))
