from django.utils.translation import ugettext_lazy as _
from django.shortcuts import get_object_or_404

from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

from .models import TranslatedContentPlugin

from inkscape.settings import DEBUG

class CMSTranslatedContentPlugin(CMSPluginBase):
    model = TranslatedContentPlugin
    name  = _('Translated Content')
    cache = DEBUG

    def render(self, context, instance, placeholder):
        context['ex'] = instance.placeholder.get_plugins('en')[0].get_plugin_instance()[0].get_translatable_content()
        return context


plugin_pool.register_plugin(CMSTranslatedContentPlugin)

