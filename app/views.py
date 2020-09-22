# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2019 - present AppSeed.us
"""

from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.urls import reverse
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



def administrator(user):
    return user.groups.filter(name='administrator').exists()


def medical_physicist(user):
    return user.groups.filter(name='medical_physicist').exists()


def radiology_technician(user):
    return user.groups.filter(name='medical_physicist').exists()


@login_required(login_url="/login/")
@user_passes_test(administrator)
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


@login_required(login_url="/login/")
def dashboard_page(request):
    return render(request, 'dashboard_page.html')


@login_required(login_url="/login/")
@user_passes_test(medical_physicist, login_url='permission_not_granted')
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


@login_required(login_url="/login/")
@user_passes_test(medical_physicist, login_url='permission_not_granted')
def display_image(request):
    if request.method == 'GET':
        for row in Document.objects.all().reverse():
            if Document.objects.filter(name=row.name).count() > 1:
                row.delete()
        all_doc = Document.objects.all()
        return render(request, 'index.html',
                      {'images': all_doc})


@login_required(login_url="/login/")
@user_passes_test(medical_physicist, login_url='permission_not_granted')
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


@login_required(login_url="/login/")
@user_passes_test(medical_physicist, login_url='permission_not_granted')
def test(request, slug, test_name):
    test_types = {'ct1': ['CT Number Accuracy', qa_tests_8_3.hu_reproducibility],
                  'ct2': ['Low Contrast Resolution', qa_tests_8_3.low_contrast_resolution],
                  'ct3': ['CT Number Uniformity Assessment', qa_tests_8_3.uniformity_assessment],
                  'ct4': ['High Contrast Spatial Resolution', qa_tests_8_3.get_study_information],}
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


@login_required(login_url="/login/")
@user_passes_test(medical_physicist, login_url='permission_not_granted')
def ct_number_accuracy(request):
    if request.POST.get('action', 'None') == 'upload_images':
        form = DocumentForm(request.POST, request.FILES)
        files = request.FILES.getlist('docfile')
        if form.is_valid():
            for f in files:
                file_instance = Document(docfile=f)
                file_instance.save()
        for row in Document.objects.all().reverse():
            if Document.objects.filter(name=row.name).count() > 1:
                row.delete()
        images = Document.objects.all()
        return render(request, 'ct_number_accuracy.html', {
            'images': images
        })
    elif request.POST.get('action', 'None')[:7] == 'analyze':
        item = Document.objects.get(slug=request.POST.get('action', False)[7:]).docfile
        doc = dcmread(item.open(), force=True)

        try:
            res, image = qa_tests_8_3.hu_reproducibility(doc)
        except:
            return render(request, 'error.html')

        image -= np.min(image)
        image = np.divide(image, np.max(image))
        image = np.multiply(image, 255).astype('uint8')

        image = Image.fromarray(image, 'L')

        byte_io = BytesIO()
        image.save(byte_io, 'PNG')

        encoded = b64encode(byte_io.getvalue()).decode('ascii')
        request.session['ct1_results'] = res
        return render(request, 'ct_number_accuracy.html',
                      {'results': request.session['ct1_results'],
                       'image': encoded})
    elif request.POST.get('action', 'None') == 'submit':
        request.session['aa_poly'] = request.session['ct1_results']['Polyethylene']['Mean']
        request.session['aa_water'] = request.session['ct1_results']['Water']['Mean']
        request.session['aa_acrylic'] = request.session['ct1_results']['Acrylic']['Mean']
        request.session['aa_bone'] = request.session['ct1_results']['Bone']['Mean']
        request.session['aa_air'] = request.session['ct1_results']['Air']['Mean']
        return redirect('app:low_contrast')
    else:
        images = Document.objects.all()
        if images:
            return render(request, 'ct_number_accuracy.html', {
                'images': images
            })
        form = DocumentForm()
        return render(request, 'ct_number_accuracy.html', {
            'form': form
        })


@login_required(login_url="/login/")
@user_passes_test(medical_physicist, login_url='permission_not_granted')
def display_mod_one_header(request, slug):
    item = Document.objects.get(slug=slug).docfile
    doc = dcmread(item.open(), force=True)
    doc_keys = doc.dir()
    elements = {key: getattr(doc, key) for key in doc_keys}
    elements = {key: val for key, val in elements.items() if type(val) is not bytes and type(val) is not dict}

    images = Document.objects.all()

    return render(request, 'ct_number_accuracy.html',
                  {'images': images,
                   'slug': slug,
                   'header': elements})


@login_required(login_url="/login/")
@user_passes_test(medical_physicist, login_url='permission_not_granted')
def low_contrast(request):
    if request.POST.get('action', 'None') == 'upload_images':
        form = DocumentForm(request.POST, request.FILES)
        files = request.FILES.getlist('docfile')
        if form.is_valid():
            for f in files:
                file_instance = Document(docfile=f)
                file_instance.save()
        for row in Document.objects.all().reverse():
            if Document.objects.filter(name=row.name).count() > 1:
                row.delete()
        images = Document.objects.all()
        return render(request, 'low_contrast_performance.html', {
            'images': images
        })
    elif request.POST.get('action', 'None')[:7] == 'analyze':
        item = Document.objects.get(slug=request.POST.get('action', False)[7:]).docfile
        doc = dcmread(item.open(), force=True)

        try:
            res, image = qa_tests_8_3.low_contrast_resolution(doc)
        except:
            return render(request, 'error.html')

        image -= np.min(image)
        image = np.divide(image, np.max(image))
        image = np.multiply(image, 255).astype('uint8')

        image = Image.fromarray(image, 'L')

        byte_io = BytesIO()
        image.save(byte_io, 'PNG')

        encoded = b64encode(byte_io.getvalue()).decode('ascii')
        request.session['ct2_results'] = res
        return render(request, 'low_contrast_performance.html',
                      {'results': request.session['ct2_results'],
                       'image': encoded})
    elif request.POST.get('action', 'None') == 'submit':
        request.session['ah_mean_disk'] = request.session['ct2_results']['Mean Disk (HU)']
        request.session['ah_mean_bkgd'] = request.session['ct2_results']['Mean Background (HU)']
        request.session['ah_std_bkgd'] = request.session['ct2_results']['Standard Deviation Background (HU)']
        return redirect('app:ct_number')
    else:
        images = Document.objects.all()
        if images:
            return render(request, 'low_contrast_performance.html', {
                'images': images
            })
        form = DocumentForm()
        return render(request, 'low_contrast_performance.html', {
            'form': form
        })


@login_required(login_url="/login/")
@user_passes_test(medical_physicist, login_url='permission_not_granted')
def display_mod_two_header(request, slug):
    item = Document.objects.get(slug=slug).docfile
    doc = dcmread(item.open(), force=True)
    doc_keys = doc.dir()
    elements = {key: getattr(doc, key) for key in doc_keys}
    elements = {key: val for key, val in elements.items() if type(val) is not bytes and type(val) is not dict}

    images = Document.objects.all()

    return render(request, 'low_contrast_performance.html',
                  {'images': images,
                   'slug': slug,
                   'header': elements})


@login_required(login_url="/login/")
@user_passes_test(medical_physicist, login_url='permission_not_granted')
def ct_number(request):
    if request.POST.get('action', 'None') == 'upload_images':
        form = DocumentForm(request.POST, request.FILES)
        files = request.FILES.getlist('docfile')
        if form.is_valid():
            for f in files:
                file_instance = Document(docfile=f)
                file_instance.save()
        for row in Document.objects.all().reverse():
            if Document.objects.filter(name=row.name).count() > 1:
                row.delete()
        images = Document.objects.all()
        return render(request, 'ct_number_uniformity_and_artifact_evaluation.html', {
            'images': images
        })
    elif request.POST.get('action', 'None')[:7] == 'analyze':
        item = Document.objects.get(slug=request.POST.get('action', False)[7:]).docfile
        doc = dcmread(item.open(), force=True)

        try:
            res, image = qa_tests_8_3.uniformity_assessment(doc)
        except:
            return render(request, 'error.html')

        image -= np.min(image)
        image = np.divide(image, np.max(image))
        image = np.multiply(image, 255).astype('uint8')

        image = Image.fromarray(image, 'L')

        byte_io = BytesIO()
        image.save(byte_io, 'PNG')

        encoded = b64encode(byte_io.getvalue()).decode('ascii')
        request.session['ct3_results'] = res
        return render(request, 'ct_number_uniformity_and_artifact_evaluation.html',
                      {'results': request.session['ct3_results'],
                       'image': encoded})
    elif request.POST.get('action', 'None') == 'submit':
        request.session['ah_top'] = request.session['ct3_results']["12'"]['Mean']
        request.session['ah_right'] = request.session['ct3_results']["3'"]['Mean']
        request.session['ah_bottom'] = request.session['ct3_results']["6'"]['Mean']
        request.session['ah_left'] = request.session['ct3_results']["9'"]['Mean']
        request.session['ah_center'] = request.session['ct3_results']["Center"]['Mean']
        return redirect('app:high_contrast')
    else:
        images = Document.objects.all()
        if images:
            return render(request, 'ct_number_uniformity_and_artifact_evaluation.html', {
                'images': images
            })
        form = DocumentForm()
        return render(request, 'ct_number_uniformity_and_artifact_evaluation.html', {
            'form': form
        })


@login_required(login_url="/login/")
@user_passes_test(medical_physicist, login_url='permission_not_granted')
def display_mod_three_header(request, slug):
    item = Document.objects.get(slug=slug).docfile
    doc = dcmread(item.open(), force=True)
    doc_keys = doc.dir()
    elements = {key: getattr(doc, key) for key in doc_keys}
    elements = {key: val for key, val in elements.items() if type(val) is not bytes and type(val) is not dict}

    images = Document.objects.all()

    return render(request, 'ct_number_uniformity_and_artifact_evaluation.html',
                  {'images': images,
                   'slug': slug,
                   'header': elements})


@login_required(login_url="/login/")
@user_passes_test(medical_physicist, login_url='permission_not_granted')
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
        input_data(request)
        return redirect('app:dashboard')
    else:
        return redirect('high_contrast_resolution.html')


@login_required(login_url="/login/")
@user_passes_test(medical_physicist, login_url='permission_not_granted')
def activities_page(request):

    all_doc = Document.objects.all()

    return render(request, 'activities_page.html',
                  {'images': all_doc})


@login_required(login_url="/login/")
@user_passes_test(medical_physicist, login_url='permission_not_granted')
def database_page(request):

    all_doc = Document.objects.all()

    return render(request, 'database_page.html',
                  {'images': all_doc})


@login_required(login_url="/login/")
@user_passes_test(medical_physicist, login_url='permission_not_granted')
def delete_files(request):
    Document.objects.all().delete()
    Report.objects.all().delete()
    return redirect('app:dashboard')


@login_required(login_url="/login/")
@user_passes_test(medical_physicist, login_url='permission_not_granted')
def ct_protocol(request):
    if request.method == 'POST':
        request.session['fac-prot-ah'] = request.POST.get('fac-prot-ah', 'No Value')
        request.session['fac-prot-aa'] = request.POST.get('fac-prot-aa', 'No Value')
        request.session['fac-prot-cc'] = request.POST.get('fac-prot-cc', 'No Value')
        request.session['fac-prot-ce'] = request.POST.get('fac-prot-ce', 'No Value')
        request.session['fac-prot-cw'] = request.POST.get('fac-prot-cw', 'No Value')
        request.session['fac-prot-sw'] = request.POST.get('fac-prot-sw', 'No Value')
        request.session['fac-prot-ph'] = request.POST.get('fac-prot-ph', 'No Value')
        request.session['fac-prot-pa'] = request.POST.get('fac-prot-pa', 'No Value')
        return redirect('table_travel_and_return_to_fixed_position_accuracy.html')
    else:
        return redirect('ct_protocol_review.html')


@login_required(login_url="/login/")
@user_passes_test(medical_physicist, login_url='permission_not_granted')
def table_travel(request):
    if request.method == 'POST':
        request.session['first'] = request.POST.get("first", "No Value")
        request.session['fourth'] = request.POST.get("fourth", "No Value")
        request.session['full_extension'] = request.POST.get("full_extension", "No Value")
        return redirect('scout_prescription_and_alignment_light_accuracy.html')
    else:
        return redirect('table_travel_and_return_to_fixed_position_accuracy.html')


@login_required(login_url="/login/")
@user_passes_test(medical_physicist, login_url='permission_not_granted')
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


@login_required(login_url="/login/")
@user_passes_test(medical_physicist, login_url='permission_not_granted')
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
        return redirect('in-plane_distance_accuracy.html')
    else:
        return redirect('slice_thickness_accuracy.html')


@login_required(login_url="/login/")
@user_passes_test(medical_physicist, login_url='permission_not_granted')
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
        return redirect('radiation_beam_width.html')
    else:
        return redirect('plane_distance_accuracy.html')


@login_required(login_url="/login/")
@user_passes_test(medical_physicist, login_url='permission_not_granted')
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


@login_required(login_url="/login/")
@user_passes_test(medical_physicist, login_url='permission_not_granted')
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


@login_required(login_url="/login/")
@user_passes_test(medical_physicist, login_url='permission_not_granted')
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


@login_required(login_url="/login/")
@user_passes_test(medical_physicist, login_url='permission_not_granted')
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
        return redirect('app:ct_number_accuracy')
    else:
        return redirect('soft-copy_quality_control.html')


def try_float(str):
    if str:
        try:
            flt = float(str)
        except ValueError:
            flt = str
    else:
        flt = ''
    return flt


@login_required(login_url="/login/")
@user_passes_test(medical_physicist, login_url='permission_not_granted')
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
    # data_sheet['I61'] = try_float(request.session['first'])
    # data_sheet['I62'] = try_float(request.session['fourth'])
    # data_sheet['I64'] = try_float(request.session['full_extension'])
    # data_sheet['I73'] = try_float(request.session['first_scout'])
    # data_sheet['I74'] = try_float(request.session['first_axial'])
    # data_sheet['I76'] = try_float(request.session['fourth_scout'])
    # data_sheet['I77'] = try_float(request.session['fourth_axial'])
    # data_sheet['I83'] = try_float(request.session['first_laser'])
    # data_sheet['I84'] = try_float(request.session['first_slice'])
    # data_sheet['I86'] = try_float(request.session['fourth_laser'])
    # data_sheet['I87'] = try_float(request.session['fourth_slice'])
    # data_sheet['D95'] = try_float(request.session['top_one_mm'])
    # data_sheet['F95'] = try_float(request.session['top_two_mm'])
    # data_sheet['H95'] = try_float(request.session['top_five_mm'])
    # data_sheet['J95'] = try_float(request.session['top_seven_mm'])
    # data_sheet['L95'] = try_float(request.session['top_ten_mm'])
    # data_sheet['D96'] = try_float(request.session['bot_one_mm'])
    # data_sheet['F96'] = try_float(request.session['bot_two_mm'])
    # data_sheet['H96'] = try_float(request.session['bot_five_mm'])
    # data_sheet['J96'] = try_float(request.session['bot_seven_mm'])
    # data_sheet['L96'] = try_float(request.session['bot_ten_mm'])
    # data_sheet['D105'] = request.session['aa_poly']
    # data_sheet['D106'] = request.session['aa_water']
    # data_sheet['D107'] = request.session['aa_acrylic']
    # data_sheet['D108'] = request.session['aa_bone']
    # data_sheet['D109'] = request.session['aa_air']
    # data_sheet['C118'] = request.session['ah_mean_disk']
    # data_sheet['C119'] = request.session['ah_mean_bkgd']
    # data_sheet['C120'] = request.session['ah_std_bkgd']
    # data_sheet['C130'] = request.session['ah_top']
    # data_sheet['C131'] = request.session['ah_right']
    # data_sheet['C132'] = request.session['ah_bottom']
    # data_sheet['C133'] = request.session['ah_left']
    # data_sheet['C134'] = request.session['ah_center']
    # data_sheet['C153'] = try_float(request.session['adult_head_physical'])
    # data_sheet['E153'] = try_float(request.session['adult_abd_physical'])
    # data_sheet['G153'] = try_float(request.session['ped_head_physical'])
    # data_sheet['I153'] = try_float(request.session['ped_abd_physical'])
    # data_sheet['C154'] = try_float(request.session['adult_head_measured'])
    # data_sheet['E154'] = try_float(request.session['adult_abd_measured'])
    # data_sheet['G154'] = try_float(request.session['ped_head_measured'])
    # data_sheet['I154'] = try_float(request.session['ped_abd_measured'])
    # data_sheet['C163'] = try_float(request.session['ah_visible'])
    # data_sheet['E163'] = try_float(request.session['aa_visible'])
    # data_sheet['G163'] = try_float(request.session['ph_visible'])
    # data_sheet['I163'] = try_float(request.session['pa_visible'])
    # data_sheet['K163'] = try_float(request.session['hrc_visible'])
    # data_sheet['C166'] = try_float(request.session['ah_50'])
    # data_sheet['E166'] = try_float(request.session['aa_50'])
    # data_sheet['G166'] = try_float(request.session['ph_50'])
    # data_sheet['I166'] = try_float(request.session['pa_50'])
    # data_sheet['K166'] = try_float(request.session['hrc_50'])
    # data_sheet['C167'] = try_float(request.session['ah_10'])
    # data_sheet['E167'] = try_float(request.session['aa_10'])
    # data_sheet['G167'] = try_float(request.session['ph_10'])
    # data_sheet['I167'] = try_float(request.session['pa_10'])
    # data_sheet['K167'] = try_float(request.session['hrc_10'])
    # data_sheet['A174'] = try_float(request.session['n_1'])
    # data_sheet['B174'] = try_float(request.session['t_1'])
    # data_sheet['E174'] = try_float(request.session['measured_1'])
    # data_sheet['G174'] = try_float(request.session['nom_1'])
    # data_sheet['I174'] = try_float(request.session['min_1'])
    # data_sheet['K174'] = try_float(request.session['max_1'])
    # data_sheet['A175'] = try_float(request.session['n_2'])
    # data_sheet['B175'] = try_float(request.session['t_2'])
    # data_sheet['E175'] = try_float(request.session['measured_2'])
    # data_sheet['G175'] = try_float(request.session['nom_2'])
    # data_sheet['I175'] = try_float(request.session['min_2'])
    # data_sheet['K175'] = try_float(request.session['max_2'])
    # data_sheet['A176'] = try_float(request.session['n_3'])
    # data_sheet['B176'] = try_float(request.session['t_3'])
    # data_sheet['E176'] = try_float(request.session['measured_3'])
    # data_sheet['G176'] = try_float(request.session['nom_3'])
    # data_sheet['I176'] = try_float(request.session['min_3'])
    # data_sheet['K176'] = try_float(request.session['max_3'])
    # data_sheet['A177'] = try_float(request.session['n_4'])
    # data_sheet['B177'] = try_float(request.session['t_4'])
    # data_sheet['E177'] = try_float(request.session['measured_4'])
    # data_sheet['G177'] = try_float(request.session['nom_4'])
    # data_sheet['I177'] = try_float(request.session['min_4'])
    # data_sheet['K177'] = try_float(request.session['max_4'])
    # data_sheet['A178'] = try_float(request.session['n_5'])
    # data_sheet['B178'] = try_float(request.session['t_5'])
    # data_sheet['E178'] = try_float(request.session['measured_5'])
    # data_sheet['G178'] = try_float(request.session['nom_5'])
    # data_sheet['I178'] = try_float(request.session['min_5'])
    # data_sheet['K178'] = try_float(request.session['max_5'])
    # data_sheet['C188'] = try_float(request.session['measured_80'])
    # data_sheet['E188'] = try_float(request.session['measured_100'])
    # data_sheet['G188'] = try_float(request.session['measured_100'])
    # data_sheet['I188'] = try_float(request.session['measured_140'])
    # data_sheet['C190'] = try_float(request.session['hvl_80'])
    # data_sheet['E190'] = try_float(request.session['hvl_100'])
    # data_sheet['G190'] = try_float(request.session['hvl_120'])
    # data_sheet['I190'] = try_float(request.session['hvl_140'])
    # data_sheet['C212'] = try_float(request.session['ah_center_1'])
    # data_sheet['E212'] = try_float(request.session['aa_center_1'])
    # data_sheet['G212'] = try_float(request.session['ph_center_1'])
    # data_sheet['I212'] = try_float(request.session['pa_center_1'])
    # data_sheet['C213'] = try_float(request.session['ah_center_2'])
    # data_sheet['E213'] = try_float(request.session['aa_center_2'])
    # data_sheet['G213'] = try_float(request.session['ph_center_2'])
    # data_sheet['I213'] = try_float(request.session['pa_center_2'])
    # data_sheet['C214'] = try_float(request.session['ah_center_3'])
    # data_sheet['E214'] = try_float(request.session['aa_center_3'])
    # data_sheet['G214'] = try_float(request.session['ph_center_3'])
    # data_sheet['I214'] = try_float(request.session['pa_center_3'])
    # data_sheet['C215'] = try_float(request.session['ah_12_1'])
    # data_sheet['E215'] = try_float(request.session['aa_12_1'])
    # data_sheet['G215'] = try_float(request.session['ph_12_1'])
    # data_sheet['I215'] = try_float(request.session['pa_12_1'])
    # data_sheet['C216'] = try_float(request.session['ah_12_2'])
    # data_sheet['E216'] = try_float(request.session['aa_12_2'])
    # data_sheet['G216'] = try_float(request.session['ph_12_2'])
    # data_sheet['I216'] = try_float(request.session['pa_12_2'])
    # data_sheet['C217'] = try_float(request.session['ah_12_3'])
    # data_sheet['E217'] = try_float(request.session['aa_12_3'])
    # data_sheet['G217'] = try_float(request.session['ph_12_3'])
    # data_sheet['I217'] = try_float(request.session['pa_12_3'])
    # data_sheet['K235'] = try_float(request.session['gray_level'])
    # data_sheet['K236'] = try_float(request.session['patch'])
    # data_sheet['K237'] = try_float(request.session['line_pair'])
    # data_sheet['C241'] = try_float(request.session['cl_0'])
    # data_sheet['C242'] = try_float(request.session['cl_10'])
    # data_sheet['C243'] = try_float(request.session['cl_20'])
    # data_sheet['C244'] = try_float(request.session['cl_30'])
    # data_sheet['C245'] = try_float(request.session['cl_40'])
    # data_sheet['C246'] = try_float(request.session['cl_50'])
    # data_sheet['C248'] = try_float(request.session['cl_60'])
    # data_sheet['C249'] = try_float(request.session['cl_70'])
    # data_sheet['C250'] = try_float(request.session['cl_80'])
    # data_sheet['C251'] = try_float(request.session['cl_90'])
    # data_sheet['C252'] = try_float(request.session['cl_100'])
    # data_sheet['C257'] = try_float(request.session['upper_left'])
    # data_sheet['C258'] = try_float(request.session['upper_right'])
    # data_sheet['C259'] = try_float(request.session['bottom_right'])
    # data_sheet['C260'] = try_float(request.session['bottom_left'])
    # data_sheet['J263'] = ''
    # data_sheet['J264'] = ''
    # data_sheet['J265'] = ''
    # data_sheet['J266'] = ''
    # workbook.save('New.xlsx')
    print(request.session)
    # handle_excel.upload_to_s3(workbook)
    # handle_excel.publish_cc_wb(cc_api_key)
    return workbook


@login_required(login_url="/login/")
@user_passes_test(medical_physicist, login_url='permission_not_granted')
def final_report(request):
    return render(request, 'report.html')


@login_required(login_url="/login/")
def send_alert(request):
    send_mail(
        'That’s your subject',
        'That’s your message body',
        'from@projectcharon.com',
        ['to@yourbestuser.com'],
        fail_silently=False,
    )
