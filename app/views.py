# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2019 - present AppSeed.us
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.core.files import File
from django.template import loader
from django.http import HttpResponse
from django import template
from pydicom import dcmread
from io import BytesIO
import numpy as np
from PIL import Image
from base64 import b64encode

from .models import Document, Report
from .forms import DocumentForm
from . import qa_tests_8_3
from . import handle_excel

import pprint, os


@login_required(login_url="/login/")
def index(request):  # useless
    return render(request, "index.html")


@login_required(login_url="/login/")
def pages(request):
    context = {}
    # All resource paths end in .html.
    # Pick out the html file name from the url. And load that template.
    try:
        
        load_template = request.path.split('/')[-1]
        html_template = loader.get_template(load_template)
        return HttpResponse(html_template.render(context, request))
        
    except template.TemplateDoesNotExist:

        html_template = loader.get_template('error-404.html')
        return HttpResponse(html_template.render(context, request))

    except:
        html_template = loader.get_template('error-500.html')
        return HttpResponse(html_template.render(context, request))


def dashboard_page(request):
    return render(request, 'dashboard_page.html')


def upload_image(request):
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        files = request.FILES.getlist('docfile')
        if form.is_valid():
            for f in files:
                file_instance = Document(docfile=f)
                file_instance.save()
            return redirect('app:images')
    else:
        form = DocumentForm()
    return render(request, 'index.html', {
        'form': form
    })


def display_image(request):
    if request.method == 'GET':
        for row in Document.objects.all().reverse():
            if Document.objects.filter(name=row.name).count() > 1:
                row.delete()
        all_doc = Document.objects.all()
        return render(request, 'index.html',
                      {'images': all_doc})


def display_header(request, slug):
    item = Document.objects.get(slug=slug).docfile
    doc = dcmread(item.open(), force=True)
    doc_keys = doc.dir()
    elements = {key: getattr(doc, key) for key in doc_keys}
    elements = {key: val for key, val in elements.items() if type(val) is not bytes and type(val) is not dict}

    all_doc = Document.objects.all()

    return render(request, 'index.html',
                  {'images': all_doc,
                   'header': elements})


def test(request, slug, test_name):
    test_types = {'ct1': ['CT Number Accuracy', qa_tests_8_3.hu_reproducibility],
                  'ct2': ['Low Contrast Resolution', qa_tests_8_3.low_contrast_resolution],
                  'ct3': ['CT Number Uniformity Assessment', qa_tests_8_3.uniformity_assessment],
                  'ct4': ['High Contrast Spatial Resolution', qa_tests_8_3.get_study_information],
                  'mri1': ['Default', qa_tests_8_3.get_study_information]}
    item = Document.objects.get(slug=slug).docfile
    doc = dcmread(item.open(), force=True)

    try:
        res, image = test_types[test_name][1](doc)
    except:
        return render(request, 'error.html')

    image -= np.min(image)
    image = np.divide(image, np.max(image))
    image = np.multiply(image, 255).astype('uint8')

    image = Image.fromarray(image, 'L')

    byte_io = BytesIO()
    image.save(byte_io, 'PNG')

    encoded = b64encode(byte_io.getvalue()).decode('ascii')
    return render(request, 'acr_ct.html',
                  {'test_name': test_types[test_name][0],
                   'results': res,
                   'image': encoded})


def activities_page(request):

    all_doc = Document.objects.all()

    return render(request, 'activities_page.html',
                  {'images': all_doc})


def database_page(request):

    all_doc = Document.objects.all()

    return render(request, 'database_page.html',
                  {'images': all_doc})


def delete_files(request):
    Document.objects.all().delete()
    Report.objects.all().delete()
    return redirect('app:dashboard')


def view_template(request):
    info = {}
    report = handle_excel.get_template()
    complete_report = handle_excel.input_data(report, info)
    return render(request, "template.html")


def table_travel(request):
    if request.method == 'POST':
        request.session['first'] = request.POST.get("first", "No Value")
        request.session['fourth'] = request.POST.get("fourth", "No Value")
        request.session['full_extension'] = request.POST.get("full_extension", "No Value")
        return redirect('scout_prescription_and_alignment_light_accuracy.html')
    else:
        return redirect('table_travel_and_return_to_fixed_position_accuracy.html')


