from django.contrib import admin
from .models import Sample, CrudeSample, Aliquot, SequenceLibrary

# admin.site.register(Sample)
admin.site.register(CrudeSample)
admin.site.register(Aliquot)
admin.site.register(SequenceLibrary)
