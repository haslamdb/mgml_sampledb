from django import forms
from .models import Sample, CrudeSample, Aliquot, Extract, SequenceLibrary


class SampleForm(forms.ModelForm):
    class Meta:
        model = Sample
        fields = ['barcode',  'sample_type', 'date_created', 'freezer_ID', 'shelf_ID', 'box_ID']

class CrudeSampleForm(forms.ModelForm):
    class Meta:
        model = CrudeSample
        fields = ['barcode',  'sample_source', 'date_created', 'your_id', 'freezer_ID', 'shelf_ID', 'box_ID']

class AliquotForm(forms.ModelForm):
    class Meta:
        model = Aliquot
        fields = ['barcode', 'parent', 'date_created', 'freezer_ID', 'shelf_ID', 'box_ID']

class ExtractForm(forms.ModelForm):
    class Meta:
        model = Extract
        fields = ['barcode', 'parent', 'extract_type', 'date_created', 'freezer_ID', 'shelf_ID', 'box_ID']

class SequenceLibraryForm(forms.ModelForm):
    class Meta:
        model = SequenceLibrary
        fields = ['barcode', 'parent', 'date_created', 'library_type','nindex', 'sindex', 'qubit_conc', 'diluted_qubit_conc', 'clean_library_conc', 'date_sequenced', 'freezer_ID', 'shelf_ID', 'box_ID']
    