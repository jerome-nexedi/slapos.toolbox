# -*- coding: utf-8 -*-

import collections
import StringIO

class LXCConfig(object):
    """LXC Configuration file parser
    """

    class _Sub(object):
        """Subobject to go throught
        LXC COnfiguration"""

        def __init__(self, parent, namespace):
            self._parent = parent
            self._namespace = namespace

        def __getattr__(self, name):
            if name.startswith('_'):
                return self.__dict__[name]
            return self._parent._get('%s.%s' % (self._namespace,
                                                name))

        def __setattr__(self, name, value):
            if name.startswith('_'):
                self.__dict__[name] = value
            else:
                self._parent._set('%s.%s' % (self._namespace, name),
                                  value)



    def __init__(self, filename):
        """LXCConfig init method. filename should be a string
        of the path to the filename.
        """
        self._filename = filename
        with open(filename, 'r') as lxcconf_file:
            self._values = self._load(lxcconf_file.read())

    def __getattr__(self, name):
        return self._get(name)

    def __setattr__(self, name, value):
        if name.startswith('_'):
            self.__dict__[name] = value
        else:
            self._set(name, value)

    def _load(self, config_string):
        result = collections.OrderedDict()
        for line in config_string.split('\n'):
            if not line.strip().startswith('#') and line.strip() != '':
                if '=' not in line:
                    raise ValueError("Not a valid LXCFile")
                key, value = [i.strip() for i in line.split('=', 1)]
                if key in result:
                    if isinstance(result[key], basestring):
                        result[key] = [result[key], value]
                    else:
                        result[key].append(value)
                else:
                    result[key] = value
        return result

    def _set(self, key, value):
        self._values['lxc.%s' % key] = value

    def _get(self, key):
        try:
            return self._values['lxc.%s' % key]
        except KeyError:
            return self._Sub(self, key)

    def __str__(self):
        result = StringIO.StringIO()
        for key, value in self._values.iteritems():
            if isinstance(value, basestring):
                print >> result, key, '=', value
            else:
                for item in value:
                    print >> result, key, '=', item
        return result.getvalue()