def scout_prescription(request):
    if request.method == 'POST':
        request.session['first_scout'] = request.POST.get("first_scout", "No Value")
        request.session['first_axial'] = request.POST.get("first_axial", "No Value")
        request.session['fourth_scout'] = request.POST.get("fourth_scout", "No Value")
        request.session['fourth_axial'] = request.POST.get("fourth_axial", "No Value")
        request.session['first_laser'] = request.POST.get("first_laser", "No Value")
        request.session['first_slice'] = request.POST.get("first_slice", "No Value")
        request.session['fourth_laser'] = request.POST.get("fourth_laser", "No Value")
        request.session['fourth_slice'] = request.POST.get("fourth_slice", "No Value")
        return redirect('slice_thickness_accuracy.html')
    else:
        return redirect('scout_prescription_and_alignment_light_accuracy.html')


def slice_thickness(request):
    if request.method == 'POST':
        request.session['top_one_mm'] = request.POST.get("top_one_mm", "No Value")
        request.session['top_two_mm'] = request.POST.get("top_two_mm", "No Value")
        request.session['top_five_mm'] = request.POST.get("top_five_mm", "No Value")
        request.session['top_seven_mm'] = request.POST.get("top_seven_mm", "No Value")
        request.session['top_ten_mm'] = request.POST.get("top_ten_mm", "No Value")
        request.session['bot_one_mm'] = request.POST.get("bot_one_mm", "No Value")
        request.session['bot_two_mm'] = request.POST.get("bot_two_mm", "No Value")
        request.session['bot_five_mm'] = request.POST.get("bot_five_mm", "No Value")
        request.session['bot_seven_mm'] = request.POST.get("bot_seven_mm", "No Value")
        request.session['bot_ten_mm'] = request.POST.get("bot_ten_mm", "No Value")
        return redirect('ct_number_accuracy.html')
    else:
        return redirect('slice_thickness_accuracy.html')


def ct_number_accuracy(request):
    if request.method == 'POST':

        return redirect('low_contrast_performance.html')
    else:
        return redirect('ct_number_accuracy.html')


def low_contrast(request):
    if request.method == 'POST':
        return redirect('ct_number_uniformity_and_artifact_evaluation.html')
    else:
        return redirect('low_contrast_performance.html')


def ct_number(request):
    if request.method == 'POST':
        return redirect('in-plane_distance_accuracy.html')
    else:
        return redirect('ct_number_uniformity_and_artifact_evaluation.html')


def in_plane(request):
    if request.method == 'POST':
        request.session['adult_head_physical'] = request.POST.get("adult_head_physical", "No Value")
        request.session['adult_abd_physical'] = request.POST.get("adult_abd_physical", "No Value")
        request.session['ped_head_physical'] = request.POST.get("ped_head_physical", "No Value")
        request.session['ped_abd_physical'] = request.POST.get("ped_abd_physical", "No Value")
        request.session['adult_head_measured'] = request.POST.get("adult_head_measured", "No Value")
        request.session['adult_abd_measured'] = request.POST.get("adult_abd_measured", "No Value")
        request.session['ped_head_measured'] = request.POST.get("ped_head_measured", "No Value")
        request.session['ped_abd_measured'] = request.POST.get("ped_abd_measured", "No Value")
        return redirect('high_contrast_resolution.html')
    else:
        return redirect('plane_distance_accuracy.html')


