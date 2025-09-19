
from sampletracking.models import CrudeSample, Aliquot, Extract, SequenceLibrary

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

def run():
    # First, populate CrudeSamples to establish the base_id
    for sample in CrudeSample.objects.all().order_by('pk'):
        if not sample.base_id:
            type_code = TYPE_CODES.get(sample.sample_source, 'XX')
            date_str = sample.collection_date.strftime('%y%m%d')
            # Use a temporary unique identifier for the base_id during back-population
            base_id = f'{type_code}-{date_str}-{str(sample.pk).zfill(4)}'
            sample.base_id = base_id
            sample.sample_id = f'{base_id}-CS'
            sample.save()

    # Populate Aliquots
    for aliquot in Aliquot.objects.all().order_by('pk'):
        if not aliquot.sample_id and aliquot.parent_barcode and aliquot.parent_barcode.base_id:
            aliquot.base_id = aliquot.parent_barcode.base_id
            aliquot.sample_id = f'{aliquot.base_id}-AL-{aliquot.pk}'
            aliquot.save()

    # Populate Extracts
    for extract in Extract.objects.all().order_by('pk'):
        if not extract.sample_id and extract.parent and extract.parent.base_id:
            extract.base_id = extract.parent.base_id
            extract.sample_id = f'{extract.base_id}-EX-{extract.pk}'
            extract.save()

    # Populate SequenceLibraries
    for library in SequenceLibrary.objects.all().order_by('pk'):
        if not library.sample_id and library.parent and library.parent.base_id:
            library.base_id = library.parent.base_id
            library.sample_id = f'{library.base_id}-SL-{library.pk}'
            library.save()

run()
