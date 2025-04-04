from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Sample, CrudeSample, Aliquot, Extract, SequenceLibrary


class DateInput(forms.DateInput):
    """
    Custom DateInput widget with HTML5 date input type
    """
    input_type = 'date'


class SampleForm(forms.ModelForm):
    """
    Base form for all sample types
    """
    class Meta:
        model = Sample
        fields = ['barcode', 'date_created', 'freezer_ID', 'shelf_ID', 'box_ID', 'notes']
        widgets = {
            'date_created': DateInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
    
    def clean_barcode(self):
        """
        Validate barcode format
        """
        barcode = self.cleaned_data.get('barcode')
        if barcode:
            # Check if barcode is proper format - can customize this validation
            if len(barcode) < 3:
                raise ValidationError("Barcode must be at least 3 characters long.")
        return barcode
    
    def clean_date_created(self):
        """
        Validate date_created is not in the future
        """
        date_created = self.cleaned_data.get('date_created')
        if date_created and date_created > timezone.now().date():
            raise ValidationError("Date cannot be in the future.")
        return date_created


class CrudeSampleForm(SampleForm):
    """
    Form for creating and updating crude samples
    """
    class Meta(SampleForm.Meta):
        model = CrudeSample
        fields = SampleForm.Meta.fields + ['sample_source', 'collection_date', 'your_id', 'source_details']
        widgets = {
            **SampleForm.Meta.widgets,
            'date_created': DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'collection_date': DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'source_details': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
    
    def clean_collection_date(self):
        """
        Validate collection_date is not in the future
        """
        collection_date = self.cleaned_data.get('collection_date')
        if collection_date and collection_date > timezone.now().date():
            raise ValidationError("Collection date cannot be in the future.")
        return collection_date
    
    def clean(self):
        """
        Cross field validation
        """
        cleaned_data = super().clean()
        collection_date = cleaned_data.get('collection_date')
        date_created = cleaned_data.get('date_created')
        
        if collection_date and date_created and collection_date > date_created:
            self.add_error('collection_date', "Collection date cannot be after creation date.")
        
        return cleaned_data


class AliquotForm(SampleForm):
    """
    Form for creating and updating aliquots
    """
    parent_barcode = forms.ModelChoiceField(
        queryset=CrudeSample.objects.all(),
        to_field_name="barcode",
        required=True,
        widget=forms.Select(attrs={'class': 'form-select selectpicker', 'data-live-search': 'true'}),
        label="Parent Barcode",
        help_text="Select the crude sample this aliquot was derived from"
    )
    
    class Meta(SampleForm.Meta):
        model = Aliquot
        fields = SampleForm.Meta.fields + ['parent_barcode', 'volume', 'concentration']
        widgets = {
            **SampleForm.Meta.widgets,
            'date_created': DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'volume': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'concentration': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        super(AliquotForm, self).__init__(*args, **kwargs)
        self.fields['parent_barcode'].empty_label = "Select a crude sample barcode"
        self.fields['parent_barcode'].widget.attrs.update({'class': 'form-select'})
        self.fields['parent_barcode'].label_from_instance = lambda obj: f"{obj.barcode} ({obj.your_id})"


class ExtractForm(SampleForm):
    """
    Form for creating and updating extracts
    """
    parent = forms.ModelChoiceField(
        queryset=Aliquot.objects.all(),
        to_field_name="barcode",
        required=True,
        widget=forms.Select(attrs={'class': 'form-select selectpicker', 'data-live-search': 'true'}),
        label="Parent Barcode",
        help_text="Select the aliquot this extract was derived from"
    )

    class Meta(SampleForm.Meta):
        model = Extract
        fields = SampleForm.Meta.fields + ['parent', 'extract_type', 'protocol_used', 'quality_score']
        widgets = {
            **SampleForm.Meta.widgets,
            'date_created': DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'protocol_used': forms.TextInput(attrs={'class': 'form-control'}),
            'quality_score': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
        
    def __init__(self, *args, **kwargs):
        super(ExtractForm, self).__init__(*args, **kwargs)
        self.fields['parent'].empty_label = "Select an aliquot barcode"
        self.fields['parent'].widget.attrs.update({'class': 'form-select'})
        self.fields['parent'].label_from_instance = lambda obj: f"{obj.barcode}"


class SequenceLibraryForm(SampleForm):
    """
    Form for creating and updating sequence libraries
    """
    parent = forms.ModelChoiceField(
        queryset=Extract.objects.all(),
        to_field_name="barcode",
        required=True,
        widget=forms.Select(attrs={'class': 'form-select selectpicker', 'data-live-search': 'true'}),
        label="Parent Barcode",
        help_text="Select the extract this library was derived from"
    )

    class Meta(SampleForm.Meta):
        model = SequenceLibrary
        fields = SampleForm.Meta.fields + [
            'parent', 'library_type', 'nindex', 'sindex', 
            'qubit_conc', 'diluted_qubit_conc', 'clean_library_conc', 
            'date_sequenced', 'sequencing_platform', 'sequencing_run_id'
        ]
        widgets = {
            **SampleForm.Meta.widgets,
            'date_created': DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'date_sequenced': DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'qubit_conc': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'diluted_qubit_conc': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'clean_library_conc': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'sequencing_platform': forms.TextInput(attrs={'class': 'form-control'}),
            'sequencing_run_id': forms.TextInput(attrs={'class': 'form-control'}),
        }
        
    def __init__(self, *args, **kwargs):
        super(SequenceLibraryForm, self).__init__(*args, **kwargs)
        self.fields['parent'].empty_label = "Select an extract barcode"
        self.fields['parent'].widget.attrs.update({'class': 'form-select'})
        self.fields['parent'].label_from_instance = lambda obj: f"{obj.barcode} ({obj.extract_type})"
    
    def clean_date_sequenced(self):
        """
        Validate date_sequenced is not in the future
        """
        date_sequenced = self.cleaned_data.get('date_sequenced')
        if date_sequenced and date_sequenced > timezone.now().date():
            raise ValidationError("Sequencing date cannot be in the future.")
        return date_sequenced
