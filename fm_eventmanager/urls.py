from django.conf.urls import include, url
#from django.urls import include, path  # For django 2.0
from django.contrib import admin
from django.conf import settings
import django_u2f.urls

admin.autodiscover()

urlpatterns = [
    url(r'^registration/', include('registration.urls')),
    url(r'^admin/', admin.site.urls),
    url(r'^u2f/', include(django_u2f.urls, namespace='u2f')),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        url(r'^__debug__/', include(debug_toolbar.urls)),

        # For django 2.0:
        #path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
