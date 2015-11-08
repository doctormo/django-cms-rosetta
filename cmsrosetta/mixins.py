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
Mixin locales access (global per thread) and restrict the translation permission
"""

from django.conf import settings
from django.contrib.auth.decorators import permission_required
from django.contrib.sites.models import Site
from django.contrib.staticfiles import finders
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from cms.utils import get_language_from_request

from .app import RosettaApp
from .settings import *

class TranslatorMixin(object):
    """Prevent people who do not have translator rights from
       accessing translator pages, shows 403 instead."""

    @property
    def locales(self):
        return RosettaApp.locales

    @property
    def language(self):
        lang = get_language_from_request(self.request)
        if lang not in RosettaApp.languages:
            if not RosettaApp.languages:
                raise ValueError("Languages isn't setup yet? that's odd.")
            return RosettaApp.languages.keys()[0]
        return lang

    @method_decorator(permission_required("cmsrosetta.change_translation", raise_exception=True))
    def dispatch(self, request, *args, **kwargs):
        return super(TranslatorMixin, self).dispatch(request, *args, **kwargs)

    def datum(self, key, *args):
        return self.request.GET.get(key, self.request.POST.get(key, *args))

    def get_context_data(self, **data):
        path = self.request.path.replace(self.language + "/", '')
        path = path.replace('en/', '')
        return {
          'languages'       : settings.LANGUAGES,
          'language'        : self.language,
          'language_name'   : RosettaApp.languages.get(self.language, 'Unknown'),
          'language_namo'   : _(RosettaApp.languages.get(self.language, 'Unknown')),
          'language_logo'   : self.get_icon(),
          'current_url'     : path,
          'language_source' : MESSAGES_SOURCE_LANGUAGE_CODE,
          'msg_per_page'    : MESSAGES_PER_PAGE, 
          'kinds'           : RosettaApp.plugins.keys(),
          'site'            : Site.objects.get_current()
        }

    def get_icon(self):
        icon = 'images/rosetta/langs/%s.svg' % self.language
        if not finders.find(icon):
            return 'images/rosetta/langs/default.svg'
        return icon

