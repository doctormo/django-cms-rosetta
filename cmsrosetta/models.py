#
# Copyright 2014, Martin Owens <doctormo@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
"""
We want to log the changes to translations. For credit and tracking.
"""

import imp
import sys

from six import text_type as text

from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.utils.importlib import import_module
from django.utils.timezone import now
from django.db.models import *

from cms.utils.permissions import get_current_user as get_user

from .poplugin import TranslationPlugin
from .settings import PLUGINS, LANGS, settings

class Translation(Model):
    user   = ForeignKey(User, default=get_user)
    when   = DateTimeField(default=now)

    lang   = CharField(max_length=6)
    kind   = CharField(max_length=16)
    page   = CharField(max_length=255)
    
    edited = PositiveIntegerField(default=0)
    added  = PositiveIntegerField(default=0)

    def __str__(self):
        return _("%(user)s translated %(page)s[%(lang)s]") % self

    def __getitem__(self, key):
        return text(getattr(self, key))


for app in settings.INSTALLED_APPS:
    modname = 'translations'
    module_name = '%s.%s' % (app, modname)
    app_mod = import_module(app)
    try:
        imp.find_module(modname, app_mod.__path__ if hasattr(app_mod, '__path__') else None)
    except ImportError as error:
        if str(error) != 'No module named translations':
            raise
    else:
        for (key, value) in import_module(module_name).__dict__.items():
            if type(value) is type and issubclass(value, TranslationPlugin)\
              and value is not TranslationPlugin:
                PLUGINS[value.slug] = value


class Locales(dict):
    """A full list of all possible locales in all projects"""
    def __init__(self):
        # Add any registered plugins
        for (kind, plugin) in PLUGINS.items():
            self[kind] = plugin()

    def __repr__(self):
        return "Locales()"

    def __getitem__(self, key):
        if key in LANGS:
            return self.get_for_lang(key)
        return dict.__getitem__(self, key)

    def progress(self):
        ret = []
        for lang in LANGS:
            index = []
            prog = []
            ret.append({'id': lang, 'name': LANGS[lang], 'progress': prog})
            for item in self[lang]:
                for (a,b,c,d) in item.progress() or []:
                    if a not in index:
                        index.append(a)
                        prog.append( [a,b,c,d] )
                    else:
                        prog[index.index(a)][-1] += d
        return ret

    def get_for_lang(self, lang):
        for kind in self.keys():
            for locale in self[kind].values():
                yield locale[lang]



