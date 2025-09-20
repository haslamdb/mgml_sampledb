"""
Management command to import legacy sequencing samples from CSV file.

CSV should have these columns (all optional except subject_id and collection_date):
- subject_id: Required - Subject/patient identifier
- collection_date: Required - Date sample was collected (YYYY-MM-DD)
- legacy_sequence_filename: Legacy filename (without _R1/_R2)
- project_name: Project or study name
- investigator: PI name
- patient_type: Patient group or classification (IBD, Control, etc.)
- study_id: External study ID
- sample_source: Sample type (Stool, Blood, etc.) - default: 'Unknown'
- barcode: Sample barcode (will auto-generate if not provided)
- n_index: N-index for sequencing
- s_index: S-index for sequencing
- library_type: Library prep type (Nextera, etc.)
- sequencing_date: Date sequenced (YYYY-MM-DD)
- sequencing_platform: Platform used (NovaSeq, etc.)
- notes: Any additional notes
- data_file_location: Path to sequence files

Usage:
python manage.py import_legacy_samples /path/to/import.csv --dry-run
python manage.py import_legacy_samples /path/to/import.csv
"""

import csv
import os
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.contrib.auth.models import User
from sampletracking.models import CrudeSample, Aliquot, Extract, SequenceLibrary


class Command(BaseCommand):
    help = 'Import legacy sequencing samples from CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to CSV file')
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview what would be imported without making changes'
        )
        parser.add_argument(
            '--skip-intermediates',
            action='store_true',
            help='Skip creation of Aliquot and Extract records'
        )
        parser.add_argument(
            '--username',
            type=str,
            default='admin',
            help='Username to use as creator (default: admin)'
        )

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        dry_run = options['dry_run']
        skip_intermediates = options['skip_intermediates']

        if not os.path.exists(csv_file):
            raise CommandError(f'CSV file does not exist: {csv_file}')

        # Get user for created_by field
        try:
            user = User.objects.get(username=options['username'])
        except User.DoesNotExist:
            raise CommandError(f"User '{options['username']}' does not exist")

        imported_count = 0
        skipped_count = 0
        errors = []

        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            if dry_run:
                self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))

            for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
                try:
                    # Required fields
                    subject_id = row.get('subject_id', '').strip()
                    collection_date_str = row.get('collection_date', '').strip()

                    if not subject_id:
                        errors.append(f"Row {row_num}: Missing required subject_id")
                        skipped_count += 1
                        continue

                    if not collection_date_str:
                        errors.append(f"Row {row_num}: Missing required collection_date")
                        skipped_count += 1
                        continue

                    # Parse collection date
                    try:
                        collection_date = datetime.strptime(collection_date_str, '%Y-%m-%d').date()
                    except ValueError:
                        errors.append(f"Row {row_num}: Invalid date format '{collection_date_str}' (use YYYY-MM-DD)")
                        skipped_count += 1
                        continue

                    # Optional fields with defaults
                    legacy_filename = row.get('legacy_sequence_filename', '').strip()
                    project_name = row.get('project_name', '').strip()
                    investigator = row.get('investigator', '').strip()
                    patient_type = row.get('patient_type', '').strip()
                    study_id = row.get('study_id', '').strip()
                    sample_source = row.get('sample_source', '').strip() or 'Unknown'
                    isolate_source = row.get('isolate_source', '').strip()  # New field
                    notes = row.get('notes', '').strip()
                    data_file_location = row.get('data_file_location', '').strip()

                    # Sequencing specific fields
                    barcode = row.get('barcode', '').strip()
                    n_index = row.get('n_index', '').strip()
                    s_index = row.get('s_index', '').strip()
                    library_type = row.get('library_type', '').strip() or 'Other'
                    sequencing_date_str = row.get('sequencing_date', '').strip()
                    sequencing_platform = row.get('sequencing_platform', '').strip()

                    # Parse sequencing date if provided
                    sequencing_date = None
                    if sequencing_date_str:
                        try:
                            sequencing_date = datetime.strptime(sequencing_date_str, '%Y-%m-%d').date()
                        except ValueError:
                            self.stdout.write(
                                self.style.WARNING(
                                    f"Row {row_num}: Invalid sequencing date '{sequencing_date_str}', skipping"
                                )
                            )

                    if dry_run:
                        self.stdout.write(
                            f"Would import: {subject_id} ({legacy_filename or 'no legacy filename'})"
                        )
                        imported_count += 1
                        continue

                    # Create records in a transaction
                    with transaction.atomic():
                        # Auto-generate barcode if not provided
                        if not barcode:
                            barcode = f"LEGACY_{subject_id}_{row_num}"

                        # 1. Create CrudeSample
                        crude_sample_data = {
                            'barcode': f"{barcode}_CR",
                            'subject_id': subject_id,
                            'collection_date': collection_date,
                            'sample_source': sample_source,
                            'date_created': collection_date,
                            'status': 'ARCHIVED',  # Mark legacy samples as archived
                            'project_name': project_name,
                            'investigator': investigator,
                            'patient_type': patient_type,
                            'study_id': study_id,
                            'notes': f"Legacy import. {notes}".strip(),
                            'created_by': user,
                            'updated_by': user
                        }

                        # Only add isolate_source if sample_source is 'Isolate' and isolate_source is provided
                        if sample_source == 'Isolate' and isolate_source:
                            crude_sample_data['isolate_source'] = isolate_source

                        crude_sample = CrudeSample.objects.create(**crude_sample_data)

                        if skip_intermediates:
                            # Create SequenceLibrary directly linked to CrudeSample
                            # This is a simplified import - normally it would go through Aliquot/Extract
                            library_barcode = f"{barcode}_SL"
                        else:
                            # 2. Create Aliquot (minimal record)
                            aliquot = Aliquot.objects.create(
                                barcode=f"{barcode}_AL",
                                parent_barcode=crude_sample,
                                date_created=collection_date,
                                status='ARCHIVED',
                                project_name=project_name,
                                investigator=investigator,
                                patient_type=patient_type,
                                study_id=study_id,
                                notes="Legacy import - intermediate record",
                                created_by=user,
                                updated_by=user
                            )

                            # 3. Create Extract (minimal record)
                            extract = Extract.objects.create(
                                barcode=f"{barcode}_EX",
                                parent=aliquot,
                                extract_type='DNA',  # Default assumption
                                date_created=collection_date,
                                status='ARCHIVED',
                                project_name=project_name,
                                investigator=investigator,
                                patient_type=patient_type,
                                study_id=study_id,
                                notes="Legacy import - intermediate record",
                                created_by=user,
                                updated_by=user
                            )

                            library_barcode = f"{barcode}_SL"
                            parent_extract = extract

                        # 4. Create SequenceLibrary
                        if not skip_intermediates:
                            sequence_library = SequenceLibrary.objects.create(
                                barcode=library_barcode,
                                parent=parent_extract,
                                library_type=library_type,
                                nindex=n_index,
                                sindex=s_index,
                                date_created=collection_date,
                                date_sequenced=sequencing_date,
                                sequencing_platform=sequencing_platform,
                                status='ARCHIVED',
                                project_name=project_name,
                                investigator=investigator,
                                patient_type=patient_type,
                                study_id=study_id,
                                legacy_sequence_filename=legacy_filename,
                                data_file_location=data_file_location,
                                is_legacy_import=True,
                                notes=f"Legacy import. {notes}".strip(),
                                created_by=user,
                                updated_by=user
                            )

                        self.stdout.write(
                            self.style.SUCCESS(
                                f"Imported: {subject_id} (barcode: {barcode})"
                            )
                        )
                        imported_count += 1

                except Exception as e:
                    errors.append(f"Row {row_num}: Error - {str(e)}")
                    skipped_count += 1
                    if not dry_run:
                        self.stdout.write(
                            self.style.ERROR(f"Error on row {row_num}: {str(e)}")
                        )

        # Print summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f"Import completed:"))
        self.stdout.write(f"  - Imported: {imported_count} samples")
        self.stdout.write(f"  - Skipped: {skipped_count} samples")

        if errors:
            self.stdout.write('')
            self.stdout.write(self.style.ERROR("Errors encountered:"))
            for error in errors[:10]:  # Show first 10 errors
                self.stdout.write(f"  - {error}")
            if len(errors) > 10:
                self.stdout.write(f"  ... and {len(errors) - 10} more errors")