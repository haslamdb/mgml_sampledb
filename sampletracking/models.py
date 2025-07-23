from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator
from django.contrib.auth.models import User
from simple_history.models import HistoricalRecords

class TimeStampedModel(models.Model):
    """
    An abstract base class model that provides self-updating
    created and modified fields.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="%(class)s_created")
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="%(class)s_updated")

    class Meta:
        abstract = True


class Sample(TimeStampedModel):
    """
    Abstract base class for all sample types.
    Contains common fields for all sample types.
    """
    # Define status choices
    STATUS_CHOICES = [
        ('AWAITING_RECEIPT', 'Awaiting Receipt'),
        ('AVAILABLE', 'Available'),
        ('IN_PROCESS', 'In Process'),
        ('EXHAUSTED', 'Exhausted'),
        ('CONTAMINATED', 'Contaminated'),
        ('ARCHIVED', 'Archived'),
    ]
    
    # Define a validator for barcodes
    barcode_validator = RegexValidator(
        r'^[A-Za-z0-9_-]+$',
        'Barcode can only contain alphanumeric characters, underscores, and hyphens.'
    )
    
    barcode = models.CharField(
        max_length=255, 
        unique=True, 
        validators=[barcode_validator],
        help_text="Unique identifier for this sample (auto-generated for plate storage)"
    )
    date_created = models.DateField(
        help_text="Date when the sample was created"
    )
    notes = models.TextField(
        blank=True, 
        null=True,
        help_text="Additional notes about this sample"
    )
    
    # Sample status
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='AWAITING_RECEIPT',
        help_text="The current status of the sample"
    )
    
    # Storage information
    freezer_ID = models.CharField(
        max_length=100, blank=True, null=True,  # Allow blank for initial registration
        help_text="Identifier for the freezer where this sample is stored"
    )
    rack_ID = models.CharField(
        max_length=100, blank=True, null=True,  # Allow blank for initial registration
        help_text="Identifier for the rack where this sample is stored"
    )
    container_type = models.CharField(
        max_length=10,
        choices=[('box', 'Box'), ('plate', 'Plate')],
        default='box',
        blank=True,
        null=True,
        help_text="Type of container (box or plate)"
    )
    box_ID = models.CharField(
        max_length=100, blank=True, null=True,  # Allow blank for initial registration
        help_text="Identifier for the container where this sample is stored"
    )
    well_ID = models.CharField(
        max_length=50, blank=True, null=True,  # Allow blank for initial registration
        help_text="Well position in the container (e.g., A1, B2, etc.)"
    )
    
    def save(self, *args, **kwargs):
        # Auto-generate barcode for plate-based storage
        if self.container_type == 'plate' and self.box_ID and self.well_ID:
            if not self.barcode or self.barcode.startswith('PLATE:'):
                self.barcode = f"PLATE:{self.box_ID}:{self.well_ID}"
            
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.__class__.__name__}: {self.barcode}"

    class Meta:
        abstract = True
        ordering = ['-date_created']


class CrudeSample(Sample):
    """
    Represents the initial crude sample before any processing.
    """
    SAMPLE_SOURCE_CHOICES = [
        ('Stool', 'Stool'),  
        ("Oral", "Oral Swab"),
        ('Nasal', 'Nasal Swab'),
        ('Skin', 'Skin Swab'),
        ('Blood', 'Blood'),
        ('Tissue', 'Tissue'),
        ('Other', 'Other')
    ]
    
    subject_id = models.CharField(
        max_length=50,
        verbose_name="Subject ID",
        help_text="Identifier provided by the submitter"
    )
    collection_date = models.DateField(
        help_text="Date when the sample was collected"
    )
    sample_source = models.CharField(
        max_length=100, 
        choices=SAMPLE_SOURCE_CHOICES, 
        default='',
        help_text="Source of the sample"
    )
    source_details = models.TextField(
        blank=True, 
        null=True,
        help_text="Additional details about the sample source"
    )
    barcode_override_used = models.BooleanField(
        default=False,
        help_text="Indicates if barcode validation was overridden during registration"
    )
    
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = "Crude Sample"
        verbose_name_plural = "Crude Samples"
        indexes = [
            models.Index(fields=['barcode']),
            models.Index(fields=['subject_id']),
            models.Index(fields=['collection_date']),
        ]


class Aliquot(Sample):
    """
    Represents an aliquot derived from a crude sample.
    """
    parent_barcode = models.ForeignKey(
        CrudeSample, 
        on_delete=models.PROTECT, 
        to_field='barcode', 
        related_name='aliquots', 
        help_text="The crude sample this aliquot was derived from"
    )
    volume = models.FloatField(
        null=True, 
        blank=True,
        help_text="Volume of the aliquot in microliters"
    )
    concentration = models.FloatField(
        null=True, 
        blank=True,
        help_text="Concentration of the aliquot"
    )
    
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = "Aliquot"
        verbose_name_plural = "Aliquots"
        indexes = [
            models.Index(fields=['barcode']),
        ]


class Extract(Sample):
    """
    Represents an extract derived from an aliquot.
    """
    EXTRACT_CHOICES = [
        ('DNA', 'DNA'),  
        ('RNA', 'RNA'),
        ('cfDNA', 'cfDNA'),
        ('Protein', 'Protein'),
        ('Metabolomics', 'Metabolomics'),
        ('Antimicrobials', 'Antimicrobials'),
        ('Other', 'Other')
    ]
    
    parent = models.ForeignKey(
        Aliquot, 
        on_delete=models.PROTECT, 
        to_field='barcode', 
        related_name='extracts', 
        help_text="The aliquot this extract was derived from"
    )
    extract_type = models.CharField(
        max_length=100, 
        choices=EXTRACT_CHOICES, 
        default='DNA',
        help_text="Type of extract"
    )
    protocol_used = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        help_text="Protocol used for extraction"
    )
    quality_score = models.FloatField(
        null=True, 
        blank=True,
        help_text="Quality score for this extract (e.g., A260/A280)"
    )
    
    # New fields for Metabolomics and Antimicrobials
    sample_weight = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True,
        help_text="Sample weight in grams (for Metabolomics/Antimicrobials)"
    )
    extraction_solvent = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Solvent used for extraction (for Metabolomics/Antimicrobials)"
    )
    solvent_volume = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Volume of solvent used in mL (for Metabolomics/Antimicrobials)"
    )
    extract_volume = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Final extract volume in mL (for Metabolomics/Antimicrobials)"
    )
    
    # New field for DNA/RNA extracts
    extraction_method = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Extraction method used (for DNA/RNA extracts)"
    )
    
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = "Extract"
        verbose_name_plural = "Extracts"
        indexes = [
            models.Index(fields=['barcode']),
            models.Index(fields=['extract_type']),
        ]


class Plate(TimeStampedModel):
    """
    Represents a physical plate (96-well or 384-well) used for sequencing.
    """
    PLATE_TYPE_CHOICES = [
        ('96', '96-Well'),
        ('384', '384-Well')
    ]
    
    # Define a validator for barcodes
    barcode_validator = RegexValidator(
        r'^[A-Za-z0-9_-]+$',
        'Barcode can only contain alphanumeric characters, underscores, and hyphens.'
    )
    
    barcode = models.CharField(
        max_length=255, 
        unique=True,
        validators=[barcode_validator],
        help_text="Unique identifier for this plate"
    )
    plate_type = models.CharField(
        max_length=3, 
        choices=PLATE_TYPE_CHOICES, 
        default='96',
        help_text="Type of plate (96-well or 384-well)"
    )
    
    # Storage information
    freezer_ID = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Identifier for the freezer where this plate is stored"
    )
    rack_ID = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Identifier for the rack where this plate is stored"
    )
    container_type = models.CharField(
        max_length=10,
        choices=[('box', 'Box'), ('plate', 'Plate')],
        default='box',
        blank=True,
        null=True,
        help_text="Type of container (box or plate)"
    )
    box_ID = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Identifier for the container where this plate is stored"
    )
    well_ID = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Well position in the container (e.g., A1, B2, etc.)"
    )
    
    notes = models.TextField(
        blank=True, 
        null=True,
        help_text="Additional notes about this plate"
    )

    def __str__(self):
        return f"{self.barcode} ({self.plate_type})"
    
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = "Plate"
        verbose_name_plural = "Plates"
        ordering = ['-created_at']


class SequenceLibrary(Sample):
    """
    Represents a sequencing library derived from an extract.
    """
    LIBRARY_CHOICES = [
        ('Nextera', 'Nextera'),  
        ('SMARTer', 'SMARTer'),
        ('QIA_COVID', 'QIA_COVID'),
        ('TruSeq', 'TruSeq'),
        ('Other', 'Other')
    ]
    
    NINDEX_CHOICES = [("N701" , "N701"),
        ("N702" , "N702"),
        ("N703" , "N703"),
        ("N704" , "N704"),
        ("N705" , "N705"),
        ("N706" , "N706"),
        ("N707" , "N707"),
        ("N710" , "N710"),
        ("N711" , "N711"),
        ("N712" , "N712"),
        ("N714" , "N714"),
        ("N715" , "N715"),
        ("N716" , "N716"),
        ("N718" , "N718"),
        ("N719" , "N719"),
        ("N720" , "N720"),
        ("N721" , "N721"),
        ("N722" , "N722"),
        ("N723" , "N723"),
        ("N724" , "N724"),
        ("N726" , "N726"),
        ("N727" , "N727"),
        ("N728" , "N728"),
        ("N729" , "N729")
    ]
    
    SINDEX_CHOICES = [("S510", "S510"),
        ("S502", "S502"),
        ("S505", "S505"),
        ("S506", "S506"),
        ("S507", "S507"),
        ("S510", "S510"),  # Note: S510 is duplicated in your original code
        ("S503", "S503"),
        ("S511", "S511"),
        ("S508", "S508"),
        ("S516", "S516"),
        ("S517", "S517"),
        ("S518", "S518"),
        ("S521", "S521"),
        ("S515", "S515"),
        ("S522", "S522"),
        ("S520", "S520"),
        ("S513", "S513")
    ]
    
    parent = models.ForeignKey(
        'Extract', 
        on_delete=models.PROTECT,  # Use PROTECT to prevent deletion of libraries
        related_name='libraries', 
        help_text="The extract this library was derived from"
    )
    library_type = models.CharField(
        max_length=100, 
        choices=LIBRARY_CHOICES, 
        default='DNA',
        help_text="Type of sequencing library"
    )
    nindex = models.CharField(
        max_length=100, 
        choices=NINDEX_CHOICES, 
        default='',
        help_text="N-index used for this library"
    )
    sindex = models.CharField(
        max_length=100, 
        choices=SINDEX_CHOICES, 
        default='',
        help_text="S-index used for this library"
    )
    qubit_conc = models.FloatField(
        null=True, 
        blank=True,
        help_text="Qubit concentration in ng/µL"
    )
    diluted_qubit_conc = models.FloatField(
        null=True, 
        blank=True,
        help_text="Diluted Qubit concentration in ng/µL"
    )
    clean_library_conc = models.FloatField(
        null=True, 
        blank=True,
        help_text="Clean library concentration in ng/µL"
    )
    date_sequenced = models.DateField(
        null=True, 
        blank=True,
        help_text="Date when the library was sequenced"
    )
    sequencing_platform = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        help_text="Platform used for sequencing"
    )
    sequencing_run_id = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        help_text="Identifier for the sequencing run"
    )
    
    # Plate and well information
    plate = models.ForeignKey(
        Plate, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='libraries',
        help_text="The plate this library is in"
    )
    well = models.CharField(
        max_length=4, 
        blank=True, 
        null=True, 
        help_text="Well position, e.g., A1, H12"
    )
    
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = "Sequence Library"
        verbose_name_plural = "Sequence Libraries"
        unique_together = [['plate', 'well']]
        indexes = [
            models.Index(fields=['barcode']),
            models.Index(fields=['library_type']),
            models.Index(fields=['date_sequenced']),
        ]
