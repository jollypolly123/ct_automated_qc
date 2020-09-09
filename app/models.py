# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2019 - present AppSeed.us
"""
from django.db import models, connection
from django.http import HttpResponse
from django.views import View
from django.core.files.base import ContentFile
from . import qa_tests_8_3
from io import BytesIO
from pydicom import dcmread
from PIL import Image
from django.template.defaultfilters import slugify
from django import forms
from django.conf import settings

import numpy as np
import random
import os


# -*- coding: utf-8 -*-


class Document(models.Model):
    name = models.CharField(max_length=100, default='')
    slug = models.SlugField()
    docfile = models.FileField(upload_to='documents/')
    image = models.ImageField(upload_to='documents/', default='./default.png')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        doc = dcmread(self.docfile.open(), force=True)
        series_descrp = doc.SeriesDescription
        try:
            slice_location = doc.SliceLocation
        except:
            slice_location = 0.0
        self.name = "{}: {}mm".format(series_descrp, slice_location)
        if not self.id:
            self.slug = slugify(self.name)
        image = qa_tests_8_3.get_pixels_hu([doc])

        image -= np.min(image)
        image = np.divide(image, np.max(image))
        image = np.multiply(image, 255).astype('uint8')

        image = Image.fromarray(image, 'L')
        img_io = BytesIO()
        image.save(img_io, format='PNG')
        self.image.save('img.png', ContentFile(img_io.getvalue()), save=False)
        super(Document, self).save(*args, **kwargs)


class Report(models.Model):
    name = models.CharField(max_length=100, default='report')
    file = models.FileField(upload_to='reports/')
