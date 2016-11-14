#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
try:
    import configparser
except ImportError:
    import ConfigParser as configparser

rcfile = None


class ConfigFactory(object):

    _confs = dict()

    @staticmethod
    def getConfig(section='main', source=None):
        global rcfile

        if source:
            conf_file = ConfigFactory.get_conf_file(source)
            if conf_file not in ConfigFactory._confs:
                # print("SOURCE Loading {0}".format(conf_file))
                conf = Config(conf_file)
                if 'main' not in conf.settings.sections():
                    conf.settings.add_section('main')
                ConfigFactory._confs[conf_file] = conf
        else:
            conf_file = 'default'
            if 'default' not in ConfigFactory._confs:
                # env HTTPWOOKIEE_CONF can be used as default conf file
                default_file = os.environ.get("HTTPWOOKIEE_CONF", None)
                # print("env check HTTPWOOKIEE_CONF :{0}".format(default_file))
                if default_file is not None and default_file is not '':
                    # print("SOURCE testing {0}".format(default_file))
                    if not os.path.exists(default_file):
                        raise IOError(
                            'Config File {0} not found'.format(default_file))
                else:
                    # lazy thing
                    if rcfile is None:
                        rcfile = os.path.join(os.path.expanduser('~'),
                                              '.httpwookieerc')
                    if os.path.exists(rcfile):
                        print('No HTTPWOOKIEE_CONF defined, '
                              'loading ~/.httpwookieerc')
                        default_file = rcfile
                    else:
                        print('No HTTPWOOKIEE_CONF defined, '
                              'and no ~/.httpwookieerc found.')
                        default_file = None

                # print("Final Loading {0}".format(default_file))
                conf = Config(default_file)
                if 'main' not in conf.settings.sections():
                    conf.settings.add_section('main')
                ConfigFactory._confs['default'] = conf

        conf = ConfigFactory._confs[conf_file]
        if conf.settings.has_section(section):
            # import pdb; pdb.set_trace()
            _c = ConfigReader(conf.settings, section)
            # _c = conf.settings[section]
            if not _c.getboolean('I_HAVE_READ_AND_UNDERSTAND_THE_FAQ'
                                 '_AND_I_AM_RESPONSIBLE_OF_MY_ACTS'):
                raise SystemExit('Read the FAQ')
            return _c
        else:
            raise ValueError('Invalid conf section {0}'.format(section))

    @staticmethod
    def get_conf_file(source):
        conf_file = source
        if not os.path.exists(conf_file):
            raise IOError('Config File {0} not found'.format(conf_file))
        return conf_file


class ConfigReader:
    'Fix py2/py3 problems, direct section access only available in py3.'

    def __init__(self, configParserObject, section='Main'):
        self.section = section
        self._conf = configParserObject

    def __str__(self):
        out = '{0} {1}'.format(self.section, self._conf.items(
            self.section, raw=True))
        return out

    def get(self, confkey):
        return self._conf.get(self.section, confkey)

    def getint(self, confkey):
        return self._conf.getint(self.section, confkey)

    def getboolean(self, confkey):
        return self._conf.getboolean(self.section, confkey)


class Config:

    settings = None
    DEFAULTS = {
        'DEBUG': u'false',
        'SERVER_HOST': u'localhost',
        'MULTIPLE_HOSTS_TESTS': 'false',
        'REVERSEPROXY_TESTS_ONLY': 'false',
        'SERVER_NON_DEFAULT_HOST': u'dummy-host2.example.com',
        'SERVER_SSL': u'false',
        # computed by socket.getaddrinfo() if not provided (b'')
        'SERVER_IP': u'',
        'SERVER_PORT': u'80',
        'SERVER_DEFAULT_LOCATION': u'/index.html',
        'SERVER_DEFAULT_LOCATION_CONTENT': u'It works',
        'SERVER_NON_DEFAULT_LOCATION': u'/index.html',
        'SERVER_NON_DEFAULT_LOCATION_CONTENT': u'Dummy Test',
        'OUTPUT_MAX_MSG_SIZE': u'3800',
        'CLIENT_SOCKET_READ_TIMEOUT_MS': u'1000',
        'CLIENT_SOCKET_READ_SIZE': u'1024',
        # String present in regular default location response body
        'BACKEND_PORT': u'8282',
        'BACKEND_LOCATION_PREFIX': u'/proxy',
        'BACKEND_WOOKIEE_LOCATION': u'/test/wookiee',
        'BACKEND_SOCK_READ_SIZE': u'1024',
        'I_HAVE_READ_AND_UNDERSTAND_THE_FAQ_AND_I_AM_RESPONSIBLE_'
        'OF_MY_ACTS': u'false'
    }

    def __init__(self, conf_file=None):
        # print('loading conf')
        defaults = self.DEFAULTS
        self.settings = configparser.ConfigParser(defaults)

        if conf_file:
            # print('loading conf file  {0}'.format(conf_file))
            self.settings.read(conf_file)


class Register:

    instance = None
    register = {}
    flags = {
        'available': True,
        'keepalive': True,
        'pipelining': True
    }

    @staticmethod
    def show():
        out = 'flags: {0}\nregister: {1}'.format(Register.flags,
                                                 Register.register)
        print(out)

    @staticmethod
    def flag(key, value=True):
        # print('REGISTER {0} => {1}'.format(key,value))
        Register.flags[key] = value

    @staticmethod
    def set(key, value):
        Register.register[key] = value

    @staticmethod
    def get(key, default=None):
        val = None
        if key in Register.register:
            val = Register.register[key]
        else:
            if default is not None:
                val = default
        return val

    @staticmethod
    def hasFlag(key, default=True):
        if key in Register.flags:
            return Register.flags[key]
        else:
            return default
