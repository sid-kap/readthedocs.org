from django.conf.urls import url, patterns, include

from rest_framework import routers

from .views.model_views import BuildViewSet, ProjectViewSet, NotificationViewSet, VersionViewSet
from readthedocs.comments.views import CommentViewSet

router = routers.DefaultRouter()
router.register(r'build', BuildViewSet)
router.register(r'version', VersionViewSet)
router.register(r'project', ProjectViewSet)
router.register(r'notification', NotificationViewSet)
router.register(r'comments', CommentViewSet, base_name="comments")

urlpatterns = patterns(
    '',
    url(r'^', include(router.urls)),
    url(r'embed/', 'readthedocs.restapi.views.core_views.embed', name='embed'),
    url(r'docurl/', 'readthedocs.restapi.views.core_views.docurl', name='docurl'),
    url(r'cname/', 'readthedocs.restapi.views.core_views.cname', name='cname'),
    url(r'footer_html/', 'readthedocs.restapi.views.footer_views.footer_html', name='footer_html'),
    url(r'index_search/',
        'readthedocs.restapi.views.search_views.index_search',
        name='index_search'),
    url(r'search/$', 'readthedocs.restapi.views.search_views.search', name='api_search'),
    url(r'search/project/$',
        'readthedocs.restapi.views.search_views.project_search',
        name='api_project_search'),
    url(r'search/section/$',
        'readthedocs.restapi.views.search_views.section_search',
        name='api_section_search'),
)