def high_contrast(request):
    if request.method == 'POST':
        request.session['ah_visible'] = request.POST.get("ah_visible", "No Value")
        request.session['aa_visible'] = request.POST.get("aa_visible", "No Value")
        request.session['ph_visible'] = request.POST.get("ph_visible", "No Value")
        request.session['pa_visible'] = request.POST.get("pa_visible", "No Value")
        request.session['hrc_visible'] = request.POST.get("hrc_visible", "No Value")
        request.session['ah_50'] = request.POST.get("ah_50", "No Value")
        request.session['aa_50'] = request.POST.get("aa_50", "No Value")
        request.session['ph_50'] = request.POST.get("ph_50", "No Value")
        request.session['pa_50'] = request.POST.get("pa_50", "No Value")
        request.session['hrc_50'] = request.POST.get("hrc_50", "No Value")
        request.session['ah_10'] = request.POST.get("ah_10", "No Value")
        request.session['aa_10'] = request.POST.get("aa_10", "No Value")
        request.session['ph_10'] = request.POST.get("ph_10", "No Value")
        request.session['pa_10'] = request.POST.get("pa_10", "No Value")
        request.session['hrc_10'] = request.POST.get("hrc_10", "No Value")
        return redirect('radiation_beam_width.html')
    else:
        return redirect('high_contrast_resolution.html')


def radiation_beam(request):
    if request.method == 'POST':
        request.session['n_1'] = request.POST.get("n_1", "No Value")
        request.session['n_2'] = request.POST.get("n_2", "No Value")
        request.session['n_3'] = request.POST.get("n_3", "No Value")
        request.session['n_4'] = request.POST.get("n_4", "No Value")
        request.session['n_5'] = request.POST.get("n_5", "No Value")
        request.session['t_1'] = request.POST.get("t_1", "No Value")
        request.session['t_2'] = request.POST.get("t_2", "No Value")
        request.session['t_3'] = request.POST.get("t_3", "No Value")
        request.session['t_4'] = request.POST.get("t_4", "No Value")
        request.session['t_5'] = request.POST.get("t_5", "No Value")
        request.session['measured_1'] = request.POST.get("measured_1", "No Value")
        request.session['measured_2'] = request.POST.get("measured_2", "No Value")
        request.session['measured_3'] = request.POST.get("measured_3", "No Value")
        request.session['measured_4'] = request.POST.get("measured_4", "No Value")
        request.session['measured_5'] = request.POST.get("measured_5", "No Value")
        request.session['nom_1'] = request.POST.get("nom_1", "No Value")
        request.session['nom_2'] = request.POST.get("nom_2", "No Value")
        request.session['nom_3'] = request.POST.get("nom_3", "No Value")
        request.session['nom_4'] = request.POST.get("nom_4", "No Value")
        request.session['nom_5'] = request.POST.get("nom_5", "No Value")
        request.session['min_1'] = request.POST.get("min_1", "No Value")
        request.session['min_2'] = request.POST.get("min_2", "No Value")
        request.session['min_3'] = request.POST.get("min_3", "No Value")
        request.session['min_4'] = request.POST.get("min_4", "No Value")
        request.session['min_5'] = request.POST.get("min_5", "No Value")
        request.session['max_1'] = request.POST.get("max_1", "No Value")
        request.session['max_2'] = request.POST.get("max_2", "No Value")
        request.session['max_3'] = request.POST.get("max_3", "No Value")
        request.session['max_4'] = request.POST.get("max_4", "No Value")
        request.session['max_5'] = request.POST.get("max_5", "No Value")
        return redirect('kvp_accuracy_and_hvl_measurement.html')
    else:
        return redirect('radiation_beam_width.html')


def kvp(request):
    if request.method == 'POST':
        request.session['measured_80'] = request.POST.get("measured_80", "No Value")
        request.session['measured_100'] = request.POST.get("measured_100", "No Value")
        request.session['measured_120'] = request.POST.get("measured_120", "No Value")
        request.session['measured_140'] = request.POST.get("measured_140", "No Value")
        request.session['hvl_80'] = request.POST.get("hvl_80", "No Value")
        request.session['hvl_100'] = request.POST.get("hvl_100", "No Value")
        request.session['hvl_120'] = request.POST.get("hvl_120", "No Value")
        request.session['hvl_140'] = request.POST.get("hvl_140", "No Value")
        return redirect('ct_dosimetry.html')
    else:
        return redirect('kvp_accuracy_and_hvl_measurement.html')


