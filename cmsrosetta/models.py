from django.db import models
# Create your models here.

from cms.models import CMSPlugin

class TranslatedContentPlugin(CMSPlugin):
    render_template = 'foo.html'

    def __unicode__(self):
        return u"..."

