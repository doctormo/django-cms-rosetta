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

#from django.contrib.auth.decorators import user_passes_test
#from django.core.paginator import Paginator
#from django.core.urlresolvers import reverse
#from django.http import Http404, HttpResponseRedirect, HttpResponse
#from django.shortcuts import render_to_response
#from django.template import RequestContext
#from django.utils.encoding import iri_to_uri
#from django.utils.translation import ugettext_lazy as _
#from django.views.decorators.cache import never_cache

#from .signals import entry_changed, post_save
#from .storage import get_storage
#from .access import can_translate
#from .settings import *
#from .utils import fix_nls

#import json
#import re
#import unicodedata
#import hashlib
#import os
#import six

from django.views.generic.base import TemplateView
from django.shortcuts import redirect

from .mixins import TranslatorMixin
from request_tree import data_tree

class List(TemplateView, TranslatorMixin):
    template_name = 'rosetta/list.html'

    def get_context_data(self, **data):
        data = TranslatorMixin.get_context_data(self, **data)
        objects = self.locales
        if 'kind' in self.kwargs:
            data['kind'] = self.kwargs['kind']
            objects = objects[self.kwargs['kind']]
        data['objects'] = objects[self.language]
        return data

class Item(TemplateView, TranslatorMixin):
    template_name = 'rosetta/item.html'

    @data_tree
    def post(self, data, request, *args, **kwargs):
        """Save Data"""
        for (md5hash, datum) in data.items():
            if isinstance(datum, dict) and '5msg' in datum:
                self.pofile.update_entry(md5hash, **datum)
            #entry = self.pofile.find(md5hash, 'md5hash')
            #if not entry or 'msg' not in datum:
            #    continue
            #entry.set_msg(datum['msg'])
            #entry.set_flag('fuzzy', datum.get('fuzzy', 0))
        if 'page' in request.POST:
            request.page = int(request.POST['page'])
            context = self.get_context_data(**kwargs)
            return self.render_to_response(context)
        return redirect('rosetta')

    @property
    def pofile(self):
        return self.locales[self.kwargs['kind']][self.kwargs['page']][self.language]

    def get_context_data(self, **data):
        data = TranslatorMixin.get_context_data(self, **data)
        data['pofile'] = self.pofile
        data['page'] = self.request.page
        return data


class Download(Item):
    def dispatch(self):
        filename = "%s" % (self.kwargs['kind'], self.kwargs['page'], self.language)
        with open(self.pofile.fname, 'r') as fhl:
            response = HttpResponse(fhl.read())
        response['Content-Disposition'] = 'attachment; filename=%s.po' % filename
        response['Content-Type'] = 'text/x-gettext-translation'
        return response

class Upload(Item):
    def post(self):
        pass # Upload new po file replacement

