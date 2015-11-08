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

import os

from django.contrib.sites.models import Site
from cms.models import Page

from .utils import locale_dirs
from .poplugin import TranslationPlugin
from .po_translations import LocaleDir
from .cms_translations import CmsPage

class LocaleDirectories(TranslationPlugin):
    slug = 'project'

    def dirs(self):
        return locale_dirs()

    def generate(self):
        for (path, kind) in self.dirs():
            if kind == self.slug and os.path.isdir(path):
                locale = LocaleDir(path, kind)
                self[locale.name] = locale

class DjangoDirectories(LocaleDirectories):
    slug = 'django'

class ThirdPartyDirectories(LocaleDirectories):
    slug = 'third-party'

class CmsTranslations(TranslationPlugin):
    """Generate po for django-cms"""
    slug = 'cms'

    def __init__(self, languages):
        self.site = Site.objects.get_current()
        super(CmsTranslations, self).__init__(languages)

    def generate(self):
        for page in Page.objects.public().filter(site=self.site):
            self[page.title] = CmsPage(page)

