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
from django.utils.decorators import method_decorator
from cms.utils import get_language_from_request

from .poutil import Locales, LANGS, KINDS

from .settings import *

class TranslatorMixin(object):
    """Prevent people who do not have translator rights from
       accessing translator pages, shows 403 instead."""
    locales = Locales()

    @property
    def language(self):
        lang = get_language_from_request(self.request)
        if lang not in LANGS:
            return LANGS.keys()[0]
        return lang

    @method_decorator(permission_required("cmsrosetta.change_translation", raise_exception=True))
    def dispatch(self, request, *args, **kwargs):
        return super(TranslatorMixin, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **data):
        path = self.request.path.replace(self.language + "/", '')
        return {
          'languages'       : settings.LANGUAGES,
          'language'        : self.language,
          'language_name'   : LANGS.get(self.language, 'Error'),
          'current_url'     : path,
          'language_source' : MESSAGES_SOURCE_LANGUAGE_CODE,
          'kinds'           : KINDS,
        }
