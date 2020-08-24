# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2019 - present AppSeed.us
"""

from django.urls import path, re_path
from django.conf.urls import url

from . import views

app_name = 'app'

urlpatterns = [
    # Matches any html file 
    re_path(r'^.*\.html', views.pages, name='pages'),
    # The home page
    path('', views.dashboard_page, name='dashboard'),
    path('upload', views.upload_image, name='image_upload'),
    path('images', views.display_image, name='images'),
    path('activities', views.activities_page, name='activities'),
    path('database', views.database_page, name='database'),
    path('test/<slug:slug>/<slug:test_name>', views.test, name='test'),
    path('image/<slug:slug>', views.display_header, name='display_header'),
    path('deleted', views.delete_files, name='delete_files'),
]
