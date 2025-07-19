from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Sample, CrudeSample, Aliquot, Extract, SequenceLibrary, Plate


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
        fields = ['barcode', 'date_created', 'status', 'freezer_ID', 'shelf_ID', 'box_ID', 'notes']
        widgets = {
            'date_created': DateInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
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


class AccessioningForm(forms.ModelForm):
    """
    A simplified form for nurses or collection staff to register a new sample.
    """
    override_barcode_check = forms.BooleanField(
        required=False,
        label="Override barcode validation",
        help_text="Check this if using generic pre-printed barcodes not specific to this subject",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = CrudeSample
        fields = ['subject_id', 'barcode', 'collection_date', 'sample_source', 'source_details']
        widgets = {
            'subject_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Subject ID'}),
            'barcode': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Scan Sample Barcode'}),
            'collection_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'sample_source': forms.Select(attrs={'class': 'form-select'}),
            'source_details': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['collection_date'].initial = timezone.now().date()
        
        # Explicitly mark required fields
        self.fields['subject_id'].required = True
        self.fields['barcode'].required = True
        self.fields['collection_date'].required = True
        self.fields['sample_source'].required = True
        
        # Update labels to show they are required
        self.fields['subject_id'].label = "Subject ID *"
        self.fields['barcode'].label = "Barcode *"
        self.fields['collection_date'].label = "Collection Date *"
        self.fields['sample_source'].label = "Sample Source *"

    def clean_collection_date(self):
        collection_date = self.cleaned_data.get('collection_date')
        if collection_date and collection_date > timezone.now().date():
            raise forms.ValidationError("Collection date cannot be in the future.")
        return collection_date
    
    def clean(self):
        """
        Cross-field validation to check if barcode contains subject ID
        """
        cleaned_data = super().clean()
        barcode = cleaned_data.get('barcode', '')
        subject_id = cleaned_data.get('subject_id', '')
        override = cleaned_data.get('override_barcode_check', False)
        
        # Only validate if override is not checked
        if barcode and subject_id and not override:
            # Check if the barcode starts with the subject ID
            if not barcode.upper().startswith(subject_id.upper()):
                error_msg = "Entered Subject ID does not match the barcode Subject ID. Please check that the sample collection barcode is for the correct Subject"
                self.add_error('barcode', error_msg)
                self.add_error('subject_id', error_msg)
        
        return cleaned_data


class CrudeSampleForm(SampleForm):
    """
    Form for creating and updating crude samples
    """
    class Meta(SampleForm.Meta):
        model = CrudeSample
        fields = SampleForm.Meta.fields + ['sample_source', 'collection_date', 'subject_id', 'source_details']
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
        self.fields['parent_barcode'].label_from_instance = lambda obj: f"{obj.barcode} ({obj.subject_id})"


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
        fields = SampleForm.Meta.fields + [
            'parent', 'extract_type', 'protocol_used', 'quality_score',
            'extraction_method', 'sample_weight', 'extraction_solvent', 
            'solvent_volume', 'extract_volume'
        ]
        widgets = {
            **SampleForm.Meta.widgets,
            'date_created': DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'protocol_used': forms.TextInput(attrs={'class': 'form-control'}),
            'quality_score': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'extraction_method': forms.TextInput(attrs={'class': 'form-control'}),
            'sample_weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'extraction_solvent': forms.TextInput(attrs={'class': 'form-control'}),
            'solvent_volume': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'extract_volume': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
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
            'date_sequenced', 'sequencing_platform', 'sequencing_run_id',
            'plate', 'well'
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
            'well': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., A1, H12'}),
        }
        
    def __init__(self, *args, **kwargs):
        super(SequenceLibraryForm, self).__init__(*args, **kwargs)
        self.fields['parent'].empty_label = "Select an extract barcode"
        self.fields['parent'].widget.attrs.update({'class': 'form-select'})
        self.fields['parent'].label_from_instance = lambda obj: f"{obj.barcode} ({obj.extract_type})"
        
        # Configure plate field
        self.fields['plate'] = forms.ModelChoiceField(
            queryset=Plate.objects.all(),
            required=False,
            widget=forms.Select(attrs={'class': 'form-select'}),
            empty_label="Select a plate (optional)",
            label="Plate",
            help_text="Select the plate this library is in"
        )
        self.fields['plate'].label_from_instance = lambda obj: f"{obj.barcode} ({obj.plate_type})"
    
    def clean_date_sequenced(self):
        """
        Validate date_sequenced is not in the future
        """
        date_sequenced = self.cleaned_data.get('date_sequenced')
        if date_sequenced and date_sequenced > timezone.now().date():
            raise ValidationError("Sequencing date cannot be in the future.")
        return date_sequenced
    
    def clean_well(self):
        """
        Validate well format (e.g., A1, H12)
        """
        well = self.cleaned_data.get('well')
        if well:
            well = well.upper().strip()
            # Validate well format: letter(s) followed by number(s)
            import re
            if not re.match(r'^[A-Z]{1,2}[0-9]{1,3}$', well):
                raise ValidationError("Well must be in format like A1, H12, AA1, etc.")
        return well
    
    def clean(self):
        """
        Cross field validation for plate and well
        """
        cleaned_data = super().clean()
        plate = cleaned_data.get('plate')
        well = cleaned_data.get('well')
        
        # If one is specified, both should be specified
        if (plate and not well) or (well and not plate):
            raise ValidationError("Both plate and well must be specified together.")
        
        return cleaned_data


class ReportForm(forms.Form):
    """
    A simple form to select a date for generating a report.
    """
    report_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        initial=timezone.now().date(),
        label="Select Report Date"
    )
