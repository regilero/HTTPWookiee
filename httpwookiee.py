#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Main Runner for HTTPWookiee
#
# Not like tests.py, this will not run the HTTP tests internally,
# but instead against a real server.
# They're two main modes (both running by default):
#
# 1) - 'client': in this mode HTTPWokkiee is an HTTP client, simply
# sending requests against the tested HTTP server
#
#    HTTPWookiee            Tested HTTP
#      Client                Server
#        |                      |
#        |-----Request--------->|
#        |<----Response---------|
#        |
#    [analysis]
#
# 2) - 'server': in this mode HTTPWookiee will also run a server, used
# as a backend fr the tested HTTP Reverse Proxy
#
#    HTTPWookiee          Tested HTTP         HTTPWookiee
#      Client            Reverse Proxy       Server Thread
#        |                    |                   |
#        |-----Request------->|                   |
#        |                    |-----Request------>|
#        |                    |<----Response------|
#        |<----Response-------|                   |
#        |                    |                   |
#    [analysis]<- - - - - - - - - - - [ internal transmission ]
#
# Note that the ports, IP address and url used in tests can be defined in the
# configuration file.
#
# For each mode a big variety of tests exists. You could run the tests by
# calling directly the python test file:
#
#     ./httpwookiee/client/tests_chunks.py
#
# But the easiest way is to used this present file with the -m or --match
# option:
#
#     ./httpwookiee.py -m client -m chunks
#
# To run the reverse proxy server tests alter the mode:
#
#     ./httpwookiee.py -m server -m chunks

from httpwookiee.core.result import TextStatusResult
from httpwookiee.core.testloader import WookieeTestLoader
from httpwookiee.core.testrunner import WookieeTestRunner
from httpwookiee.config import ConfigFactory
from httpwookiee.core.version import Version
import unittest
import os
import sys
import argparse


def collectTestClasses(dirPath,
                       filters={},
                       debug=False,
                       classNamePrefix=''):
    classes = []
    if debug:
        print(' Files in {0}:'.format(dirPath))
    for dirName, subdirList, fileList in os.walk(dirPath, topdown=True):
        for subdir in subdirList:
            # we do our own recursion to build class name
            if (not subdir[:1] == '_') and not (subdir[:1] == '.'):
                subclasses = collectTestClasses(
                    os.path.join(dirName, subdir),
                    filters,
                    debug=debug,
                    classNamePrefix='{0}.{1}'.format(classNamePrefix, subdir))
                classes = classes + subclasses

        # prevents recursion in os.walk, '[:]' syntax trick enforce assignement
        # on the same subdirList that the main loop (reference)
        subdirList[:] = []

        for file in fileList:
            if ((file[:4] == "test") and (file[-3:] == ".py")):
                fullName = '{0}.{1}'.format(classNamePrefix, file[:-3])
                matched = True
                if filters['exclude']:
                    for excluding in filters['exclude']:
                        if not fullName.lower().find(excluding) == -1:
                            matched = False
                            break
                if matched and filters['match']:
                    for matching in filters['match']:
                        if fullName.lower().find(matching) == -1:
                            matched = False
                            break
                if matched:
                    if debug:
                        print(' * {0}'.format(fullName))
                    classes.append(fullName)
    return classes


def collectTestsSuites(classes, filters, debug=False, listOnly=False):

    suite = unittest.TestSuite()
    tl = WookieeTestLoader(filters, debug=(debug or listOnly))
    if debug:
        print(' Test suites:')
    for tclass in sorted(classes):
        if listOnly or debug:
            print(' + {0}'.format(tclass))
        collected_tests = tl.loadTestsFromClass(tclass)
        if not listOnly:
            suite.addTests(collected_tests)
    return _sortAllTests(suite)


def _sortAllTests(suite):
    flist = unittest.TestSuite()
    testlist = {}
    for test in suite:
        testlist[str(test)] = test
    for testId in sorted(testlist):
        flist.addTest(testlist[testId])
    return flist


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-V',
        "--verbose",
        help="increase output verbosity",
        action="store_true")
    parser.add_argument(
        '-v',
        "--version",
        help="current version",
        action="store_true")
    parser.add_argument(
        '-l',
        "--list",
        help="list available test files and units",
        action="store_true")
    parser.add_argument(
        '-n',
        "--no-buffer",
        help="send output as you get it, do not buffer until the end",
        action="store_true")
    parser.add_argument(
        '-m',
        "--match",
        help="case insensitive filter on included test files",
        action="append",
        default=[],
        metavar='STR')
    parser.add_argument(
        '-e',
        "--exclude",
        help="case insensitive filter on excluded test files",
        action="append",
        default=[],
        metavar='STR')
    parser.add_argument(
        '-M',
        "--unit-match",
        help="case insensitive filter on included unit test name",
        action="append",
        default=[],
        metavar='STR')
    parser.add_argument(
        '-E',
        "--unit-exclude",
        help="case insensitive filter on excluded unit test name",
        action="append",
        default=[],
        metavar='STR')
    parser.add_argument(
        '-t',
        "--test-num",
        help="select tests by number",
        action="append",
        type=int,
        default=[],
        metavar='NUM')
    args = parser.parse_args()

    if args.verbose or args.version:
        print(Version())
        if args.version:
            exit(0)

    # use env HTTPWOOKIEE_CONF to override defaults and force AUTOTEST
    # where client testers will run against our proxy backend, without using
    # any proxy, in fact.
    currdir = os.path.dirname(os.path.realpath(__file__))

    config = ConfigFactory.getConfig()
    if args.verbose or config.getboolean('DEBUG'):
        verbosity = 2
    else:
        verbosity = 1

    # Pre Flight tests, detect features support ---------------
    # for name, obj in inspect.getmembers(httpwookiee.client.tests_regular):
    #    if 'Test' == name[:4] and inspect.isclass(obj):
    #        testcases.append(obj)

    # collect all our main tests files --------------------------
    filters = {
        'match': [x.lower() for x in args.match],
        'exclude': [x.lower() for x in args.exclude],
        'nums': args.test_num,
    }
    classes = collectTestClasses(os.path.join(currdir, "httpwookiee"),
                                 filters,
                                 debug=args.verbose,
                                 classNamePrefix='httpwookiee')
    # collect our unit tests methods in theses files -------------
    filters = {
        'match': [x.lower() for x in args.unit_match],
        'exclude': [x.lower() for x in args.unit_exclude],
        'nums': args.test_num,
    }
    suite = collectTestsSuites(classes,
                               filters,
                               debug=args.verbose,
                               listOnly=args.list)

    if len(suite._tests):
        # without stream forced here python 2.7 is failing
        WookieeTestRunner(resultclass=TextStatusResult,
                          verbosity=verbosity,
                          buffer=not(args.no_buffer),
                          stream=sys.stderr).run(suite)
    else:
        print('No test to run, check your filters '
              '(or you where in list only mode?).')
