
try:
    from django.conf.urls import patterns, url, include
except ImportError:
    from django.conf.urls.defaults import patterns, url, include

from .views import *

def url_tree(regex, *urls):
    return url(regex, include(patterns('', *urls)))

urlpatterns = patterns('cmsrosetta.views',
  url(r'^$',                  Stats.as_view(),      name='rosetta'),
  url(r'^all/$',              List.as_view(),       name='rosetta-list'),
  url_tree(r'^(?P<kind>[\w-]+)/',
    url(r'^$',                List.as_view(),       name='rosetta-list'),
    url_tree(r'^(?P<page>.*)/',
      url(r'^download/$',     Download.as_view(),   name='rosetta-download'),
      url(r'^upload/$',       Upload.as_view(),     name='rosetta-upload'),
      url(r'^$',              Item.as_view(),       name='rosetta-file'),
    ),
  ),
)
