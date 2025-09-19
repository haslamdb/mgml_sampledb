#!/usr/bin/env python
"""
Script to update existing samples to 'Isolate' type and populate sample_ids
"""
import os
import sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mgml_sampledb.settings')

import django
django.setup()

from sampletracking.models import CrudeSample, Aliquot, Extract, SequenceLibrary
from django.db import transaction

def update_sample_ids():
    """Update all existing samples with proper sample_ids"""

    print("Starting sample_id population process...")

    with transaction.atomic():
        # Step 1: Update all CrudeSamples from 'Other' to 'Isolate'
        print("\n1. Updating CrudeSamples from 'Other' to 'Isolate'...")
        updated = CrudeSample.objects.filter(sample_source='Other').update(sample_source='Isolate')
        print(f"   Updated {updated} CrudeSamples to 'Isolate'")

        # Step 2: Generate base_id and sample_id for all CrudeSamples
        print("\n2. Generating base_id and sample_id for CrudeSamples...")
        crude_samples = CrudeSample.objects.filter(sample_id__isnull=True).order_by('collection_date', 'id')

        # Group by collection date to ensure proper sequencing
        date_counters = {}

        for cs in crude_samples:
            # Generate base_id
            type_code = 'IS'  # All are Isolates now
            date_str = cs.collection_date.strftime('%y%m%d')
            prefix = f'{type_code}-{date_str}'

            # Get the next sequence number for this date
            if prefix not in date_counters:
                # Check if there are already samples with this prefix
                existing = CrudeSample.objects.filter(
                    base_id__startswith=prefix
                ).order_by('base_id').last()

                if existing and existing.base_id:
                    parts = existing.base_id.split('-')
                    if len(parts) >= 3:
                        try:
                            date_counters[prefix] = int(parts[2])
                        except ValueError:
                            date_counters[prefix] = 0
                    else:
                        date_counters[prefix] = 0
                else:
                    date_counters[prefix] = 0

            date_counters[prefix] += 1
            seq = date_counters[prefix]

            cs.base_id = f'{prefix}-{str(seq).zfill(3)}'
            cs.sample_id = f'{cs.base_id}-CS'
            cs.save()
            print(f"   {cs.barcode}: {cs.sample_id}")

        # Step 3: Generate sample_ids for Aliquots
        print("\n3. Generating sample_id for Aliquots...")
        aliquots = Aliquot.objects.filter(sample_id__isnull=True).select_related('parent_barcode')

        # Group aliquots by parent
        parent_aliquot_counts = {}

        for aliquot in aliquots.order_by('parent_barcode', 'id'):
            if aliquot.parent_barcode:
                parent = aliquot.parent_barcode
                if parent.base_id:
                    # Count how many aliquots this parent already has with sample_ids
                    if parent.barcode not in parent_aliquot_counts:
                        existing_count = Aliquot.objects.filter(
                            parent_barcode=parent,
                            sample_id__isnull=False
                        ).count()
                        parent_aliquot_counts[parent.barcode] = existing_count

                    parent_aliquot_counts[parent.barcode] += 1
                    seq = parent_aliquot_counts[parent.barcode]

                    aliquot.base_id = parent.base_id
                    aliquot.sample_id = f'{aliquot.base_id}-AL-{seq}'
                    aliquot.save()
                    print(f"   {aliquot.barcode}: {aliquot.sample_id}")

        # Step 4: Generate sample_ids for Extracts
        print("\n4. Generating sample_id for Extracts...")
        extracts = Extract.objects.filter(sample_id__isnull=True).select_related('parent')

        # Group extracts by parent aliquot
        parent_extract_counts = {}

        for extract in extracts.order_by('parent', 'id'):
            if extract.parent:
                parent = extract.parent
                if parent.base_id:
                    # Count how many extracts this parent already has with sample_ids
                    if parent.barcode not in parent_extract_counts:
                        existing_count = Extract.objects.filter(
                            parent=parent,
                            sample_id__isnull=False
                        ).count()
                        parent_extract_counts[parent.barcode] = existing_count

                    parent_extract_counts[parent.barcode] += 1
                    seq = parent_extract_counts[parent.barcode]

                    extract.base_id = parent.base_id
                    extract.sample_id = f'{extract.base_id}-EX-{seq}'
                    extract.save()
                    print(f"   {extract.barcode}: {extract.sample_id}")

        # Step 5: Check for any SequenceLibraries (if they exist)
        print("\n5. Checking for SequenceLibraries...")
        libraries = SequenceLibrary.objects.filter(sample_id__isnull=True)
        if libraries.exists():
            print(f"   Found {libraries.count()} SequenceLibraries without sample_id")
            # Add logic here if needed
        else:
            print("   No SequenceLibraries found")

    # Final verification
    print("\n6. Final verification...")
    print(f"   CrudeSamples with sample_id: {CrudeSample.objects.filter(sample_id__isnull=False).count()}")
    print(f"   CrudeSamples without sample_id: {CrudeSample.objects.filter(sample_id__isnull=True).count()}")
    print(f"   Aliquots with sample_id: {Aliquot.objects.filter(sample_id__isnull=False).count()}")
    print(f"   Aliquots without sample_id: {Aliquot.objects.filter(sample_id__isnull=True).count()}")
    print(f"   Extracts with sample_id: {Extract.objects.filter(sample_id__isnull=False).count()}")
    print(f"   Extracts without sample_id: {Extract.objects.filter(sample_id__isnull=True).count()}")

    print("\n✅ Sample ID population completed successfully!")

if __name__ == '__main__':
    update_sample_ids()