from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

handler404 = 'core.views.handler404'
handler403 = 'core.views.handler403'
handler500 = 'core.views.handler500'

urlpatterns = [
    path('', include('posts.urls', namespace='posts')),
    path('admin/', admin.site.urls),
    path('auth/', include('users.urls')),
    path('auth/', include('django.contrib.auth.urls')),
    path('about/', include('about.urls', namespace='about')),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += (path('__debug__/', include(debug_toolbar.urls)),)
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
