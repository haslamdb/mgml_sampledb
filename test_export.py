#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mgml_sampledb.settings')
django.setup()

from sampletracking.models import Extract

# Test if Extract model has the expected fields
extract = Extract.objects.first()
if extract:
    print("Testing Extract fields:")
    print(f"  sample_id: {getattr(extract, 'sample_id', 'NOT FOUND')}")
    print(f"  barcode: {getattr(extract, 'barcode', 'NOT FOUND')}")
    print(f"  volume: {getattr(extract, 'volume', 'NOT FOUND')}")
    print(f"  concentration: {getattr(extract, 'concentration', 'NOT FOUND')}")
    print(f"  date_created: {getattr(extract, 'date_created', 'NOT FOUND')}")
    print(f"  status: {getattr(extract, 'status', 'NOT FOUND')}")
    print(f"  get_status_display: {getattr(extract, 'get_status_display', 'NOT FOUND')}")
    print(f"  project_name: {getattr(extract, 'project_name', 'NOT FOUND')}")
    print(f"  investigator: {getattr(extract, 'investigator', 'NOT FOUND')}")
    print(f"  patient_type: {getattr(extract, 'patient_type', 'NOT FOUND')}")
    print(f"  study_id: {getattr(extract, 'study_id', 'NOT FOUND')}")
    print(f"  freezer_id: {getattr(extract, 'freezer_id', 'NOT FOUND')}")
    print(f"  rack_id: {getattr(extract, 'rack_id', 'NOT FOUND')}")
    print(f"  box_id: {getattr(extract, 'box_id', 'NOT FOUND')}")
    print(f"  well_position: {getattr(extract, 'well_position', 'NOT FOUND')}")
    print(f"  notes: {getattr(extract, 'notes', 'NOT FOUND')}")
    print(f"  a260_280: {getattr(extract, 'a260_280', 'NOT FOUND')}")
    print(f"  a260_230: {getattr(extract, 'a260_230', 'NOT FOUND')}")
    print(f"  get_extract_type_display: {callable(getattr(extract, 'get_extract_type_display', None))}")
else:
    print("No Extract objects found in database")