def ct_dosimetry(request):
    if request.method == 'POST':
        request.session['ah_center_1'] = request.POST.get("ah_center_1", "No Value")
        request.session['ah_center_2'] = request.POST.get("ah_center_2", "No Value")
        request.session['ah_center_3'] = request.POST.get("ah_center_3", "No Value")
        request.session['ah_12_1'] = request.POST.get("ah_12_1", "No Value")
        request.session['ah_12_2'] = request.POST.get("ah_12_2", "No Value")
        request.session['ah_12_3'] = request.POST.get("ah_12_3", "No Value")
        request.session['aa_center_1'] = request.POST.get("aa_center_1", "No Value")
        request.session['aa_center_2'] = request.POST.get("aa_center_2", "No Value")
        request.session['aa_center_3'] = request.POST.get("aa_center_3", "No Value")
        request.session['aa_12_1'] = request.POST.get("aa_12_1", "No Value")
        request.session['aa_12_2'] = request.POST.get("aa_12_2", "No Value")
        request.session['aa_12_3'] = request.POST.get("aa_12_3", "No Value")
        request.session['ph_center_1'] = request.POST.get("ph_center_1", "No Value")
        request.session['ph_center_2'] = request.POST.get("ph_center_2", "No Value")
        request.session['ph_center_3'] = request.POST.get("ph_center_3", "No Value")
        request.session['ph_12_1'] = request.POST.get("ph_12_1", "No Value")
        request.session['ph_12_2'] = request.POST.get("ph_12_2", "No Value")
        request.session['ph_12_3'] = request.POST.get("ph_12_3", "No Value")
        request.session['pa_center_1'] = request.POST.get("pa_center_1", "No Value")
        request.session['pa_center_2'] = request.POST.get("pa_center_2", "No Value")
        request.session['pa_center_3'] = request.POST.get("pa_center_3", "No Value")
        request.session['pa_12_1'] = request.POST.get("pa_12_1", "No Value")
        request.session['pa_12_2'] = request.POST.get("pa_12_2", "No Value")
        request.session['pa_12_3'] = request.POST.get("pa_12_3", "No Value")
        return redirect('soft-copy_quality_control.html')
    else:
        return redirect('ct_dosimetry.html')


def soft_copy(request):
    if request.method == 'POST':
        request.session['gray_level'] = request.POST.get("gray_level", "No Value")
        request.session['patch'] = request.POST.get("patch", "No Value")
        request.session['line_pair'] = request.POST.get("line_pair", "No Value")
        request.session['upper_left'] = request.POST.get("upper_left", "No Value")
        request.session['upper_right'] = request.POST.get("upper_right", "No Value")
        request.session['bottom_right'] = request.POST.get("bottom_right", "No Value")
        request.session['bottom_left'] = request.POST.get("bottom_left", "No Value")
        request.session['cl_0'] = request.POST.get("cl_0", "No Value")
        request.session['cl_10'] = request.POST.get("cl_10", "No Value")
        request.session['cl_20'] = request.POST.get("cl_20", "No Value")
        request.session['cl_30'] = request.POST.get("cl_30", "No Value")
        request.session['cl_40'] = request.POST.get("cl_40", "No Value")
        request.session['cl_50'] = request.POST.get("cl_50", "No Value")
        request.session['cl_60'] = request.POST.get("cl_60", "No Value")
        request.session['cl_70'] = request.POST.get("cl_70", "No Value")
        request.session['cl_80'] = request.POST.get("cl_80", "No Value")
        request.session['cl_90'] = request.POST.get("cl_90", "No Value")
        request.session['cl_100'] = request.POST.get("cl_100", "No Value")
        input_data(request)
        return redirect('app:dashboard')
    else:
        return redirect('soft-copy_quality_control.html')


