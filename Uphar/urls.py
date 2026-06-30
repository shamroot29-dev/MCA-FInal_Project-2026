from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',include(('User_Master.urls','user'))),
    path('guide/',include(('guide.urls','guide'))),
    path('med/',include(('med.urls','med'))),
    path('Chemist_Master/',include(('Chemist_Master.urls','chemist'))),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
