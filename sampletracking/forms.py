from django import forms
from .models import SampleBase, CrudeSample

class SampleBaseForm(forms.ModelForm):
    class Meta:
        model = SampleBase
        fields = ['sample_type', 'date_collected', 'your_id']

class CrudeSampleForm(forms.ModelForm):
    class Meta:
        model = CrudeSample
        fields = ['barcode', 'location', 'processing_date']