def input_data(request):
    cc_api_key = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiIxIiwianRpIjoiNGU3NGEyYzU5OTkxZmRmOWE0OTY2NjNhOGVhZ" \
                 "jFiOGE1YzBlMWQzOGUzMzhhYzBjYTJmZmFkMTdhNjJhNjg0ZThiOWM0MzY2ZWQ5YmU0YzciLCJpYXQiOjE2MDAxNDc0ODMsIm5" \
                 "iZiI6MTYwMDE0NzQ4MywiZXhwIjo0NzU1ODIxMDgzLCJzdWIiOiI0NDk5ODk2MCIsInNjb3BlcyI6WyJ1c2VyLnJlYWQiLCJ1c" \
                 "2VyLndyaXRlIiwidGFzay5yZWFkIiwid2ViaG9vay5yZWFkIiwidGFzay53cml0ZSIsIndlYmhvb2sud3JpdGUiLCJwcmVzZXQ" \
                 "ucmVhZCIsInByZXNldC53cml0ZSJdfQ.qOuoZmrynlRPhf60cbJbPccDTlOfc2OQMh6FyslSdWfkov9Ppp7HvSX_mTaiB8k9qF" \
                 "0SKsfOxNBQ5_eh4oaLLYlgo71w4nNj_mGv0C3ymIVRMq6oTcoKPYEVYmBk4Pxitpwm7DgPsLRP6hOhtZJlIjb1S12hLE1N8vnn" \
                 "oRkY2WsZE9bd6l2qVjnhHWk2se54SkbD-J7E_3OGx543Tfrgq8UxQerR1BOAkSu9C6zXGxrjv1mCYEy70k9BgSeS-QkEuUvt3I" \
                 "uEGdBYYEdbXf826WQSrKO7T3QK_1YN93Bkqa0nPmug6qdbSBalYhOc5l-HfDdU9M1-kojE6RNy4C5M8Vid6LY9Zf7wImxeCG1P" \
                 "uL-Adtww112uTlvl8Vi7cNMrCZ1sWg-Q0i3iabjJqxvRfhjDhJj2beI3cictvFryLLhWm6VQoVFHDFuLhUHSOppoLOFxMR6Mew" \
                 "9vN3YDjpkCzBBThzHdKTL6qImPozcAgwzxbSvpIIyJKY_p6UPQYPkaVxo5Hcgx805OODv-NiJ2q4ublO-RDcKH1p2Znvil1hbw" \
                 "NOQ15nKH5jFDf2HqT-54psaxaz3oTzHtu8LL79wKc99PAl78Gi-FjQWb5AXrHurhGroJTaZFQygl7Gb7KTnLJ9Wl8NEzo_QyDJ" \
                 "-EsNq_rOZwLrf3Pb6Ffi4BeseKEFM"
    workbook = handle_excel.get_template()
    data_sheet = workbook["Data"]
    data_sheet['I61'] = int(request.session['first']) if request.session['first'].isdigit() else ''
    data_sheet['I62'] = int(request.session['fourth']) if request.session['fourth'].isdigit() else ''
    data_sheet['I64'] = int(request.session['full_extension']) if request.session['full_extension'].isdigit() else ''
    data_sheet['I73'] = int(request.session['first_scout']) if request.session['first_scout'].isdigit() else ''
    data_sheet['I74'] = int(request.session['first_axial']) if request.session['first_axial'].isdigit() else ''
    data_sheet['I76'] = int(request.session['fourth_scout']) if request.session['fourth_scout'].isdigit() else ''
    data_sheet['I77'] = int(request.session['fourth_axial']) if request.session['fourth_axial'].isdigit() else ''
    data_sheet['I83'] = int(request.session['first_laser']) if request.session['first_laser'].isdigit() else ''
    data_sheet['I84'] = int(request.session['first_slice']) if request.session['first_slice'].isdigit() else ''
    data_sheet['I86'] = int(request.session['fourth_laser']) if request.session['fourth_laser'].isdigit() else ''
    data_sheet['I87'] = int(request.session['fourth_slice']) if request.session['fourth_slice'].isdigit() else ''
    data_sheet['D95'] = int(request.session['top_one_mm']) if request.session['top_one_mm'].isdigit() else ''
    data_sheet['F95'] = int(request.session['top_two_mm']) if request.session['top_two_mm'].isdigit() else ''
    data_sheet['H95'] = int(request.session['top_five_mm']) if request.session['top_five_mm'].isdigit() else ''
    data_sheet['J95'] = int(request.session['top_seven_mm']) if request.session['top_seven_mm'].isdigit() else ''
    data_sheet['L95'] = int(request.session['top_ten_mm']) if request.session['top_ten_mm'].isdigit() else ''
    data_sheet['D96'] = int(request.session['bot_one_mm']) if request.session['bot_one_mm'].isdigit() else ''
    data_sheet['F96'] = int(request.session['bot_two_mm']) if request.session['bot_two_mm'].isdigit() else ''
    data_sheet['H96'] = int(request.session['bot_five_mm']) if request.session['bot_five_mm'].isdigit() else ''
    data_sheet['J96'] = int(request.session['bot_seven_mm']) if request.session['bot_seven_mm'].isdigit() else ''
    data_sheet['L96'] = int(request.session['bot_ten_mm']) if request.session['bot_ten_mm'].isdigit() else ''
    data_sheet['C153'] = int(request.session['adult_head_physical']) if request.session['adult_head_physical'].isdigit() else ''
    data_sheet['E153'] = int(request.session['adult_abd_physical']) if request.session['adult_abd_physical'].isdigit() else ''
    data_sheet['G153'] = int(request.session['ped_head_physical']) if request.session['ped_head_physical'].isdigit() else ''
    data_sheet['I153'] = int(request.session['ped_abd_physical']) if request.session['ped_abd_physical'].isdigit() else ''
    data_sheet['C154'] = int(request.session['adult_head_measured']) if request.session['adult_head_measured'].isdigit() else ''
    data_sheet['E154'] = int(request.session['adult_abd_measured']) if request.session['adult_abd_measured'].isdigit() else ''
    data_sheet['G154'] = int(request.session['ped_head_measured']) if request.session['ped_head_measured'].isdigit() else ''
    data_sheet['I154'] = int(request.session['ped_abd_measured']) if request.session['ped_abd_measured'].isdigit() else ''
    data_sheet['C163'] = int(request.session['ah_visible']) if request.session['ah_visible'].isdigit() else ''
    data_sheet['E163'] = int(request.session['aa_visible']) if request.session['aa_visible'].isdigit() else ''
    data_sheet['G163'] = int(request.session['ph_visible']) if request.session['ph_visible'].isdigit() else ''
    data_sheet['I163'] = int(request.session['pa_visible']) if request.session['pa_visible'].isdigit() else ''
    data_sheet['K163'] = int(request.session['hrc_visible']) if request.session['hrc_visible'].isdigit() else ''
    data_sheet['C166'] = int(request.session['ah_50']) if request.session['ah_50'].isdigit() else ''
    data_sheet['E166'] = int(request.session['aa_50']) if request.session['aa_50'].isdigit() else ''
    data_sheet['G166'] = int(request.session['ph_50']) if request.session['ph_50'].isdigit() else ''
    data_sheet['I166'] = int(request.session['pa_50']) if request.session['pa_50'].isdigit() else ''
    data_sheet['K166'] = int(request.session['hrc_50']) if request.session['hrc_50'].isdigit() else ''
    data_sheet['C167'] = int(request.session['ah_10']) if request.session['ah_10'].isdigit() else ''
    data_sheet['E167'] = int(request.session['aa_10']) if request.session['aa_10'].isdigit() else ''
    data_sheet['G167'] = int(request.session['ph_10']) if request.session['ph_10'].isdigit() else ''
    data_sheet['I167'] = int(request.session['pa_10']) if request.session['pa_10'].isdigit() else ''
    data_sheet['K167'] = int(request.session['hrc_10']) if request.session['hrc_10'].isdigit() else ''
    data_sheet['A174'] = int(request.session['n_1']) if request.session['n_1'].isdigit() else ''
    data_sheet['B174'] = int(request.session['t_1']) if request.session['t_1'].isdigit() else ''
    data_sheet['E174'] = int(request.session['measured_1']) if request.session['measured_1'].isdigit() else ''
    data_sheet['G174'] = int(request.session['nom_1']) if request.session['nom_1'].isdigit() else ''
    data_sheet['I174'] = int(request.session['min_1']) if request.session['min_1'].isdigit() else ''
    data_sheet['K174'] = int(request.session['max_1']) if request.session['max_1'].isdigit() else ''
    data_sheet['A175'] = int(request.session['n_2']) if request.session['n_2'].isdigit() else ''
    data_sheet['B175'] = int(request.session['t_2']) if request.session['t_2'].isdigit() else ''
    data_sheet['E175'] = int(request.session['measured_2']) if request.session['measured_2'].isdigit() else ''
    data_sheet['G175'] = int(request.session['nom_2']) if request.session['nom_2'].isdigit() else ''
    data_sheet['I175'] = int(request.session['min_2']) if request.session['min_2'].isdigit() else ''
    data_sheet['K175'] = int(request.session['max_2']) if request.session['max_2'].isdigit() else ''
    data_sheet['A176'] = int(request.session['n_3']) if request.session['n_3'].isdigit() else ''
    data_sheet['B176'] = int(request.session['t_3']) if request.session['t_3'].isdigit() else ''
    data_sheet['E176'] = int(request.session['measured_3']) if request.session['measured_3'].isdigit() else ''
    data_sheet['G176'] = int(request.session['nom_3']) if request.session['nom_3'].isdigit() else ''
    data_sheet['I176'] = int(request.session['min_3']) if request.session['min_3'].isdigit() else ''
    data_sheet['K176'] = int(request.session['max_3']) if request.session['max_3'].isdigit() else ''
    data_sheet['A177'] = int(request.session['n_4']) if request.session['n_4'].isdigit() else ''
    data_sheet['B177'] = int(request.session['t_4']) if request.session['t_4'].isdigit() else ''
    data_sheet['E177'] = int(request.session['measured_4']) if request.session['measured_4'].isdigit() else ''
    data_sheet['G177'] = int(request.session['nom_4']) if request.session['nom_4'].isdigit() else ''
    data_sheet['I177'] = int(request.session['min_4']) if request.session['min_4'].isdigit() else ''
    data_sheet['K177'] = int(request.session['max_4']) if request.session['max_4'].isdigit() else ''
    data_sheet['A178'] = int(request.session['n_5']) if request.session['n_5'].isdigit() else ''
    data_sheet['B178'] = int(request.session['t_5']) if request.session['t_5'].isdigit() else ''
    data_sheet['E178'] = int(request.session['measured_5']) if request.session['measured_5'].isdigit() else ''
    data_sheet['G178'] = int(request.session['nom_5']) if request.session['nom_5'].isdigit() else ''
    data_sheet['I178'] = int(request.session['min_5']) if request.session['min_5'].isdigit() else ''
    data_sheet['K178'] = int(request.session['max_5']) if request.session['max_5'].isdigit() else ''
    data_sheet['C188'] = int(request.session['measured_80']) if request.session['first'].isdigit() else ''
    data_sheet['E188'] = int(request.session['measured_100']) if request.session['first'].isdigit() else ''
    data_sheet['G188'] = int(request.session['measured_100']) if request.session['first'].isdigit() else ''
    data_sheet['I188'] = int(request.session['measured_140']) if request.session['first'].isdigit() else ''
    data_sheet['C190'] = int(request.session['hvl_80']) if request.session['first'].isdigit() else ''
    data_sheet['E190'] = int(request.session['hvl_100']) if request.session['first'].isdigit() else ''
    data_sheet['G190'] = int(request.session['hvl_120']) if request.session['first'].isdigit() else ''
    data_sheet['I190'] = int(request.session['hvl_140']) if request.session['first'].isdigit() else ''
    data_sheet['C212'] = int(request.session['ah_center_1']) if request.session['first'].isdigit() else ''
    data_sheet['E212'] = int(request.session['aa_center_1']) if request.session['first'].isdigit() else ''
    data_sheet['G212'] = int(request.session['ph_center_1']) if request.session['first'].isdigit() else ''
    data_sheet['I212'] = int(request.session['pa_center_1']) if request.session['first'].isdigit() else ''
    data_sheet['C213'] = int(request.session['ah_center_2']) if request.session['first'].isdigit() else ''
    data_sheet['E213'] = int(request.session['aa_center_2']) if request.session['first'].isdigit() else ''
    data_sheet['G213'] = int(request.session['ph_center_2']) if request.session['first'].isdigit() else ''
    data_sheet['I213'] = int(request.session['pa_center_2']) if request.session['first'].isdigit() else ''
    data_sheet['C214'] = int(request.session['ah_center_3']) if request.session['first'].isdigit() else ''
    data_sheet['E214'] = int(request.session['aa_center_3']) if request.session['first'].isdigit() else ''
    data_sheet['G214'] = int(request.session['ph_center_3']) if request.session['first'].isdigit() else ''
    data_sheet['I214'] = int(request.session['pa_center_3']) if request.session['first'].isdigit() else ''
    data_sheet['C215'] = int(request.session['ah_12_1']) if request.session['first'].isdigit() else ''
    data_sheet['E215'] = int(request.session['aa_12_1']) if request.session['first'].isdigit() else ''
    data_sheet['G215'] = int(request.session['ph_12_1']) if request.session['first'].isdigit() else ''
    data_sheet['I215'] = int(request.session['pa_12_1']) if request.session['first'].isdigit() else ''
    data_sheet['C216'] = int(request.session['ah_12_2']) if request.session['first'].isdigit() else ''
    data_sheet['E216'] = int(request.session['aa_12_2']) if request.session['first'].isdigit() else ''
    data_sheet['G216'] = int(request.session['ph_12_2']) if request.session['first'].isdigit() else ''
    data_sheet['I216'] = int(request.session['pa_12_2']) if request.session['first'].isdigit() else ''
    data_sheet['C217'] = int(request.session['ah_12_3']) if request.session['first'].isdigit() else ''
    data_sheet['E217'] = int(request.session['aa_12_3']) if request.session['first'].isdigit() else ''
    data_sheet['G217'] = int(request.session['ph_12_3']) if request.session['first'].isdigit() else ''
    data_sheet['I217'] = int(request.session['pa_12_3']) if request.session['first'].isdigit() else ''
    data_sheet['K235'] = int(request.session['gray_level']) if request.session['first'].isdigit() else ''
    data_sheet['K236'] = int(request.session['patch']) if request.session['first'].isdigit() else ''
    data_sheet['K237'] = int(request.session['line_pair']) if request.session['first'].isdigit() else ''
    data_sheet['C241'] = int(request.session['cl_0']) if request.session['first'].isdigit() else ''
    data_sheet['C242'] = int(request.session['cl_10']) if request.session['first'].isdigit() else ''
    data_sheet['C243'] = int(request.session['cl_20']) if request.session['first'].isdigit() else ''
    data_sheet['C244'] = int(request.session['cl_30']) if request.session['first'].isdigit() else ''
    data_sheet['C245'] = int(request.session['cl_40']) if request.session['first'].isdigit() else ''
    data_sheet['C246'] = int(request.session['cl_50']) if request.session['first'].isdigit() else ''
    data_sheet['C248'] = int(request.session['cl_60']) if request.session['first'].isdigit() else ''
    data_sheet['C249'] = int(request.session['cl_70']) if request.session['first'].isdigit() else ''
    data_sheet['C250'] = int(request.session['cl_80']) if request.session['first'].isdigit() else ''
    data_sheet['C251'] = int(request.session['cl_90']) if request.session['first'].isdigit() else ''
    data_sheet['C252'] = int(request.session['cl_100']) if request.session['first'].isdigit() else ''
    data_sheet['C257'] = int(request.session['upper_left']) if request.session['first'].isdigit() else ''
    data_sheet['C258'] = int(request.session['upper_right']) if request.session['first'].isdigit() else ''
    data_sheet['C259'] = int(request.session['bottom_right']) if request.session['first'].isdigit() else ''
    data_sheet['C260'] = int(request.session['bottom_left']) if request.session['first'].isdigit() else ''
    data_sheet['J263'] = ''
    data_sheet['J264'] = ''
    data_sheet['J265'] = ''
    data_sheet['J266'] = ''
    wb = workbook.save("CT-Report.xlsx")
    wb.close()
    handle_excel.publish_cc_wb(cc_api_key)
    return workbook


def send_alert(request):
    send_mail(
        'That’s your subject',
        'That’s your message body',
        'from@projectcharon.com',
        ['to@yourbestuser.com'],
        fail_silently=False,
    )
