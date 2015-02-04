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
 Look into django-cms models and pick out data for translations.
"""

from django.contrib.sites.models import Site
from cms.models import Page

from cmsrosetta.settings import LANGS
from cmsrosetta.poplugin import *

class CmsPage(TranslationDirectory):
    def __init__(self, page, lang=None):
        self.page = page
        self.lang = lang
        self.app  = self

    def __getitem__(self, lang):
        if lang not in LANGS:
            raise KeyError("Unknown language: %s" % str(lang))
        if lang == self.lang:
            return self
        return type(self)(self.page, lang)

    def name(self):
        return self.page.get_title(self.lang)

    def progress(self):
        pass


"""
draft_page = page.get_draft_object()
published_page = page.get_public_object()
list[str] = page.get_languages()

str = page.get_page_title(lang)
str = page.get_title(lang)
str = page.get_menu_title(lang)
str = page.get_meta_description(lang)
bool = page.is_published(lang)

d = [ d.get_plugin_instance()[0] for c in b.placeholders.all() for d in c.get_plugins('en') ]

p = d[0].get_plugin_class_instance()
(i, p) = d[0].get_plugin_instance()
"""

