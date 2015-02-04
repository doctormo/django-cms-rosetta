
__all__ = ('get_path', 'cache', 'p_cache')

from django.utils.importlib import import_module
from os.path import *

from .settings import settings, CACHE_NAME

from django.core.cache import get_cache
cache = get_cache(CACHE_NAME)

get_path = lambda p: normpath(abspath(isfile(p) and dirname(p) or p))
PROJECT_PATH = get_path(import_module(settings.SETTINGS_MODULE).__file__)

def no_change(v):
    return v

def p_cache(time_limit, key=None, kind=no_change):
    def _outer(f):
        _key = key or f.__name__
        def _inner(*args, **kwargs):
            if not cache.get(_key):
                cache.set(key, kind(f(*args, **kwargs)), time_limit)
            return cache.get(_key)
        return _inner
    return _outer

@p_cache(60 * 60, 'rosetta_locale_paths', list)
def locale_dirs():
    for path in getattr(settings, 'LOCALE_PATHS', ()) + (
              os.path.join(PROJECT_PATH, 'locale'),
              os.path.join(PROJECT_PATH, '..', 'locale')):
        yield (path, 'project')

    for path in EXTRA_PATHS:
        yield (path, 'other')

    for root, dirnames, filename in os.walk(get_path(django.__file__)):
        if 'locale' in dirnames and 'contrib' not in root:
            yield (os.path.join(root, 'locale'), 'django')

    # project/app/locale
    for appname in settings.INSTALLED_APPS:
        if EXCLUDED_APPLICATIONS and appname in EXCLUDED_APPLICATIONS:
            continue
        apppath = os.path.join(get_path(import_module(appname).__file__), 'locale')

        if 'contrib' in apppath and 'django' in apppath:
            yield (apppath, 'django') # Used to be 'contrib'
        elif PROJECT_PATH not in apppath:
            yield (apppath, 'third-party')
        else:
            yield (apppath, 'project')


