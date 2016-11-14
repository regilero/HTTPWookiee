#!/usr/bin/env python
# -*- coding: utf-8 -*-


class EndOfBufferError(Exception):
    """Exception used to manage the end of content in parsing."""
    pass


class PrematureEndOfStream(Exception):
    """We reach the End before expected."""
    pass


class OptionalCRLFSeparator(Exception):
    """Exception used to detect extra separator between messages."""
    pass
