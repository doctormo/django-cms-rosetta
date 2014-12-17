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

from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import TemplateView
from django.shortcuts import redirect

from .mixins import TranslatorMixin
from request_tree import data_tree

class Stats(TemplateView, TranslatorMixin):
    template_name = 'rosetta/home.html'

    def get_context_data(self, **data):
        data = TranslatorMixin.get_context_data(self, **data)
        data['language'] = None
        data['languages'] = self.locales.progress()
        return data

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
        if 'save' in request.POST:
            self.save_pofile(data)
            request.page = int(request.POST['save'])
        elif 'page' in request.POST:
            request.page = int(request.POST['page'])


        if not request.page:
            return redirect('rosetta')

        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def save_pofile(self, data):
        for (md5hash, datum) in data.items():
            if isinstance(datum, dict) and '5msg' in datum:
                self.pofile.update_entry(md5hash, **datum)
            entry = self.pofile.find(md5hash, 'md5hash')
            if not entry or 'msg' not in datum:
                continue
            entry.set_msg(datum['msg'])
            entry.set_flag('fuzzy', datum.get('fuzzy', 0))
        updates = self.pofile.has_updates
        if updates:
            messages.success(self.request, _("Saved %d translation entries") % updates)
            self.pofile.save()
        else:
            messages.warning(self.request, _("No changes to save, so skipped saving anything."))

    @property
    def pofile(self):
        return self.locales[self.kwargs['kind']][self.kwargs['page']][self.language]

    def get_context_data(self, **data):
        data = TranslatorMixin.get_context_data(self, **data)
        data['filter']  = self.datum('filter', 'untranslated')
        data['entries'] = self.pofile.get_filter(data['filter'])
        data['pofile']  = self.pofile
        data['page']    = self.request.page
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

