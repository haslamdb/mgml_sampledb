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
        fields = ['barcode', 'date_created', 'status', 'freezer_ID', 'container_type', 'box_ID', 'well_ID', 'notes']
        widgets = {
            'date_created': DateInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:  # Only set initial for new records
            self.fields['date_created'].initial = timezone.now().date()
            self.fields['status'].initial = 'AVAILABLE'
    
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
    auto_create_aliquot = forms.BooleanField(
        required=False,
        label="Automatically create an aliquot for this sample",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'auto_create_aliquot_checkbox'})
    )
    aliquot_barcode = forms.CharField(
        max_length=255,
        required=False,
        label="Aliquot Barcode",
        help_text="Scan the barcode for the aliquot tube.",
        widget=forms.TextInput(attrs={'class': 'form-control'})
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
        
        auto_create = cleaned_data.get('auto_create_aliquot')
        aliquot_barcode = cleaned_data.get('aliquot_barcode')

        if auto_create and not aliquot_barcode:
            self.add_error('aliquot_barcode', 'This field is required when automatically creating an aliquot.')

        if aliquot_barcode:
            if barcode and aliquot_barcode == barcode:
                self.add_error('aliquot_barcode', 'Aliquot barcode cannot be the same as the crude sample barcode.')
            if Sample.objects.filter(barcode=aliquot_barcode).exists():
                self.add_error('aliquot_barcode', f'A sample with barcode "{aliquot_barcode}" already exists.')
        
        return cleaned_data


class CrudeSampleForm(SampleForm):
    """
    Form for creating and updating crude samples
    """
    class Meta(SampleForm.Meta):
        model = CrudeSample
        fields = SampleForm.Meta.fields + ['sample_source', 'isolate_source', 'collection_date', 'subject_id', 'source_details', 'project_name', 'investigator', 'patient_type', 'study_id']
        widgets = {
            **SampleForm.Meta.widgets,
            'date_created': DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'collection_date': DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'sample_source': forms.Select(attrs={'class': 'form-control', 'id': 'id_sample_source'}),
            'isolate_source': forms.Select(attrs={'class': 'form-control', 'id': 'id_isolate_source'}),
            'source_details': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'project_name': forms.TextInput(attrs={'class': 'form-control'}),
            'investigator': forms.TextInput(attrs={'class': 'form-control'}),
            'patient_type': forms.TextInput(attrs={'class': 'form-control'}),
            'study_id': forms.TextInput(attrs={'class': 'form-control'}),
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
        Cross field validation and isolate_source handling
        """
        cleaned_data = super().clean()

        # Clear isolate_source if sample_source is not 'Isolate'
        sample_source = cleaned_data.get('sample_source')
        isolate_source = cleaned_data.get('isolate_source')
        if sample_source != 'Isolate' and isolate_source:
            cleaned_data['isolate_source'] = ''

        # Validate dates
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
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Parent Barcode",
        help_text="Select the crude sample this aliquot was derived from"
    )
    
    class Meta(SampleForm.Meta):
        model = Aliquot
        fields = SampleForm.Meta.fields + ['parent_barcode', 'volume']
        widgets = {
            **SampleForm.Meta.widgets,
            'date_created': DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'volume': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        super(AliquotForm, self).__init__(*args, **kwargs)
        self.fields['parent_barcode'].empty_label = "Type to search by barcode or subject ID"
        self.fields['parent_barcode'].widget.attrs.update({
            'class': 'form-select selectpicker',
            'data-live-search': 'true',
            'data-size': '10',
            'data-width': '100%'
        })
        # Display format: "BARCODE | Subject: SUBJECT_ID | Source: SOURCE"
        self.fields['parent_barcode'].label_from_instance = lambda obj: (
            f"{obj.barcode} | Subject: {obj.subject_id} | "
            f"Source: {obj.get_sample_source_display() if obj.sample_source else 'Unknown'}"
        )

        # Sort by most recent first
        self.fields['parent_barcode'].queryset = CrudeSample.objects.all().order_by('-date_created')


class ExtractForm(SampleForm):
    """
    Form for creating and updating extracts
    """
    parent = forms.ModelChoiceField(
        queryset=Aliquot.objects.all(),
        to_field_name="barcode",
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Parent Barcode",
        help_text="Select the aliquot this extract was derived from"
    )

    class Meta(SampleForm.Meta):
        model = Extract
        fields = SampleForm.Meta.fields + [
            'parent', 'extract_type', 'quality_score', 'concentration',
            'extraction_method', 'sample_weight', 'extraction_solvent', 
            'solvent_volume', 'extract_volume'
        ]
        widgets = {
            **SampleForm.Meta.widgets,
            'date_created': DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'extract_type': forms.Select(attrs={'class': 'form-select'}),
            'quality_score': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'concentration': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'extraction_method': forms.Select(attrs={'class': 'form-select'}),
            'sample_weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'extraction_solvent': forms.TextInput(attrs={'class': 'form-control'}),
            'solvent_volume': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'extract_volume': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'freezer_ID': forms.TextInput(attrs={'class': 'form-control'}),
            'container_type': forms.Select(attrs={'class': 'form-select'}),
            'box_ID': forms.TextInput(attrs={'class': 'form-control'}),
            'well_ID': forms.TextInput(attrs={'class': 'form-control'}),
        }
        
    def __init__(self, *args, **kwargs):
        super(ExtractForm, self).__init__(*args, **kwargs)
        self.fields['parent'].empty_label = "Type to search by barcode or parent info"
        self.fields['parent'].widget.attrs.update({
            'class': 'form-select selectpicker',
            'data-live-search': 'true',
            'data-size': '10',
            'data-width': '100%'
        })
        # Display format includes parent's subject ID for better searchability
        self.fields['parent'].label_from_instance = lambda obj: (
            f"{obj.barcode} | Parent: {obj.parent_barcode.barcode if obj.parent_barcode else 'N/A'} | "
            f"Subject: {obj.parent_barcode.subject_id if obj.parent_barcode else 'N/A'}"
        )

        # Sort by most recent first
        self.fields['parent'].queryset = Aliquot.objects.select_related('parent_barcode').order_by('-date_created')


class SequenceLibraryForm(SampleForm):
    """
    Form for creating and updating sequence libraries
    """
    parent = forms.ModelChoiceField(
        queryset=Extract.objects.all(),
        to_field_name="barcode",
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'}),
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
            'library_type': forms.Select(attrs={'class': 'form-select'}),
            'nindex': forms.TextInput(attrs={'class': 'form-control'}),
            'sindex': forms.TextInput(attrs={'class': 'form-control'}),
            'qubit_conc': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'diluted_qubit_conc': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'clean_library_conc': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'sequencing_platform': forms.TextInput(attrs={'class': 'form-control'}),
            'sequencing_run_id': forms.TextInput(attrs={'class': 'form-control'}),
            'freezer_ID': forms.TextInput(attrs={'class': 'form-control'}),
            'container_type': forms.Select(attrs={'class': 'form-select'}),
            'box_ID': forms.TextInput(attrs={'class': 'form-control'}),
            'well_ID': forms.TextInput(attrs={'class': 'form-control'}),
        }
        
    def __init__(self, *args, **kwargs):
        super(SequenceLibraryForm, self).__init__(*args, **kwargs)
        self.fields['parent'].empty_label = "Type to search by barcode or extract info"
        self.fields['parent'].widget.attrs.update({
            'class': 'form-select selectpicker',
            'data-live-search': 'true',
            'data-size': '10',
            'data-width': '100%'
        })
        # Display format includes parent aliquot info and subject ID
        self.fields['parent'].label_from_instance = lambda obj: (
            f"{obj.barcode} | Type: {obj.get_extract_type_display() if obj.extract_type else 'Unknown'} | "
            f"Parent: {obj.parent.barcode if obj.parent else 'N/A'} | "
            f"Subject: {obj.parent.parent_barcode.subject_id if obj.parent and obj.parent.parent_barcode else 'N/A'}"
        )

        # Sort by most recent first with related data pre-fetched
        self.fields['parent'].queryset = Extract.objects.select_related(
            'parent', 'parent__parent_barcode'
        ).order_by('-date_created')

        # Update field labels
        self.fields['nindex'].label = "N-index"
        self.fields['sindex'].label = "S-index"
        self.fields['qubit_conc'].label = "Input DNA conc"
        self.fields['diluted_qubit_conc'].label = "Diluted input conc"
    
    def clean_date_sequenced(self):
        """
        Validate date_sequenced is not in the future
        """
        date_sequenced = self.cleaned_data.get('date_sequenced')
        if date_sequenced and date_sequenced > timezone.now().date():
            raise ValidationError("Sequencing date cannot be in the future.")
        return date_sequenced
    


class ReportForm(forms.Form):
    """
    A simple form to select a date for generating a report.
    """
    report_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        initial=timezone.now().date(),
        label="Select Report Date"
    )


class AdvancedFilterForm(forms.Form):
    """
    Advanced filtering form for comprehensive sample reports
    """
    # Sample type filter
    sample_type = forms.ChoiceField(
        choices=[
            ('', 'All Sample Types'),
            ('crude', 'Parent Samples'),
            ('aliquot', 'Aliquots'),
            ('extract', 'Extracts'),
            ('library', 'Sequence Libraries'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Sample Type"
    )

    # Project and study filters
    project_name = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter project name...'}),
        label="Project Name"
    )

    investigator = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter investigator name...'}),
        label="Investigator"
    )

    patient_type = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., IBD, Control, Cancer...'}),
        label="Patient Group"
    )

    study_id = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter study ID...'}),
        label="Study ID"
    )

    # Subject ID filter
    subject_id = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter subject ID...'}),
        label="Subject ID"
    )

    # Date range filters
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label="Date From"
    )

    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label="Date To"
    )

    # Sample source filter (for crude samples)
    sample_source = forms.ChoiceField(
        choices=[('', 'All Sources')] + CrudeSample.SAMPLE_SOURCE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Sample Source"
    )

    # Isolate source filter (for isolates)
    isolate_source = forms.ChoiceField(
        choices=[('', 'All Isolate Sources')] + [c for c in CrudeSample.ISOLATE_SOURCE_CHOICES if c[0] != ''],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Isolate Source (when Sample Source = Isolate)"
    )

    # Library type filter (for sequence libraries)
    library_type = forms.ChoiceField(
        choices=[('', 'All Library Types')] + SequenceLibrary.LIBRARY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Library Type (Sequence Libraries only)"
    )

    # Status filter
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + Sample.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Sample Status"
    )

    # Legacy data filter
    legacy_only = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="Show only legacy imports"
    )

    # Export format
    export_format = forms.ChoiceField(
        choices=[
            ('view', 'View in Browser'),
            ('csv', 'Export to CSV'),
            ('labels', 'Export for Labels'),
        ],
        initial='view',
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label="Output Format"
    )


class QuickAliquotForm(forms.Form):
    """
    Form for quickly creating both a crude sample and aliquot in one step
    """
    # Parent Sample fields (minimal required)
    crude_barcode = forms.CharField(
        max_length=50,
        label="Parent Sample Barcode",
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text="Barcode for the crude sample"
    )

    subject_id = forms.CharField(
        max_length=50,
        label="Subject ID",
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text="Identifier provided by the submitter"
    )

    collection_date = forms.DateField(
        initial=timezone.now().date(),
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label="Collection Date",
        help_text="Date when the sample was collected"
    )

    sample_source = forms.ChoiceField(
        choices=CrudeSample.SAMPLE_SOURCE_CHOICES,
        initial='Blood',
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Sample Source"
    )

    # Aliquot fields
    aliquot_barcode = forms.CharField(
        max_length=50,
        label="Aliquot Barcode",
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text="Barcode for the aliquot"
    )

    use_same_barcode = forms.BooleanField(
        required=False,
        initial=False,
        label="Use same barcode for both samples",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Check to use the crude sample barcode for the aliquot as well"
    )

    aliquot_volume = forms.FloatField(
        required=False,
        label="Aliquot Volume (µL)",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
        help_text="Volume of the aliquot in microliters"
    )

    aliquot_concentration = forms.FloatField(
        required=False,
        label="Concentration",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        help_text="Concentration of the aliquot"
    )

    store_crude_sample = forms.BooleanField(
        required=False,
        initial=True,
        label="Store crude sample",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Uncheck if crude sample is consumed/processed immediately"
    )

    # Storage fields (optional)
    freezer_ID = forms.CharField(
        max_length=50,
        required=False,
        label="Freezer ID",
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text="Storage freezer ID (optional)"
    )

    box_ID = forms.CharField(
        max_length=50,
        required=False,
        label="Box ID",
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text="Storage box ID (optional)"
    )

    notes = forms.CharField(
        required=False,
        label="Notes",
        widget=forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        help_text="Any additional notes (optional)"
    )

    def clean(self):
        cleaned_data = super().clean()
        use_same_barcode = cleaned_data.get('use_same_barcode')

        if use_same_barcode:
            cleaned_data['aliquot_barcode'] = cleaned_data.get('crude_barcode')

        # Validate collection date is not in the future
        collection_date = cleaned_data.get('collection_date')
        if collection_date and collection_date > timezone.now().date():
            raise ValidationError({'collection_date': 'Collection date cannot be in the future.'})

        return cleaned_data
