
__all__ = ('get_path', 'cache', 'p_cache')

from django.utils.importlib import import_module
from os.path import *

import types
import settings

from django.core.cache import get_cache
cache = get_cache(settings.CACHE_NAME)

get_path = lambda p: normpath(abspath(isfile(p) and dirname(p) or p))

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

