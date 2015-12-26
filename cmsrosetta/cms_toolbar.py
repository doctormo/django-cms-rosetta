#
# Copyright 2015, Martin Owens <doctormo@gmail.com>
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
Fix some issues in django-cms for translations with rosetta.
"""

from django.utils.translation import ugettext_lazy as _

from cms.models import Page
from cms.cms_toolbars import PageToolbar, PlaceholderToolbar
from cms.toolbar_pool import toolbar_pool
from cms.toolbar.toolbar import CMSToolbar

def pages(self):
    if self.publisher_is_draft:
        return (self, self.publisher_public)
    return (self.publisher_draft, self)
Page.pages = pages

def auto_translate(self, language):
    # Not checking public for languages means auto is default
    if not self.pages()[0]:
        return False
    languages = str(self.pages()[0].languages).split(',')
    return str(language) not in languages
Page.auto_translate = auto_translate

def auto_empty(self, language):
    if not self.pages()[1]:
        return False
    languages = str(self.pages()[1].languages).split(',')
    return str(language) not in languages
Page.auto_empty = auto_empty

def tb_auto_translate(self):
    if self.request.current_page:
        return self.request.current_page.auto_translate(self.language)
CMSToolbar.auto_translate = property(tb_auto_translate)

class NewPhTb(PlaceholderToolbar):
    def add_structure_mode_item(self, *args, **kwargs):
        if not self.toolbar.auto_translate:
            super(NewPhTb, self).add_structure_mode_item(*args, **kwargs)

class NewPageTb(PageToolbar):
    def add_draft_live(self, *args, **kwargs):
        return self.add_draft_live_item(
            template='cms/toolbar/items/live_draft_translate.html')

    def add_publish_button(self, *args, **kwargs):
        if not self.toolbar.auto_translate:
            super(NewPageTb, self).add_publish_button(*args, **kwargs)

# Remove existing page toolbar
toolbar_pool.unregister(PlaceholderToolbar)
toolbar_pool.register(NewPhTb)
toolbar_pool.unregister(PageToolbar)
toolbar_pool.register(NewPageTb)

from cms.templatetags.cms_admin import TreePublishRow
from cms.utils.compat.dj import force_unicode
from django.utils.safestring import mark_safe

old_render = TreePublishRow.render_tag

def render_tag(self, context, page, language):
    if page.auto_translate(language) and not page.auto_empty(language):
        return mark_safe('<span style="background-color:#ad7fa8;" class="%s" title="%s"></span>' % (
            'translated', force_unicode(_('Managed Translation'))))
    return old_render(self, context, page, language)

TreePublishRow.render_tag = render_tag

