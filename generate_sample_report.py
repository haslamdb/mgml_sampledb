#!/usr/bin/env python
"""
Generate comprehensive sample reports for MGML Sample Database
"""
import os
import sys
import csv
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mgml_sampledb.settings')
import django
django.setup()

from sampletracking.models import CrudeSample, Aliquot, Extract, SequenceLibrary
from django.db.models import Count

def generate_sample_report():
    """Generate detailed reports for all sample types"""

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_dir = '/var/www/mgml_sampledb/reports'
    os.makedirs(report_dir, exist_ok=True)

    print("=" * 60)
    print("MGML SAMPLE DATABASE - COMPREHENSIVE SAMPLE REPORT")
    print("=" * 60)
    print(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Summary Statistics
    print("SUMMARY STATISTICS")
    print("-" * 40)
    crude_count = CrudeSample.objects.count()
    aliquot_count = Aliquot.objects.count()
    extract_count = Extract.objects.count()
    library_count = SequenceLibrary.objects.count()

    print(f"Total CrudeSamples:     {crude_count}")
    print(f"Total Aliquots:         {aliquot_count}")
    print(f"Total Extracts:         {extract_count}")
    print(f"Total SequenceLibraries: {library_count}")
    print(f"TOTAL SAMPLES:          {crude_count + aliquot_count + extract_count + library_count}")
    print()

    # CrudeSamples Report
    print("\nCRUDE SAMPLES DETAILED REPORT")
    print("=" * 60)

    crude_samples = CrudeSample.objects.all().order_by('collection_date', 'sample_id')

    # CSV Export for CrudeSamples
    csv_file = os.path.join(report_dir, f'crude_samples_{timestamp}.csv')
    with open(csv_file, 'w', newline='') as csvfile:
        fieldnames = ['Sample_ID', 'Base_ID', 'Barcode', 'Subject_ID', 'Sample_Source',
                     'Collection_Date', 'Date_Created', 'Freezer_ID', 'Box_ID', 'Well_ID',
                     'Status', 'Created_By', 'Notes']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for cs in crude_samples:
            print(f"\nSample ID: {cs.sample_id}")
            print(f"  Barcode:         {cs.barcode}")
            print(f"  Base ID:         {cs.base_id}")
            print(f"  Subject ID:      {cs.subject_id}")
            print(f"  Sample Source:   {cs.sample_source}")
            print(f"  Collection Date: {cs.collection_date}")
            print(f"  Date Created:    {cs.date_created}")
            print(f"  Storage:         Freezer={cs.freezer_ID}, Box={cs.box_ID}, Well={cs.well_ID}")
            print(f"  Status:          {cs.status}")
            print(f"  Created By:      {cs.created_by}")

            # Count children
            aliquot_count = cs.aliquots.count()
            print(f"  Child Aliquots:  {aliquot_count}")

            # Write to CSV
            writer.writerow({
                'Sample_ID': cs.sample_id,
                'Base_ID': cs.base_id,
                'Barcode': cs.barcode,
                'Subject_ID': cs.subject_id,
                'Sample_Source': cs.sample_source,
                'Collection_Date': cs.collection_date,
                'Date_Created': cs.date_created,
                'Freezer_ID': cs.freezer_ID or '',
                'Box_ID': cs.box_ID or '',
                'Well_ID': cs.well_ID or '',
                'Status': cs.status,
                'Created_By': str(cs.created_by) if cs.created_by else '',
                'Notes': cs.notes or ''
            })

    print(f"\n✅ CrudeSamples exported to: {csv_file}")

    # Aliquots Report
    print("\n\nALIQUOTS DETAILED REPORT")
    print("=" * 60)

    aliquots = Aliquot.objects.all().order_by('parent_barcode', 'sample_id')

    # CSV Export for Aliquots
    csv_file = os.path.join(report_dir, f'aliquots_{timestamp}.csv')
    with open(csv_file, 'w', newline='') as csvfile:
        fieldnames = ['Sample_ID', 'Base_ID', 'Barcode', 'Parent_Barcode', 'Parent_Sample_ID',
                     'Volume', 'Concentration', 'Date_Created', 'Freezer_ID', 'Box_ID',
                     'Well_ID', 'Status', 'Created_By']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for aliquot in aliquots:
            print(f"\nSample ID: {aliquot.sample_id}")
            print(f"  Barcode:         {aliquot.barcode}")
            print(f"  Base ID:         {aliquot.base_id}")
            print(f"  Parent Barcode:  {aliquot.parent_barcode.barcode}")
            print(f"  Parent Sample:   {aliquot.parent_barcode.sample_id}")
            print(f"  Volume:          {aliquot.volume} µL" if aliquot.volume else "  Volume:          N/A")
            print(f"  Concentration:   {aliquot.concentration}" if aliquot.concentration else "  Concentration:   N/A")
            print(f"  Date Created:    {aliquot.date_created}")
            print(f"  Storage:         Freezer={aliquot.freezer_ID}, Box={aliquot.box_ID}, Well={aliquot.well_ID}")
            print(f"  Status:          {aliquot.status}")

            # Count children
            extract_count = aliquot.extracts.count()
            print(f"  Child Extracts:  {extract_count}")

            # Write to CSV
            writer.writerow({
                'Sample_ID': aliquot.sample_id,
                'Base_ID': aliquot.base_id,
                'Barcode': aliquot.barcode,
                'Parent_Barcode': aliquot.parent_barcode.barcode,
                'Parent_Sample_ID': aliquot.parent_barcode.sample_id,
                'Volume': aliquot.volume or '',
                'Concentration': aliquot.concentration or '',
                'Date_Created': aliquot.date_created,
                'Freezer_ID': aliquot.freezer_ID or '',
                'Box_ID': aliquot.box_ID or '',
                'Well_ID': aliquot.well_ID or '',
                'Status': aliquot.status,
                'Created_By': str(aliquot.created_by) if aliquot.created_by else ''
            })

    print(f"\n✅ Aliquots exported to: {csv_file}")

    # Extracts Report
    print("\n\nEXTRACTS DETAILED REPORT")
    print("=" * 60)

    extracts = Extract.objects.all().order_by('parent', 'sample_id')

    # CSV Export for Extracts
    csv_file = os.path.join(report_dir, f'extracts_{timestamp}.csv')
    with open(csv_file, 'w', newline='') as csvfile:
        fieldnames = ['Sample_ID', 'Base_ID', 'Barcode', 'Parent_Barcode', 'Parent_Sample_ID',
                     'Extract_Type', 'Quality_Score', 'Concentration', 'Extraction_Method',
                     'Date_Created', 'Freezer_ID', 'Box_ID', 'Well_ID', 'Status', 'Created_By']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for extract in extracts:
            print(f"\nSample ID: {extract.sample_id}")
            print(f"  Barcode:         {extract.barcode}")
            print(f"  Base ID:         {extract.base_id}")
            print(f"  Parent Barcode:  {extract.parent.barcode}")
            print(f"  Parent Sample:   {extract.parent.sample_id}")
            print(f"  Extract Type:    {extract.extract_type}")
            print(f"  Quality Score:   {extract.quality_score}" if extract.quality_score else "  Quality Score:   N/A")
            print(f"  Concentration:   {extract.concentration} ng/µL" if extract.concentration else "  Concentration:   N/A")
            print(f"  Method:          {extract.extraction_method}" if extract.extraction_method else "  Method:          N/A")
            print(f"  Date Created:    {extract.date_created}")
            print(f"  Storage:         Freezer={extract.freezer_ID}, Box={extract.box_ID}, Well={extract.well_ID}")
            print(f"  Status:          {extract.status}")

            # Count children
            library_count = extract.libraries.count()
            print(f"  Child Libraries: {library_count}")

            # Write to CSV
            writer.writerow({
                'Sample_ID': extract.sample_id,
                'Base_ID': extract.base_id,
                'Barcode': extract.barcode,
                'Parent_Barcode': extract.parent.barcode,
                'Parent_Sample_ID': extract.parent.sample_id,
                'Extract_Type': extract.extract_type,
                'Quality_Score': extract.quality_score or '',
                'Concentration': extract.concentration or '',
                'Extraction_Method': extract.extraction_method or '',
                'Date_Created': extract.date_created,
                'Freezer_ID': extract.freezer_ID or '',
                'Box_ID': extract.box_ID or '',
                'Well_ID': extract.well_ID or '',
                'Status': extract.status,
                'Created_By': str(extract.created_by) if extract.created_by else ''
            })

    print(f"\n✅ Extracts exported to: {csv_file}")

    # Sample Source Summary
    print("\n\nSAMPLE SOURCE DISTRIBUTION")
    print("=" * 60)
    source_counts = CrudeSample.objects.values('sample_source').annotate(count=Count('id'))
    for source in source_counts:
        print(f"{source['sample_source']:15} {source['count']:5} samples")

    # Collection Date Summary
    print("\n\nCOLLECTION DATE DISTRIBUTION")
    print("=" * 60)
    date_counts = CrudeSample.objects.values('collection_date').annotate(count=Count('id')).order_by('collection_date')
    for date_group in date_counts:
        print(f"{date_group['collection_date']}:  {date_group['count']} samples")

    print("\n" + "=" * 60)
    print(f"✅ REPORT GENERATION COMPLETE")
    print(f"Reports saved to: {report_dir}")
    print("=" * 60)

    return report_dir

if __name__ == '__main__':
    generate_sample_report()