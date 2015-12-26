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
from importlib import import_module
from collections import defaultdict
from glob import glob

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.utils.timezone import now

from polib import POFile, pofile as get_po

from .poentry import POEntry
from .poplugin import *
from .app import RosettaApp
from .settings import POFILENAMES, POFILE_WRAP_WIDTH, settings
from .utils import *

import sys
import six
import hashlib


LAST_RELOAD  = now()


class NewPoFile(POFile):
    """A po file full of translatable strings"""
    _filters = (
       ('untranslated', _('Untranslated only'), None ),
       ('translated',   _('Translated only'),   ['done'] ),
       ('obsolete',     _('Obsolete only'),     None ),
       ('fuzzy',        _('Fuzzy only'),        ['done'] ),
       ('all',          _('All'),               None ),
    )

    def __init__(self, *args, **kwargs):
        POFile.__init__(self, *args, **kwargs)
        self.loaded_time = now()
        self.filename = os.path.realpath(self.fpath)

    @property
    def mofile(self):
        return self.filename[:-2] + 'mo'

    def all_entries(self):
        return [ e for e in self if not e.obsolete ]

    def get_filter(self, fid):
        return getattr(self, fid+'_entries', lambda: [])()

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
        return _(RosettaApp.languages.get(self.lang, 'Unknown'))

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

    def progress(self):
        return ((a,b,c,len(self.get_filter(a))) for (a,b,c) in self._filters )

    def get_url(self):
        return reverse('rosetta-file', kwargs=dict(kind=self.app.kind, page=self.app.name))


class LocaleDir(TranslationDirectory):
    """A single locale directory"""
    po_class = NewPoFile

    def __init__(self, path, kind):
        self.path = get_path(path)
        self.kind = kind
        super(LocaleDir, self).__init__(RosettaApp.languages)

    def generate(self, lang):
        name = self._generate_name(lang)
        pofile = get_po(name, klass=self.po_class, wrapwidth=POFILE_WRAP_WIDTH)
        pofile.app = self
        return pofile

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

    @property
    def name(self):
        path = self.path.replace('/locale', '')
        return path.split("/")[-1].replace(' ', '_') + (
          path.endswith('js.po') and '_js' or '')

    def __repr__(self):
        return "LocaleDir('%s')" % (self.path)

