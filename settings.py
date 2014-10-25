
from django.conf import settings

# Number of messages to display per page.
MESSAGES_PER_PAGE = 10

# Enable Google translation suggestions
ENABLE_TRANSLATION_SUGGESTIONS = False

# Displays this language beside the original MSGID in the admin
MAIN_LANGUAGE = None

# Change these if the source language in your PO files isn't English
MESSAGES_SOURCE_LANGUAGE_CODE = 'en'
MESSAGES_SOURCE_LANGUAGE_NAME = 'English'

ACCESS_CONTROL_FUNCTION = None

WSGI_AUTO_RELOAD = False
UWSGI_AUTO_RELOAD = False


# Exclude applications defined in this list from being translated
EXCLUDED_APPLICATIONS = ()

# Line length of the updated PO file
POFILE_WRAP_WIDTH = 78

# Storage class to handle temporary data storage
STORAGE_CLASS = None

# Allow overriding of the default filenames, you mostly won't need to change this
POFILENAMES = ('django.po', 'djangojs.po')

CACHE_NAME = 'rosetta' in settings.CACHES and 'rosetta' or 'default'

# Require users to be authenticated (and Superusers or in group "translators").
# Set this to False at your own risk
REQUIRES_AUTH = True


# Get all our overloaded settings and all of django's globals
for (name, default) in locals().items():
    locals()[name] = getattr(settings, 'ROSETTA_'+name, default)
