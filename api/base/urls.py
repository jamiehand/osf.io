from django.conf import settings
from django.conf.urls import include, url, patterns
# from django.contrib import admin
from django.conf.urls.static import static
from settings import API_PREFIX


from . import views

base_pattern = '^{}'.format(API_PREFIX)

urlpatterns = [
    ### API ###
    url(base_pattern,
        include(patterns('',
                         url(r'^$', views.root),  # TODO I think this is becoming '//v2' but should be '/v2'
                         url(r'^nodes/', include('api.nodes.urls', namespace='nodes')),
                         url(r'^users/', include('api.users.urls', namespace='users')),
                         url(r'^docs/', include('rest_framework_swagger.urls')),
                         ))
        )
]

urlpatterns += static('/static/', document_root=settings.STATIC_ROOT)
