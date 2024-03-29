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
    path('ct_protocol', views.ct_protocol, name='ct_protocol'),
    path('table_travel', views.table_travel, name='table_travel'),
    path('scout_prescription', views.scout_prescription, name='scout_prescription'),
    path('slice_thickness', views.slice_thickness, name='slice_thickness'),
    path('ct_number_accuracy', views.ct_number_accuracy, name='ct_number_accuracy'),
    path('ct_number_accuracy/<slug:slug>', views.display_mod_one_header, name='display_mod_one_header'),
    path('low_contrast', views.low_contrast, name='low_contrast'),
    path('low_contrast/<slug:slug>', views.display_mod_two_header, name='display_mod_two_header'),
    path('ct_number', views.ct_number, name='ct_number'),
    path('ct_number/<slug:slug>', views.display_mod_three_header, name='display_mod_three_header'),
    path('in_plane', views.in_plane, name='in_plane'),
    path('high_contrast', views.high_contrast, name='high_contrast'),
    path('final_report', views.final_report, name='final_report'),
    path('radiation_beam', views.radiation_beam, name='radiation_beam'),
    path('kvp', views.kvp, name='kvp'),
    path('ct_dosimetry', views.ct_dosimetry, name='ct_dosimetry'),
    path('soft_copy', views.soft_copy, name='soft_copy'),
    path('water_ct', views.water_ct, name='water_ct'),
    path('water_ct/<slug:slug>', views.display_water_header, name='display_water_header'),
    path('technologist_qc', views.technologist_qc, name='technologist_qc'),
    path('technologist_reports', views.technologist_reports, name='technologist_reports'),
    path('technologist_report/<slug:slug>', views.technologist_report, name='technologist_report'),
    path('download_ct_qc_report', views.download_ct_qc_report, name='download_ct_qc_report'),
    path('download_then_dashboard', views.download_then_dashboard, name='download_then_dashboard'),
    path('deleted', views.delete_files, name='delete_files'),
]
