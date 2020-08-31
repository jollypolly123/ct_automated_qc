# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2019 - present AppSeed.us
"""

from django.contrib import admin
from django.urls import path, include  # add this
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve

urlpatterns = [
    path('admin', admin.site.urls),
    path('accounts', include('django.contrib.auth.urls')),
    path("", include("authentication.urls")),
    path("", include("app.urls")),
] + static(settings.MEDIA_URL, serve, document_root=settings.MEDIA_ROOT) \
              + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
