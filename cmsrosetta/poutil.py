#
# Copyright (C) 2014 Martin Owens <doctormo@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

import django
import os

from datetime import datetime
from collections import defaultdict
from glob import glob

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.utils.importlib import import_module
from django.utils.timezone import now

from polib import POEntry, POFile, pofile as get_po

from .utils import *
from .settings import *

import sys
import six
import hashlib

get_path     = lambda p: os.path.normpath(os.path.abspath(os.path.isfile(p)\
                 and os.path.dirname(p) or p))

LAST_RELOAD  = now()
KINDS        = set()
LANGS        = dict(settings.LANGUAGES)
C_LANG       = LANGS.pop(MESSAGES_SOURCE_LANGUAGE_CODE, None)
PROJECT_PATH = get_path(import_module(settings.SETTINGS_MODULE).__file__)

def get_md5hash(self):
    return hashlib.md5(
      (six.text_type(self.msgid) +
       six.text_type(self.msgstr) +
       six.text_type(self.msgctxt or "")).encode('utf8')
    ).hexdigest()

def set_msg(self, msg):
    if isinstance(msg, list):
        for (x, d) in enumerate(self.msgstr_plural):
            msg[x] = fix_nls(d, msg[x])
            if msg[x] != d:
                self.msgstr_plural[x] = msg[x]
                self.updated = True
    else:
        msg = fix_nls(self.msgstr, msg)
        if msg != self.msgstr:
            self.msgstr = msg
            self.updated = True

def set_flag(self, flag, value):
    (a,b) = (flag in self.flags, value)
    if a and not b:
        self.flags.remove(flag)
        self.updated = True
    elif b and not a:
        self.flags.append(flag)
        self.updated = True

# Monkey patch for unique-id for each entry
POEntry.md5hash = property(get_md5hash)
POEntry.set_flag = set_flag
POEntry.set_msg = set_msg


class NewPoFile(POFile):
    """A po file full of translatable strings"""
    _filters = (
       ('untranslated', _('Untranslated only')),
       ('translated', _('Translated only')),
       ('obsolete', _('Obsolete only')),
       ('fuzzy', _('Fuzzy only')),
       ('all', _('All')),
    )

    def __init__(self, *args, **kwargs):
        POFile.__init__(self, *args, **kwargs)
        self.loaded_time = now()

    def all_entries(self):
        return [ e for e in self if not e.obsolete ]

    def get_filter(self, fid):
        return getattr(self, fid+'_entries')()

    @property
    def filters(self):
        for (fid, name) in self._filters:
            if len(self.get_filter(fid)):
                yield (fid, name)

    @property
    def filename(self):
        return os.path.realpath(self.fpath)

    @property
    def path(self):
        f = self.filename
        if 'site-packages' in f:
            return '@' + f.split('site-packages')[-1]
        return os.path.realpath(f).replace(settings.PROJECT_PATH, '~')

    @property
    def lang(self):
        """Returns the two letter code for this language"""
        return self.filename.split('/locale/', 1)[-1].split('/')[0]

    @property
    def language(self):
        """Returns the translated full name for this language translation"""
        return _(LANGS.get(self.lang, 'Unknown'))

    @property
    def last_modified(self):
        """Returns the last modified time of the po-file itself"""
        return datetime.utcfromtimestamp(os.path.getmtime(self.filename))

    @property
    def is_fresh(self):
        """Returns true if last modified is above last thread reload"""
        return self.last_modified <= LAST_RELOAD

    @property
    def is_stale(self):
        """Returns true if the last_modified is above the obj load"""
        return self.last_modified >= self.loaded_time

    @property
    def has_updates(self):
        """Returns true if any of the entries have been updated"""
        return any( [ getattr(e, 'updated', False) for e in self ] )

    def progress_totals(self):
        return [ (i[0], i[1], float(i[1]) / len(self) * 100) for i in self.progress() ]

    def done_total(self):
        return float(sum([ i[1] for i in self.progress() ])) / len(self) * 100

    def progress(self):
        return (
          ('done',     len(self.translated_entries())),
          ('fuzzy',    len(self.fuzzy_entries())),
          ('obsolete', len(self.obsolete_entries())),
        )

    def get_url(self):
        return reverse('rosetta-file', kwargs=dict(kind=self.app.kind, page=self.app.name))


