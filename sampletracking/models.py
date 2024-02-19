from django.db import models
from datetime import datetime
from django.utils import timezone
from django.db.models import Max

class Sample(models.Model):
    barcode = models.CharField(max_length=255, unique=True)
    sample_type = models.CharField(max_length=10, choices=[
        ('CRUDE', 'Crude Sample'),
        ('ALIQUOT', 'Crude Aliquot'),
        ('DNA', 'DNA Extract'),
        ('RNA', 'RNA Extract'),
        ('SEQ', 'Sequence Library'),
    ])
    date_created = models.DateField()
    freezer_ID = models.CharField(max_length=100)
    shelf_ID = models.CharField(max_length=100)
    box_ID = models.CharField(max_length=100)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')

    class Meta:
        abstract = True



class CrudeSample(models.Model):
    SAMPLE_TYPE_CHOICES = [
        ('Stool', 'Stool'),  
        ('Nasal', 'Nasal Swab'),
        ('Skin', 'Skin Swab'),
        ("Oral", "Oral Swab"),
        ('Other', 'Other')
    ]
    
    sample_id = models.CharField(max_length=30, primary_key=True, unique=True)
    mgml_barcode = models.CharField(max_length=30, unique=True) # later we have to use barcode scanner to get this value
    creation_date = models.DateTimeField(default=timezone.now) 
    your_id = models.CharField(max_length=50)
    collection_date = models.DateField() 
    sample_type = models.CharField(max_length=100, choices=SAMPLE_TYPE_CHOICES, default='')
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True)
    # tube_barcode = models.CharField(max_length=50, unique=True, default='') 
    status = models.CharField(max_length=100, default = 'Received')
    notes = models.TextField(max_length=400, blank=True) 

    def save(self, *args, **kwargs):
        if not self.sample_id:  
            self.sample_id = self.generate_sample_id()  
        super(Sample, self).save(*args, **kwargs) 

    @staticmethod
    def generate_sample_id():
        last_sample = Sample.objects.order_by('-sample_id').first()
        if last_sample:
            last_id = last_sample.sample_id
            try:
                prefix, num = last_id.split('_')
                num = int(num) + 1
                new_id = f'{prefix}_{num:05}'
            except (ValueError, IndexError):
                # Handle the case where the ID format is unexpected
                new_id = 'MGML_00001'
        else:
            new_id = 'MGML_00001'
        return new_id
    pass

class CrudeAliquot(Sample):
    # Additional fields specific to CrudeAliquot can be added here
    pass

class DNAExtract(Sample):
    # Additional fields specific to DNAExtract can be added here
    pass

class RNAExtract(Sample):
    # Additional fields specific to RNAExtract can be added here
    pass

class SequenceLibrary(Sample):
    # Additional fields specific to SequenceLibrary can be added here
    pass



