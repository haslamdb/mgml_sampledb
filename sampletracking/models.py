from django.db import models
from datetime import datetime
from django.utils import timezone
from django.db.models import Max

class Sample(models.Model):
    barcode = models.CharField(max_length=255, unique=True)
    date_created = models.DateField()
    freezer_ID = models.CharField(max_length=100)
    shelf_ID = models.CharField(max_length=100)
    box_ID = models.CharField(max_length=100)
        
    class Meta:
        abstract = True



class CrudeSample(Sample):
    SAMPLE_SOURCE_CHOICES = [
        ('Stool', 'Stool'),  
        ('Nasal', 'Nasal Swab'),
        ('Skin', 'Skin Swab'),
        ("Oral", "Oral Swab"),
        ('Other', 'Other')
    ]
    your_id = models.CharField(max_length=50)
    collection_date = models.DateField() 
    sample_source = models.CharField(max_length=100, choices=SAMPLE_SOURCE_CHOICES, default='')

    pass



class Aliquot(Sample):
    parent_barcode = models.ForeignKey(CrudeSample, on_delete=models.CASCADE, to_field='barcode', related_name='aliquots', null=True, blank=True)  
    pass


class Extract(Sample):
    parent = models.ForeignKey(Aliquot, on_delete=models.CASCADE, to_field='barcode', related_name='extracts', null=True, blank=True)
    
    EXTRACT_CHOICES = [
        ('DNA', 'DNA'),  
        ('RNA', 'RNA'),
        ('cfDNA', 'cfDNA')
    ]
    extract_type = models.CharField(max_length=100, choices=EXTRACT_CHOICES, default='DNA')
        
    pass


class SequenceLibrary(Sample):
    parent = models.ForeignKey('Extract', on_delete=models.PROTECT, related_name='children', null=True, blank=True)
    LIBRARY_CHOICES = [
        ('Nextera', 'Nextera'),  
        ('SMARTer', 'SMARTer'),
        ('QIA_COVID', 'QIA_COVID')
    ]
    library_type = models.CharField(max_length=100, choices=LIBRARY_CHOICES, default='DNA')

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
    nindex = models.CharField(max_length=100, choices=NINDEX_CHOICES, default='')

    SINDEX_CHOICES = [("S510", "S510"),
        ("S502", "S502"),
        ("S505", "S505"),
        ("S506", "S506"),
        ("S507", "S507"),
        ("S510", "S510"),
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
    sindex = models.CharField(max_length=100, choices=SINDEX_CHOICES, default='')
    qubit_conc = models.FloatField(null=True, blank=True)
    diluted_qubit_conc = models.FloatField(null=True, blank=True)
    clean_library_conc = models.FloatField(null=True, blank=True)
    date_sequenced = models.DateField(null=True, blank=True)

    pass