class LocaleDir(object):
    """A single locale directory"""
    def __init__(self, path, kind):
        self.path = get_path(path)
        self._po_files = []
        self._po_langs = {}
        self.kind = kind

    def __iter__(self):
        return self.po_files.__iter__()

    def __getitem__(self, key):
        return self.po_langs[key]

    @property
    def po_files(self):
        if not self._po_files:
            for lang in LANGS.keys():
                pofile = self._generate_lang(lang)
                if not pofile:
                    continue
                self._po_files.append( get_po(pofile, klass=NewPoFile, wrapwidth=POFILE_WRAP_WIDTH))
                self._po_langs[lang] = self._po_files[-1]
                self._po_files[-1].app = self
        return self._po_files

    @property
    def po_langs(self):
        if not self._po_langs:
            po = self.po_files
        return self._po_langs

    def get_for_lang(self, lang):
        return self.po_langs[lang]

    def _generate_lang(self, lang):
        for fn in POFILENAMES:
            for lang_code in self._veriations(lang):
                filename = self._po_file(lang_code, fn)
                if os.path.isfile(filename):
                    return filename
        return self._gen_filename(lang)

    def _po_file(self, lang, fn):
        return os.path.join(self.path, lang, 'LC_MESSAGES', fn)

    def _gen_filename(self, lang):
        pot_file = self.pot_file()
        if pot_file:
            filename = self._po_file(lang, os.path.basename(pot_file))
            print "Saving %s" % filename
            if not os.path.isdir(os.path.dirname(filename)):
                os.makedirs(os.path.dirname(filename))
            new_po = get_po(pot_file)
            new_po.fpath = None
            new_po.metadata['Language'] = lang
            for entry in new_po:
                entry.msgstr = ''
                if entry.msgstr_plural:
                    for pos in entry.msgstr_plural:
                        entry.msgstr_plural[pos] = ''
            new_po.save(filename)
            return filename

    def pot_file(self):
        if not hasattr(self, '_pot_file'):
            self._pot_file = None
            for item in glob(self._po_file('*', '*.po')):
                if not self._pot_file or os.path.getmtime(item) > os.path.getmtime(self._pot_file):
                    self._pot_file = item
        return self._pot_file

    def _veriations(self, lang):
        """Generator to return en, en_GB, en_gb, en-gb, en-GB veriations"""
        lang = lang.replace('_', '-')
        if '-' in lang:
            bits = lang.lower().split('-', 1)
            for sep in '-_':
                yield bits[0] + sep + bits[1]
                yield bits[0] + sep + bits[1].upper()
        else:
            yield lang

    @property
    def name(self):
        path = self.path.replace('/locale', '')
        return path.split("/")[-1].replace(' ', '_') + (
          path.endswith('js.po') and '_js' or '')

    def __repr__(self):
        return "LocaleDir('%s')" % (self.path)


class CmsGenerator(object):
    """Generate po for django-cms"""
    def __getitem__(self, page):
        pass

    def values(self):
        return []

class KindList(dict):
    """A subset list showing only items"""
    def __getitem__(self, key):
        if key in LANGS:
            return [ b.get_for_lang(key) for (a,b) in self.items() ]
        return dict.__getitem__(self, key)

class Locales(defaultdict):
    """A full list of all possible locales in all projects"""
    def __init__(self):
        defaultdict.__init__(self, KindList)
        for (path, kind) in self.dirs():
            if os.path.isdir(path):
                locale = LocaleDir(path, kind)
                if locale.name in self[kind]:
                    raise KeyError("Locale id/name used: %s (%s.%s)" % (
                        path, kind, locale.name))
                self[kind][locale.name] = locale
                KINDS.add(kind)
        self['cms'] = CmsGenerator()

    def __repr__(self):
        return "Locales()"

    def __getitem__(self, key):
        if key in LANGS:
            return self.get_for_lang(key)
        return defaultdict.__getitem__(self, key)

    def get_for_lang(self, lang):
        for kind in self.keys():
            for locale in self[kind].values():
                yield locale.get_for_lang(lang)

    @p_cache(60 * 60, 'rosetta_locale_paths', list)
    def dirs(self):
        for path in getattr(settings, 'LOCALE_PATHS', ()) + (
                  os.path.join(PROJECT_PATH, 'locale'),
                  os.path.join(PROJECT_PATH, '..', 'locale')):
            yield (path, 'project')

        for path in EXTRA_PATHS:
            yield (path, 'other')

        for root, dirnames, filename in os.walk(get_path(django.__file__)):
            if 'locale' in dirnames:
                yield (os.path.join(root, 'locale'), 'django')

        # project/app/locale
        for appname in settings.INSTALLED_APPS:
            if EXCLUDED_APPLICATIONS and appname in EXCLUDED_APPLICATIONS:
                continue
            apppath = os.path.join(get_path(import_module(appname).__file__), 'locale')

            if 'contrib' in apppath and 'django' in apppath:
                yield (apppath, 'contrib')
            elif PROJECT_PATH not in apppath:
                yield (apppath, 'third-party')
            else:
                yield (apppath, 'project')

