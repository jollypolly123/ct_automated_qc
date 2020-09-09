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
    path('view_template', views.view_template, name='view_template'),
    path('upload', views.upload_image, name='image_upload'),
    path('images', views.display_image, name='images'),
    path('activities', views.activities_page, name='activities'),
    path('database', views.database_page, name='database'),
    path('test/<slug:slug>/<slug:test_name>', views.test, name='test'),
    path('image/<slug:slug>', views.display_header, name='display_header'),
    path('table_travel', views.table_travel, name='table_travel'),
    path('scout_prescription', views.scout_prescription, name='scout_prescription'),
    path('slice_thickness', views.slice_thickness, name='slice_thickness'),
    path('ct_number_accuracy', views.ct_number_accuracy, name='ct_number_accuracy'),
    path('low_contrast', views.low_contrast, name='low_contrast'),
    path('ct_number', views.ct_number, name='ct_number'),
    path('in_plane', views.in_plane, name='in_plane'),
    path('high_contrast', views.high_contrast, name='high_contrast'),
    path('radiation_beam', views.radiation_beam, name='radiation_beam'),
    path('kvp', views.kvp, name='kvp'),
    path('ct_dosimetry', views.ct_dosimetry, name='ct_dosimetry'),
    path('soft_copy', views.soft_copy, name='soft_copy'),
    path('deleted', views.delete_files, name='delete_files'),
]
