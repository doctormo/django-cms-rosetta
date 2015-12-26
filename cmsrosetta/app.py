#
# Copyright 2015, Martin Owens <doctormo@gmail.com>
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
Loads all the current progress into memory.
"""

import imp
from collections import OrderedDict

from importlib import import_module
from django.apps import AppConfig, apps

from .settings import settings, MESSAGES_SOURCE_LANGUAGE_CODE
from .poplugin import TranslationPlugin

class Locales(dict):
    """A full list of all possible locales in all projects"""
    def __init__(self, langs, plugins):
        self.languages = langs
        # Add any registered plugins
        for (kind, plugin) in plugins.items():
            self[kind] = plugin(langs)

    def __repr__(self):
        return "Locales()"

    def __getitem__(self, key):
        if key in self.languages:
            return self.get_for_lang(key)
        return dict.__getitem__(self, key)

    def progress(self, kind=None):
        ret = []
        for (lang, name) in self.languages.items():
            index = []
            prog = []
            ret.append({'id': lang, 'name': name, 'progress': prog})
            for item in self.get_for_lang(lang, kind):
                for (a,b,c,d) in item.progress() or []:
                    if a not in index:
                        index.append(a)
                        prog.append( [a,b,c,d] )
                    else:
                        prog[index.index(a)][-1] += d
        return ret

    def get_for_lang(self, lang, *kinds):
        if not kinds or not kinds[0]:
            kinds = self.keys()
        for kind in kinds:
            for locale in self[kind].values():
                yield locale[lang]


class RosettaApp(AppConfig):
    name = 'cmsrosetta'
    modname = 'translations'
    verbose_name = "CMS Rosetta"

    languages = {}
    plugins = {}
    locales = Locales({}, {})

    def ready(self):
        RosettaApp.languages = OrderedDict(self.install_languages())
        RosettaApp.plugins = OrderedDict(self.install_plugins())
        RosettaApp.locales = Locales(RosettaApp.languages, RosettaApp.plugins)

    def install_languages(self):
        for lang in getattr(settings, 'LANGUAGES', []):
            if lang[0] != MESSAGES_SOURCE_LANGUAGE_CODE:
                yield lang

    def install_plugins(self):
        for app in settings.INSTALLED_APPS:
            mod = import_module(app)
            try:
                imp.find_module(self.modname, getattr(mod, '__path__', None))
                for plugin in self.register('%s.%s' % (app, self.modname)):
                    yield plugin
            except ImportError as error:
                if app == 'cmsrosetta' or str(error) != 'No module named translations':
                    raise

    def register(self, module_name):
        for (key, value) in import_module(module_name).__dict__.items():
            if type(value) is type and issubclass(value, TranslationPlugin)\
               and value is not TranslationPlugin:
                yield (value.slug, value)

