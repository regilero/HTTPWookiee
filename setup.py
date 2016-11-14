#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path
import sys

here = path.abspath(path.dirname(__file__))

# Get long description from README.md
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

requires = ['termcolor', 'six', 'argparse']
if sys.version_info[0] == 2:
    requires.append('configparser')
    requires.append('py2-ipaddress')
    requires.append('future')

setup(
    name="HTTPWookiee",
    version="0.6.0",
    author="LEROY Régis [regilero]",
    author_email="regis.leroy@gmail.com",
    include_package_data=True,
    url="http://pypi.python.org/pypi/HTTPWookiee_v010/",
    license="GNU GPL V3",
    description='HTTP Smuggling test tool for HTTP Servers and proxies',
    long_description=long_description,
    classifiers=[
        # How mature is this project? Common values are
        # 3 - Alpha
        # 4 - Beta
        # 5 - Production/Stable
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Intended Audience :: Developers',
        'Topic :: Internet :: WWW/HTTP :: HTTP Servers',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
    ],
    keywords='HTTP Smuggling test server proxy',
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    install_requires=requires,
    # pip install -e .[dev,test]
    extras_require={
        'dev': ['check-manifest'],
        'test': ['coverage'],
    }
)
