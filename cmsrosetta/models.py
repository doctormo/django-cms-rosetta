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

import sys

from six import text_type as text

from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.utils.timezone import now
from django.db.models import *

from cms.utils.permissions import get_current_user as get_user

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


import imp
from django.conf import settings
from django.utils.importlib import import_module
from .poplugin import TranslationPlugin
from .settings import PLUGINS

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



