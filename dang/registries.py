""" Registry objects """

import ConfigParser


class Entry(object):
    def __init__(self, name, version, revision, meta):
        self.name = name
        self.version = version
        self.revision = revision
        self.meta = meta

    @classmethod
    def from_meta(klass, name, meta):
        version = meta.pop('version', '')
        revision = meta.pop('revision', '')
        return klass(name, version, revision, meta)


class Registry(object):
    entry_maker = Entry.from_meta

    def __init__(self, name, entries=(), ini_file=None):
        self.name = name
        self.entries = []
        for entry in entries:
            if hasattr(entry, 'from_meta'):
                self.entries.append(entry)
            else:
                self.entries.append(self.entry_maker(entry))
        self.ini_file = ini_file

    @classmethod
    def from_ini_file(klass, ini_file):
        if not hasattr(ini_file, 'read'):
            ini_fobj = open(ini_file, 'rU')
        else:
            ini_fobj  = ini_file
        config = ConfigParser.SafeConfigParser()
        config.readfp(ini_fobj)
        entries = []
        defaults = config.defaults()
        reg_name = defaults['registry_name']
        for section in config.sections():
            name, version, revision = [s.strip() for s in section.split(',')]
            meta = {}
            for key, value in config.items(section):
                if key in ('version', 'revision'):
                    raise ValueError('Version and revision go in the section '
                                     'title')
                elif key != 'registry_name':
                    meta[key] = value
            entries.append(Entry(name, version, revision, meta))
        return klass(reg_name, entries, ini_file)

    def to_ini_file(self, ini_file=None):
        if ini_file is None:
            ini_file = self.ini_file
        if ini_file is None:
            raise ValueError('No ini file to write to')
        if not hasattr(ini_file, 'write'):
            ini_fobj = open(ini_file, 'wt')
        else:
            ini_fobj = ini_file
        config = ConfigParser.SafeConfigParser()
        config.set('DEFAULT', 'registry_name', self.name)
        for entry in self.entries:
            section_name = "%s,%s,%s" % (entry.name,
                                         entry.version,
                                         entry.revision)
            config.add_section(section_name)
            for key, value in entry.meta.items():
                config.set(section_name, key, value)
        config.write(ini_fobj)

