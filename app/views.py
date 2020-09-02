# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2019 - present AppSeed.us
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.template import loader
from django.http import HttpResponse
from django import template
from pydicom import dcmread
from io import BytesIO
import numpy as np
from PIL import Image
from base64 import b64encode


from .models import Document
from .forms import DocumentForm
from . import qa_tests_8_3

import pprint


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
    return redirect('app:dashboard')


def send_alert(request):
    send_mail(
        'That’s your subject',
        'That’s your message body',
        'from@projectcharon.com',
        ['to@yourbestuser.com'],
        fail_silently=False,
    )