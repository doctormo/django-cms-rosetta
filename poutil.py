from datetime import datetime

from django.utils.translation import ugettext_lazy as _
from django.core.cache import get_cache

import django
import os

from .utils import *
from .settings import *

from polib import POFile, pofile as pobase

try:
    from django.utils import timezone
except:
    timezone = None

LANGS = dict(settings.LANGUAGES)

class NewPoFile(POFile):
    @property
    def filename(self):
        return os.path.realpath(getattr(self, '_filename', 'UNKNOWN'))

    @property
    def path(self):
        f = self.filename
        if 'site-packages' in f:
            return '@' + f.split('site-packages')[-1]
        return os.path.realpath(f).replace(settings.PROJECT_PATH, '~')

    @property
    def name(self):
        f = self.filename.replace('/locale', '')
        return f.split("/")[-4].replace('_', ' ') + (
          'djangojs.po' in f and ' (Javascript)' or '')

    @property
    def lang(self):
        return self.filename.split('/locale/', 1)[-1].split('/')[0]

    @property
    def language(self):
        return _(LANGS.get(self.lang, 'Unknown'))

    def progress(self):
        return (
          ('done', float(len(self.translated_entries())) / len(self) * 99),
          ('fuzzy', float(len(self.fuzzy_entries())) / len(self) * 99),
          ('obsolete', float(len(self.obsolete_entries()))  / len(self) * 99),
        )



def pofile(pofile, *args, **kwargs):
    kwargs['klass'] = NewPoFile
    ret = pobase(pofile, *args, **kwargs)
    ret._filename = pofile
    return ret

def pofiles(pos):
    return sorted([pofile(l) for l in pos], key=lambda app: app.name)


def timestamp_with_timezone(dt=None):
    """
    Return a timestamp with a timezone for the configured locale.  If all else
    fails, consider localtime to be UTC.
    """
    dt = dt or datetime.now()
    if timezone is None:
        return dt.strftime('%Y-%m-%d %H:%M%z')
    if not dt.tzinfo:
        tz = timezone.get_current_timezone()
        if not tz:
            tz = timezone.utc
        dt = dt.replace(tzinfo=timezone.get_current_timezone())
    return dt.strftime("%Y-%m-%d %H:%M%z")


class Mode(list):
    """Controls the categorisation of po files and the selectable mode to
       filter for them"""
    def __init__(self, value):
        self.value = value
        self.append('all')

    def is_(self, b):
        if b not in self:
            self.append( b )
        return self.value in (b, 'all')

    def __eq__(self, b):
        return b == self.value


@p_cache(60 * 60, 'rosetta_django_paths', list)
def django_dirs():
    for root, dirnames, filename in os.walk(os.path.abspath(os.path.dirname(django.__file__))):
        if 'locale' in dirnames:
            yield os.path.join(root, 'locale')


def find_pos(lang, mode):
    """
    scans a couple possible repositories of gettext catalogs for the given
    language code
    """
    paths = []

    # project/locale
    parts = settings.SETTINGS_MODULE.split('.')
    project = __import__(parts[0], {}, {}, [])
    p_path = os.path.abspath(os.path.dirname(project.__file__))
    abs_project_path = os.path.normpath(p_path)
    if mode.is_('project'):
        paths += [os.path.join(p_path, 'locale'), os.path.join(p_path, '..', 'locale')]
        paths += list(getattr(settings, 'LOCALE_PATHS', ()))

    # extra/locale
    if mode.is_('extra'):
        paths += list(EXTRA_PATHS)

    # django/locale
    if mode.is_('django'):
        paths += django_dirs()

    # settings
    for localepath in settings.LOCALE_PATHS:
        if os.path.isdir(localepath):
            paths.append(localepath)

    # project/app/locale
    for appname in settings.INSTALLED_APPS:
        if EXCLUDED_APPLICATIONS and appname in EXCLUDED_APPLICATIONS:
            continue
        p = appname.rfind('.')
        if p >= 0:
            app = getattr(__import__(appname[:p], {}, {}, [str(appname[p + 1:])]), appname[p + 1:])
        else:
            app = __import__(appname, {}, {}, [])

        apppath = os.path.normpath(os.path.abspath(os.path.join(os.path.dirname(app.__file__), 'locale')))

        # django apps
        if 'contrib' in apppath and 'django' in apppath and not mode.is_('django'):
            continue

        # third party external
        if not mode.is_('third-party') and abs_project_path not in apppath:
            continue

        # local apps
        if not mode.is_('project') and abs_project_path in apppath:
            continue

        if os.path.isdir(apppath):
            paths.append(apppath)

    ret = set()
    langs = [lang, ]
    if u'-' in lang:
        _l, _c = map(lambda x: x.lower(), lang.split(u'-'))
        langs += [u'%s_%s' % (_l, _c), u'%s_%s' % (_l, _c.upper()), ]
    elif u'_' in lang:
        _l, _c = map(lambda x: x.lower(), lang.split(u'_'))
        langs += [u'%s-%s' % (_l, _c), u'%s-%s' % (_l, _c.upper()), ]

    paths = map(os.path.normpath, paths)
    paths = list(set(paths))
    for path in paths:
        if not os.path.isdir(path):
            continue
        for lang_ in langs:
            dirname = os.path.join(path, lang_, 'LC_MESSAGES')
            for fn in POFILENAMES:
                filename = os.path.join(dirname, fn)
                if os.path.isfile(filename):
                    ret.add(os.path.abspath(filename))
    return list(sorted(ret))


def pagination_range(first, last, current):
    r = []

    r.append(first)
    if first + 1 < last:
        r.append(first + 1)

    if current - 2 > first and current - 2 < last:
        r.append(current - 2)
    if current - 1 > first and current - 1 < last:
        r.append(current - 1)
    if current > first and current < last:
        r.append(current)
    if current + 1 < last and current + 1 > first:
        r.append(current + 1)
    if current + 2 < last and current + 2 > first:
        r.append(current + 2)

    if last - 1 > first:
        r.append(last - 1)
    r.append(last)

    r = list(set(r))
    r.sort()
    prev = 10000
    for e in r[:]:
        if prev + 1 < e:
            try:
                r.insert(r.index(e), '...')
            except ValueError:
                pass
        prev = e
    return r
