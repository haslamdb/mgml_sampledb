from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator
from django.contrib.auth.models import User
from simple_history.models import HistoricalRecords
from datetime import date

# Dictionary to map the full sample type name to a 2-letter code.
TYPE_CODES = {
    'Stool': 'ST',
    'Oral': 'OR',
    'Nasal': 'NA',
    'Skin': 'SK',
    'Blood': 'BL',
    'Tissue': 'TI',
    'Isolate': 'IS',
    'Other': 'OT',
}

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
    base_id = models.CharField(
        max_length=20,
        blank=True,
        editable=False,
        help_text="Base ID shared among related samples (e.g., ST-241219-001)",
        null=True
    )
    sample_id = models.CharField(
        max_length=30,
        unique=True,
        blank=True,
        editable=False,
        help_text="Full unique sample ID (e.g., ST-241219-001-CS)",
        null=True
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

    # Project and study information
    project_name = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Name of the project or study this sample belongs to"
    )
    investigator = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Principal investigator or responsible party"
    )
    patient_type = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Patient Group",
        help_text="Patient group or classification (e.g., IBD, Control, Cancer)"
    )
    study_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="External study identifier or protocol number"
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
    Represents the initial parent sample before any processing.
    Note: Class name remains CrudeSample for database compatibility.
    """
    SAMPLE_SOURCE_CHOICES = [
        ('Stool', 'Stool'),
        ("Oral", "Oral Swab"),
        ('Nasal', 'Nasal Swab'),
        ('Skin', 'Skin Swab'),
        ('Blood', 'Blood'),
        ('Tissue', 'Tissue'),
        ('Isolate', 'Isolate'),
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

    ISOLATE_SOURCE_CHOICES = [
        ('', '---------'),
        ('Blood', 'Blood'),
        ('Urine', 'Urine'),
        ('Wound', 'Wound'),
        ('Stool', 'Stool'),
        ('Laboratory', 'Laboratory'),
        ('Other', 'Other')
    ]

    isolate_source = models.CharField(
        max_length=50,
        choices=ISOLATE_SOURCE_CHOICES,
        blank=True,
        null=True,
        help_text="Source of the isolate (only applicable when sample source is 'Isolate')"
    )

    source_details = models.TextField(
        blank=True,
        null=True,
        help_text="Additional details about the sample source"
    )

    def save(self, *args, **kwargs):
        if not self.pk and not self.sample_id:  # Only on creation
            # 1. Generate base_id
            type_code = TYPE_CODES.get(self.sample_source, 'XX')
            date_str = self.collection_date.strftime('%y%m%d')
            prefix = f'{type_code}-{date_str}'

            # Find the last sample with this date prefix
            last_sample = CrudeSample.objects.filter(
                base_id__startswith=prefix
            ).order_by('base_id').last()

            if last_sample and last_sample.base_id:
                # Extract sequence number from base_id like 'ST-241219-001'
                parts = last_sample.base_id.split('-')
                if len(parts) >= 3:
                    try:
                        last_seq = int(parts[2])
                        next_seq = last_seq + 1
                    except ValueError:
                        next_seq = 1
                else:
                    next_seq = 1
            else:
                next_seq = 1

            self.base_id = f'{prefix}-{str(next_seq).zfill(3)}'

            # 2. Generate full sample_id
            self.sample_id = f'{self.base_id}-CS'

        super().save(*args, **kwargs)

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Parent Sample"
        verbose_name_plural = "Parent Samples"
        indexes = [
            models.Index(fields=['barcode']),
            models.Index(fields=['subject_id']),
            models.Index(fields=['collection_date']),
        ]


class Aliquot(Sample):
    """
    Represents an aliquot derived from a parent sample.
    """
    parent_barcode = models.ForeignKey(
        CrudeSample,
        on_delete=models.PROTECT,
        to_field='barcode',
        related_name='aliquots',
        help_text="The parent sample this aliquot was derived from"
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

    def save(self, *args, **kwargs):
        if not self.pk and not self.sample_id:  # Only on creation
            if self.parent_barcode:
                self.base_id = self.parent_barcode.base_id
                # Get the count of existing aliquots for the same parent
                sibling_count = Aliquot.objects.filter(parent_barcode=self.parent_barcode).count()
                self.sample_id = f'{self.base_id}-AL-{sibling_count + 1}'
        super().save(*args, **kwargs)

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
    quality_score = models.FloatField(
        null=True, 
        blank=True,
        help_text="Quality score for this extract (e.g., A260/A280)"
    )
    concentration = models.FloatField(
        null=True,
        blank=True,
        help_text="Concentration of the extract in ng/µL"
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
    EXTRACTION_METHOD_CHOICES = [
        ('PowerFecal Pro DNA', 'PowerFecal Pro DNA'),
        ('ZymoBIOMICS DNA', 'ZymoBIOMICS DNA'),
        ('RNeasy PowerMicrobiome', 'RNeasy PowerMicrobiome'),
        ('ZymoBIOMICS RNA', 'ZymoBIOMICS RNA'),
        ('AllPrep PowerFecal DNA/RNA', 'AllPrep PowerFecal DNA/RNA'),
        ('ZymoBIOMICS DNA/RNA', 'ZymoBIOMICS DNA/RNA'),
        ('Other', 'Other'),
    ]
    extraction_method = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        choices=EXTRACTION_METHOD_CHOICES,
        default='PowerFecal Pro DNA',
        help_text="Extraction method used (for DNA/RNA extracts)"
    )

    def save(self, *args, **kwargs):
        if not self.pk and not self.sample_id:  # Only on creation
            if self.parent:
                self.base_id = self.parent.base_id
                # Get the count of existing extracts for the same parent
                sibling_count = Extract.objects.filter(parent=self.parent).count()
                self.sample_id = f'{self.base_id}-EX-{sibling_count + 1}'
        super().save(*args, **kwargs)

    def __str__(self):
        return self.sample_id if self.sample_id else self.barcode
    
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
        # Metagenomics
        ('Nextera_XT', 'Illumina Nextera XT DNA Library Prep'),  # NX - Default
        ('Nextera_Flex', 'Illumina Nextera DNA Flex / DNA Prep'),  # NF
        ('TruSeq_Nano', 'Illumina TruSeq Nano DNA'),  # TN
        ('NEBNext_Ultra_DNA', 'NEBNext Ultra II DNA Library Prep'),  # ND
        ('QIAseq_FX', 'QIAseq FX DNA Library Kit'),  # QF
        ('Swift_Accel', 'Swift Biosciences Accel-NGS 2S DNA Library Kit'),  # SA
        ('PacBio_SMRTbell', 'PacBio SMRTbell Express Template Prep Kit'),  # PB
        ('ONT_Ligation', 'Oxford Nanopore Ligation Sequencing Kit'),  # OL
        ('ONT_Rapid', 'Oxford Nanopore Rapid Sequencing Kit'),  # OR
        ('Twist_Hybrid', 'Twist Target Enrichment (Hybrid Capture)'),  # TH
        ('Agilent_SureSelect', 'Agilent SureSelect Target Enrichment'),  # AS
        ('16S_Metagenomic', '16S Metagenomic Sequencing Library Prep'),  # 16
        ('ITS_Amplicon', 'ITS Amplicon Library Prep (fungal)'),  # IT

        # Metatranscriptomics
        ('TruSeq_Total_RNA', 'Illumina TruSeq Stranded Total RNA (Ribo-Zero)'),  # TR
        ('NEBNext_RNA_Ribo', 'NEBNext rRNA Depletion + Ultra II RNA Prep'),  # NR
        ('RiboZero_Plus', 'Ribo-Zero Plus rRNA Depletion Kit'),  # RZ
        ('SMARTer_Total_Microbes', 'SMARTer Stranded Total RNA-Seq (microbes)'),  # SM
        ('SMARTer_Pico', 'SMARTer Stranded Total RNA-Seq v2 - Pico Input'),  # SP
        ('QIAseq_FastSelect', 'QIAseq FastSelect rRNA Removal + RNA Library'),  # QR
        ('Lexogen_RiboCop', 'Lexogen RiboCop rRNA Depletion + CORALL RNA-Seq'),  # LR
        ('ONT_Direct_RNA', 'Oxford Nanopore Direct RNA Sequencing Kit'),  # OD
        ('PacBio_IsoSeq', 'PacBio Iso-Seq Express Template Prep'),  # PI

        # Bulk RNA-seq
        ('TruSeq_mRNA', 'Illumina TruSeq Stranded mRNA Library Prep'),  # TM
        ('TruSeq_SmallRNA', 'Illumina TruSeq Small RNA Library Prep'),  # TS
        ('NEBNext_Ultra_RNA', 'NEBNext Ultra II Directional RNA Library Prep'),  # NU
        ('SMART_Seq_v4', 'SMART-Seq v4 Ultra Low Input RNA Kit'),  # S4
        ('QuantSeq_3prime', 'QuantSeq 3′ mRNA-Seq Library Prep (Lexogen)'),  # Q3

        # Single-cell RNA-seq
        ('10x_3prime', '10x Genomics Chromium Single Cell 3′ Gene Expression'),  # X3
        ('10x_5prime', '10x Genomics Chromium Single Cell 5′ Gene Expression'),  # X5
        ('10x_Multiome', '10x Genomics Multiome (ATAC + RNA)'),  # XM
        ('SMART_Seq2', 'SMART-Seq2'),  # S2
        ('SMART_Seq3', 'SMART-Seq3'),  # S3
        ('CEL_Seq2', 'CEL-Seq2'),  # C2
        ('Drop_seq', 'Drop-seq (academic protocol)'),  # DS
        ('inDrops', 'inDrops (academic protocol)'),  # ID
        ('Seq_Well', 'Seq-Well (academic protocol)'),  # SW

        # Specialized RNA-seq
        ('10x_Visium', '10x Genomics Visium Spatial Gene Expression'),  # XV
        ('NanoString_GeoMx', 'NanoString GeoMx DSP RNA Library Prep'),  # NG
        ('Slide_seq', 'Slide-seq / Slide-seqV2'),  # SS
        ('SMART_Seq_HT', 'SMART-Seq HT Kit (high-throughput)'),  # SH
        ('SMART_Seq_Nucleus', 'SMARTer Stranded Total RNA-Seq (Single Nucleus)'),  # SN

        # Legacy/Other
        ('Nextera', 'Nextera (legacy)'),  # NL
        ('SMARTer', 'SMARTer (legacy)'),  # SL
        ('QIA_COVID', 'QIA_COVID'),  # QC
        ('TruSeq', 'TruSeq (legacy)'),  # TL
        ('Other', 'Other/Custom'),  # OT
    ]

    # Dictionary for quick suffix lookup
    LIBRARY_SUFFIX_MAP = {
        'Nextera_XT': 'NX',
        'Nextera_Flex': 'NF',
        'TruSeq_Nano': 'TN',
        'NEBNext_Ultra_DNA': 'ND',
        'QIAseq_FX': 'QF',
        'Swift_Accel': 'SA',
        'PacBio_SMRTbell': 'PB',
        'ONT_Ligation': 'OL',
        'ONT_Rapid': 'OR',
        'Twist_Hybrid': 'TH',
        'Agilent_SureSelect': 'AS',
        '16S_Metagenomic': '16',
        'ITS_Amplicon': 'IT',
        'TruSeq_Total_RNA': 'TR',
        'NEBNext_RNA_Ribo': 'NR',
        'RiboZero_Plus': 'RZ',
        'SMARTer_Total_Microbes': 'SM',
        'SMARTer_Pico': 'SP',
        'QIAseq_FastSelect': 'QR',
        'Lexogen_RiboCop': 'LR',
        'ONT_Direct_RNA': 'OD',
        'PacBio_IsoSeq': 'PI',
        'TruSeq_mRNA': 'TM',
        'TruSeq_SmallRNA': 'TS',
        'NEBNext_Ultra_RNA': 'NU',
        'SMART_Seq_v4': 'S4',
        'QuantSeq_3prime': 'Q3',
        '10x_3prime': 'X3',
        '10x_5prime': 'X5',
        '10x_Multiome': 'XM',
        'SMART_Seq2': 'S2',
        'SMART_Seq3': 'S3',
        'CEL_Seq2': 'C2',
        'Drop_seq': 'DS',
        'inDrops': 'ID',
        'Seq_Well': 'SW',
        '10x_Visium': 'XV',
        'NanoString_GeoMx': 'NG',
        'Slide_seq': 'SS',
        'SMART_Seq_HT': 'SH',
        'SMART_Seq_Nucleus': 'SN',
        'Nextera': 'NL',
        'SMARTer': 'SL',
        'QIA_COVID': 'QC',
        'TruSeq': 'TL',
        'Other': 'OT',
    }
    
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
        default='Nextera_XT',
        help_text="Type of sequencing library preparation method"
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

    # Legacy data fields
    legacy_sequence_filename = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Original filename for historical/legacy sequence data (without _R1/_R2 suffix)"
    )
    data_file_location = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Path to the actual sequence data files"
    )
    is_legacy_import = models.BooleanField(
        default=False,
        help_text="Indicates if this record was imported from historical data"
    )

    def get_sequence_filenames(self):
        """
        Returns the sequence filenames (R1 and R2).
        For legacy data, uses legacy_sequence_filename.
        For new data, derives from base_id (without -SL suffix) and adds library type suffix.
        """
        if self.legacy_sequence_filename:
            return {
                'R1': f"{self.legacy_sequence_filename}_R1.fastq.gz",
                'R2': f"{self.legacy_sequence_filename}_R2.fastq.gz"
            }
        elif self.base_id:
            # Use base_id (which doesn't have -SL suffix) and add library type suffix
            suffix = self.LIBRARY_SUFFIX_MAP.get(self.library_type, 'OT')
            base_name = f"{self.base_id}_{suffix}"
            return {
                'R1': f"{base_name}_R1.fastq.gz",
                'R2': f"{base_name}_R2.fastq.gz"
            }
        return {'R1': None, 'R2': None}

    def save(self, *args, **kwargs):
        if not self.pk and not self.sample_id:  # Only on creation
            if self.parent:
                self.base_id = self.parent.base_id
                # Get the count of existing libraries for the same parent
                sibling_count = SequenceLibrary.objects.filter(parent=self.parent).count()
                self.sample_id = f'{self.base_id}-SL-{sibling_count + 1}'
        super(Sample, self).save(*args, **kwargs)

    def __str__(self):
        return self.sample_id if self.sample_id else self.barcode

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