"""
@never_cache
@user_passes_test(lambda user: can_translate(user), settings.LOGIN_URL)
def messages(request):
    "Displays a list of messages to be translated"
    storage = get_storage(request)
    query = ''
    if storage.has('rosetta_i18n_fn'):
        rosetta_i18n_fn = storage.get('rosetta_i18n_fn')
        rosetta_i18n_app = 'XXX' #get_app_name(rosetta_i18n_fn)
        rosetta_i18n_lang_code = storage.get('rosetta_i18n_lang_code')
        rosetta_i18n_lang_bidi = rosetta_i18n_lang_code.split('-')[0] in settings.LANGUAGES_BIDI
        rosetta_i18n_write = storage.get('rosetta_i18n_write', True)
        if rosetta_i18n_write:
            rosetta_i18n_pofile = pofile(rosetta_i18n_fn, wrapwidth=POFILE_WRAP_WIDTH)
            for entry in rosetta_i18n_pofile:
                entry.md5hash = hashlib.md5(
                    (six.text_type(entry.msgid) +
                    six.text_type(entry.msgstr) +
                    six.text_type(entry.msgctxt or "")).encode('utf8')
                ).hexdigest()

        else:
            rosetta_i18n_pofile = storage.get('rosetta_i18n_pofile')

        if 'filter' in request.GET:
            if request.GET.get('filter') in ('untranslated', 'translated', 'fuzzy', 'all'):
                filter_ = request.GET.get('filter')
                storage.set('rosetta_i18n_filter', filter_)
                return HttpResponseRedirect(reverse('rosetta-home'))

        rosetta_i18n_filter = storage.get('rosetta_i18n_filter', 'all')

        if '_next' in request.POST:
                        storage.set('rosetta_last_save_error', True)

            if file_change and rosetta_i18n_write:
                try:
                    # Provide defaults in case authorization is not required.
                    request.user.first_name = getattr(request.user, 'first_name', 'Anonymous')
                    request.user.last_name = getattr(request.user, 'last_name', 'User')
                    request.user.email = getattr(request.user, 'email', 'anonymous@user.tld')

                    rosetta_i18n_pofile.metadata['Last-Translator'] = unicodedata.normalize('NFKD', u"%s %s <%s>" % (request.user.first_name, request.user.last_name, request.user.email)).encode('ascii', 'ignore')
                    rosetta_i18n_pofile.metadata['X-Translated-Using'] = u"django-rosetta %s" % VERSION
                    rosetta_i18n_pofile.metadata['PO-Revision-Date'] = timestamp_with_timezone()
                except UnicodeDecodeError:
                    pass

                try:
                    rosetta_i18n_pofile.save()
                    po_filepath, ext = os.path.splitext(rosetta_i18n_fn)
                    save_as_mo_filepath = po_filepath + '.mo'
                    rosetta_i18n_pofile.save_as_mofile(save_as_mo_filepath)

                    post_save.send(sender=None, language_code=rosetta_i18n_lang_code, request=request)
                    # Try auto-reloading via the WSGI daemon mode reload mechanism
                    if WSGI_AUTO_RELOAD and \
                        'mod_wsgi.process_group' in request.environ and \
                        request.environ.get('mod_wsgi.process_group', None) and \
                        'SCRIPT_FILENAME' in request.environ and \
                        int(request.environ.get('mod_wsgi.script_reloading', '0')):
                            try:
                                os.utime(request.environ.get('SCRIPT_FILENAME'), None)
                            except OSError:
                                pass
                    # Try auto-reloading via uwsgi daemon reload mechanism
                    if UWSGI_AUTO_RELOAD:
                        try:
                            import uwsgi
                            # pretty easy right?
                            uwsgi.reload()
                        except:
                            # we may not be running under uwsgi :P
                            pass

                except:
                    storage.set('rosetta_i18n_write', False)
                storage.set('rosetta_i18n_pofile', rosetta_i18n_pofile)

                # Retain query arguments
                query_arg = '?_next=1'
                if 'query' in request.GET or 'query' in request.POST:
                    query_arg += '&query=%s' % request.REQUEST.get('query')
                if 'page' in request.GET:
                    query_arg += '&page=%d&_next=1' % int(request.GET.get('page'))
                return HttpResponseRedirect(reverse('rosetta-home') + iri_to_uri(query_arg))
        rosetta_i18n_lang_code = storage.get('rosetta_i18n_lang_code')

        if 'query' in request.REQUEST and request.REQUEST.get('query', '').strip():
            query = request.REQUEST.get('query').strip()
            rx = re.compile(re.escape(query), re.IGNORECASE)
            paginator = Paginator([e for e in rosetta_i18n_pofile if not e.obsolete and rx.search(six.text_type(e.msgstr) + six.text_type(e.msgid) + u''.join([o[0] for o in e.occurrences]))], MESSAGES_PER_PAGE)
        else:
            if rosetta_i18n_filter == 'untranslated':
                paginator = Paginator(rosetta_i18n_pofile.untranslated_entries(), MESSAGES_PER_PAGE)
            elif rosetta_i18n_filter == 'translated':
                paginator = Paginator(rosetta_i18n_pofile.translated_entries(), MESSAGES_PER_PAGE)
            elif rosetta_i18n_filter == 'fuzzy':
                paginator = Paginator([e for e in rosetta_i18n_pofile.fuzzy_entries() if not e.obsolete], MESSAGES_PER_PAGE)
            else:
                paginator = Paginator([e for e in rosetta_i18n_pofile if not e.obsolete], MESSAGES_PER_PAGE)

        if 'page' in request.GET and int(request.GET.get('page')) <= paginator.num_pages and int(request.GET.get('page')) > 0:
            page = int(request.GET.get('page'))
        else:
            page = 1

        if '_next' in request.GET or '_next' in request.POST:
            page += 1
            if page > paginator.num_pages:
                page = 1
            query_arg = '?page=%d' % page
            return HttpResponseRedirect(reverse('rosetta-home') + iri_to_uri(query_arg))

        rosetta_messages = paginator.page(page).object_list
        main_language = None
        if MAIN_LANGUAGE and MAIN_LANGUAGE != rosetta_i18n_lang_code:
            for language in settings.LANGUAGES:
                if language[0] == MAIN_LANGUAGE:
                    main_language = _(language[1])
                    break

            fl = ("/%s/" % MAIN_LANGUAGE).join(rosetta_i18n_fn.split("/%s/" % rosetta_i18n_lang_code))
            po = pofile(fl)

            for message in rosetta_messages:
                message.main_lang = po.find(message.msgid).msgstr

        needs_pagination = paginator.num_pages > 1
        if needs_pagination:
            if paginator.num_pages >= 10:
                page_range = pagination_range(1, paginator.num_pages, page)
            else:
                page_range = range(1, 1 + paginator.num_pages)

        if storage.has('rosetta_last_save_error'):
            storage.delete('rosetta_last_save_error')
            rosetta_last_save_error = True
        else:
            rosetta_last_save_error = False

        return render_to_response('rosetta/pofile.html', dict(
            version=VERSION,
            MESSAGES_SOURCE_LANGUAGE_NAME=MESSAGES_SOURCE_LANGUAGE_NAME,
            ENABLE_TRANSLATION_SUGGESTIONS=ENABLE_TRANSLATION_SUGGESTIONS,
            rosetta_i18n_lang_name=_(storage.get('rosetta_i18n_lang_name')),
            rosetta_i18n_lang_code=rosetta_i18n_lang_code,
            rosetta_i18n_lang_bidi=rosetta_i18n_lang_bidi,
            rosetta_last_save_error=rosetta_last_save_error,
            rosetta_i18n_filter=rosetta_i18n_filter,
            rosetta_i18n_write=rosetta_i18n_write,
            rosetta_messages=rosetta_messages,
            page_range=needs_pagination and page_range,
            needs_pagination=needs_pagination,
            main_language=main_language,
            rosetta_i18n_app=rosetta_i18n_app,
            page=page,
            query=query,
            paginator=paginator,
            rosetta_i18n_pofile=rosetta_i18n_pofile
        ), context_instance=RequestContext(request))
    else:
        return list_languages(request, do_session_warn=True)


@never_cache
@user_passes_test(lambda user: can_translate(user), settings.LOGIN_URL)


@never_cache
@user_passes_test(lambda user: can_translate(user), settings.LOGIN_URL)
def list_languages(request, do_session_warn=False):
    "
    Lists the languages for the current project, the gettext catalog files
    that can be translated and their translation progress
    "
    storage = get_storage(request)
    languages = []

    if 'filter' in request.GET:
        storage.set('rosetta_i18n_catalog_filter', request.GET.get('filter'))
        return HttpResponseRedirect(reverse('rosetta-pick-file'))

    filter_mode = Mode(storage.get('rosetta_i18n_catalog_filter', 'project'))
    for language in settings.LANGUAGES:
        pos = find_pos(language[0], mode=filter_mode)
        if len(pos):
            languages.append( (language[0], _(language[1]), pofiles(pos)) )

    do_session_warn = do_session_warn and 'SessionRosettaStorage' in str(STORAGE_CLASS) and 'signed_cookies' in settings.SESSION_ENGINE

    return render_to_response('rosetta/languages.html', dict(
        version=VERSION,
        do_session_warn=do_session_warn,
        languages=languages,
        filter_mode=filter_mode,
    ), context_instance=RequestContext(request))


@never_cache
@user_passes_test(lambda user: can_translate(user), settings.LOGIN_URL)
def lang_sel(request, langid, idx):
    "
    Selects a file to be translated
    "
    storage = get_storage(request)
    if langid not in [l[0] for l in settings.LANGUAGES]:
        raise Http404
    else:
        po = pofiles(find_pos(langid, mode=Mode(storage.get('rosetta_i18n_catalog_filter', 'project'))))[int(idx)]

        storage.set('rosetta_i18n_lang_code', langid)
        storage.set('rosetta_i18n_lang_name', six.text_type([l[1] for l in settings.LANGUAGES if l[0] == langid][0]))
        storage.set('rosetta_i18n_fn', po.filename)

        for entry in po:
            entry.md5hash = hashlib.new('md5',
                (six.text_type(entry.msgid) +
                six.text_type(entry.msgstr) +
                six.text_type(entry.msgctxt or "")).encode('utf8')
            ).hexdigest()

        storage.set('rosetta_i18n_pofile', po)
        try:
            os.utime(po.filename, None)
            storage.set('rosetta_i18n_write', True)
        except OSError:
            storage.set('rosetta_i18n_write', False)

        return HttpResponseRedirect(reverse('rosetta-home'))


def translate_text(request):
    language_from = request.GET.get('from', None)
    language_to = request.GET.get('to', None)
    text = request.GET.get('text', None)

    if language_from == language_to:
        data = {'success': True, 'translation': text}
    else:
        # run the translation:
        AZURE_CLIENT_ID = getattr(settings, 'AZURE_CLIENT_ID', None)
        AZURE_CLIENT_SECRET = getattr(settings, 'AZURE_CLIENT_SECRET', None)

        translator = Translator(AZURE_CLIENT_ID, AZURE_CLIENT_SECRET)

        try:
            translated_text = translator.translate(text, language_to)
            data = {'success': True, 'translation': translated_text}
        except TranslateApiException as e:
            data = {'success': False, 'error': "Translation API Exception: {0}".format(e.message)}

    return HttpResponse(json.dumps(data), mimetype='application/json')
"""

