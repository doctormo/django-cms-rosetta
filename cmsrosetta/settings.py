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

from .version import VERSION

try:
    from django.conf import settings
except ImportError:
    settings = None

# Number of messages to display per page.
MESSAGES_PER_PAGE = 10

# Enable Google translation suggestions
ENABLE_TRANSLATION_SUGGESTIONS = False

# Displays this language beside the original MSGID in the admin
MAIN_LANGUAGE = None

# Change these if the source language in your PO files isn't English
MESSAGES_SOURCE_LANGUAGE_CODE = 'en'
MESSAGES_SOURCE_LANGUAGE_NAME = 'English'

WSGI_AUTO_RELOAD = False
UWSGI_AUTO_RELOAD = False

# Exclude applications defined in this list from being translated
EXCLUDED_APPLICATIONS = ()

# Line length of the updated PO file
POFILE_WRAP_WIDTH = 78

# Allow overriding of the default filenames, you mostly won't need to change this
POFILENAMES = ('django.po', 'djangojs.po')

CACHE_NAME = 'rosetta' in getattr(settings, 'CACHES', {}) and 'rosetta' or 'default'

# Require users to be authenticated (and Superusers or in group "translators").
# Set this to False at your own risk
REQUIRES_AUTH = True

EXTRA_PATHS = ()

# Get all our overloaded settings and all of django's globals
for (name, default) in locals().items():
    locals()[name] = getattr(settings, 'ROSETTA_'+name, default)

from collections import OrderedDict
S_LANG = MESSAGES_SOURCE_LANGUAGE_CODE
LANGS     = OrderedDict(l for l in getattr(settings, 'LANGUAGES', []) if l[0] != S_LANG)
LANGUAGES = list(LANGS)

