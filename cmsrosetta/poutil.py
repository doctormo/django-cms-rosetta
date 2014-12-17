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

import pytz
import django
import os

from datetime import datetime
from collections import defaultdict
from glob import glob

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.utils.importlib import import_module
from django.utils.timezone import now

from polib import POFile, pofile as get_po

from .poentry import POEntry
from .utils import *
from .settings import *

import sys
import six
import hashlib


LAST_RELOAD  = now()
KINDS        = set()
PROJECT_PATH = get_path(import_module(settings.SETTINGS_MODULE).__file__)

class NewPoFile(POFile):
    """A po file full of translatable strings"""
    _filters = (
       ('untranslated', _('Untranslated only'), False ),
       ('translated',   _('Translated only'),   True  ),
       ('obsolete',     _('Obsolete only'),     False ),
       ('fuzzy',        _('Fuzzy only'),        True  ),
       ('all',          _('All'),               False ),
    )

    def __init__(self, *args, **kwargs):
        POFile.__init__(self, *args, **kwargs)
        self.loaded_time = now()
        self.filename = os.path.realpath(self.fpath)
        self.mofile = self.filename[:-2] + 'mo'

    def all_entries(self):
        return [ e for e in self if not e.obsolete ]

    def get_filter(self, fid):
        return getattr(self, fid+'_entries')()

    @property
    def filters(self):
        for (fid, name, done) in self._filters:
            if len(self.get_filter(fid)):
                yield (fid, name)

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
        return pytz.utc.localize(datetime.utcfromtimestamp(os.path.getmtime(self.filename)))

    @property
    def last_compiled(self):
        """Returns the last compiled time of the mo-file itself"""
        return pytz.utc.localize(datetime.utcfromtimestamp(os.path.getmtime(self.mofile)))

    @property
    def is_fresh(self):
        """Returns true if last modified is above last thread reload"""
        return self.last_compiled <= LAST_RELOAD

    @property
    def is_stale(self):
        """Returns true if the last_modified is above the obj load"""
        return self.last_modified >= self.loaded_time

    @property
    def has_updates(self):
        """Returns true if any of the entries have been updated"""
        return sum( [ getattr(e, 'updated', False) for e in self ] )

    def progress_totals(self):
        return [ (a, b, float(b) / len(self) * 100) for (a,b) in self.progress(True).items() ]

    def done_total(self):
        return float(sum([ b for (a,b) in self.progress(True).items() ])) / len(self) * 100

    def progress(self, done=None):
        return dict( (b, len(self.get_filter(a))) for (a,b,c) in self._filters
            if done == None or c == done )

    def get_url(self):
        return reverse('rosetta-file', kwargs=dict(kind=self.app.kind, page=self.app.name))


class LocaleDir(list):
    """A single locale directory"""
    def __init__(self, path, kind):
        self.path = get_path(path)
        self.kind = kind

    def __iter__(self):
        for lang in LANGS:
            yield self[lang]

    def __getitem__(self, key):
        if not len(self):
            self._generate_all()
        index  = list(LANGS).index(key)
        pofile = list.__getitem__(self, index)
        if pofile.is_stale:
            self[index] = self.generate(key)
        return list.__getitem__(self, index)

    def generate(self, lang):
        poname = self._generate_name(lang)
        pofile = get_po(poname, klass=NewPoFile, wrapwidth=POFILE_WRAP_WIDTH)
        pofile.app = self
        return pofile

    def _generate_all(self):
        for lang in LANGS:
            self.append(self.generate(lang))

    def _generate_name(self, lang):
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
            return [ b[key] for (a,b) in self.items() ]
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

    def stats(self):
        ret = defaultdict(lambda: defaultdict(int))
        for lang in LANGS:
            for item in self[lang]:
                for (p,t) in item.progress().items():
                    ret[lang][p] += t

    def get_for_lang(self, lang):
        for kind in self.keys():
            for locale in self[kind].values():
                yield locale[lang]

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

