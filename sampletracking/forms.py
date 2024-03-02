from django import forms
from .models import Sample, CrudeSample, Aliquot, Extract, SequenceLibrary


class SampleForm(forms.ModelForm):
    class Meta:
        model = Sample
        fields = ['barcode',  'date_created', 'freezer_ID', 'shelf_ID', 'box_ID']

class CrudeSampleForm(forms.ModelForm):
    class Meta:
        model = CrudeSample
        fields = ['barcode',  'sample_source', 'date_created', 'collection_date', 'your_id', 'freezer_ID', 'shelf_ID', 'box_ID']
        widgets = {
            'date_created': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'collection_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

class AliquotForm(forms.ModelForm):
    parent_barcode = forms.ModelChoiceField(
        queryset=CrudeSample.objects.all(),
        to_field_name="barcode",
        required=True,
        widget=forms.Select(attrs={'class': 'selectpicker', 'data-live-search': 'true'}),
        label="Parent Barcode",
        # help_text="Type or select the crude sample barcode"
    )

    class Meta:
        model = Aliquot
        fields = ['barcode', 'parent_barcode', 'date_created', 'freezer_ID', 'shelf_ID', 'box_ID']
        widgets = {
            'date_created': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }


    def __init__(self, *args, **kwargs):
        super(AliquotForm, self).__init__(*args, **kwargs)
        self.fields['parent_barcode'].empty_label = "Select a crude sample (MGML lab) barcode"
        self.fields['parent_barcode'].widget.attrs.update({'class': 'form-control'})
        self.fields['parent_barcode'].label_from_instance = lambda obj: f"{obj.barcode}"



class ExtractForm(forms.ModelForm):

    parent_barcode = forms.ModelChoiceField(
        queryset=Aliquot.objects.all(),
        to_field_name="barcode",
        required=True,
        widget=forms.Select(attrs={'class': 'selectpicker', 'data-live-search': 'true'}),
        label="Parent Barcode",
        # help_text="Type or select the parent barcode"
    )

    class Meta:
        model = Extract
        fields = ['barcode', 'parent_barcode', 'extract_type', 'date_created', 'freezer_ID', 'shelf_ID', 'box_ID']
        widgets = {
            'date_created': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }
    def __init__(self, *args, **kwargs):
        super(ExtractForm, self).__init__(*args, **kwargs)
        # This is an optional customization to add a class or any attribute to your form fields
        # for styling or to incorporate JavaScript functionalities
        self.fields['parent_barcode'].empty_label = "Select an aliquot barcode"
        self.fields['parent_barcode'].widget.attrs.update({'class': 'form-control'})
        self.fields['parent_barcode'].label_from_instance = lambda obj: f"{obj.barcode}"
    

class SequenceLibraryForm(forms.ModelForm):

    parent_barcode = forms.ModelChoiceField(
    queryset=Extract.objects.all(),
    to_field_name="barcode",
    required=True,
    widget=forms.Select(attrs={'class': 'selectpicker', 'data-live-search': 'true'}),
    label="Parent Barcode",
    # help_text="Type or select the extract barcode"
    )

    class Meta:
        model = SequenceLibrary
        fields = ['barcode', 'parent_barcode', 'date_created', 'library_type','nindex', 'sindex', 'qubit_conc', 'diluted_qubit_conc', 'clean_library_conc', 'date_sequenced', 'freezer_ID', 'shelf_ID', 'box_ID']
        widgets = {
            'date_created': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'date_sequenced': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }
        
    def __init__(self, *args, **kwargs):
        super(SequenceLibraryForm, self).__init__(*args, **kwargs)
        # This is an optional customization to add a class or any attribute to your form fields
        # for styling or to incorporate JavaScript functionalities
        self.fields['parent_barcode'].empty_label = "Select an extract barcode"
        self.fields['parent_barcode'].widget.attrs.update({'class': 'form-control'})
        self.fields['parent_barcode'].label_from_instance = lambda obj: f"{obj.barcode}"