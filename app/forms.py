from .models import Document
from django import forms
from django.forms import ClearableFileInput


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ('docfile',)
        widgets = {
            'docfile': ClearableFileInput(attrs={'multiple': True}),
        }


class dicom_image_form(forms.Form):
    docfile = forms.FileField(
        label='Select a file',
        help_text='Single DICOM Image'
    )

