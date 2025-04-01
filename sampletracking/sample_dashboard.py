from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta

from .models import CrudeSample, Aliquot, Extract, SequenceLibrary


@login_required
def dashboard(request):
    """
    Display an overview dashboard of sample statistics
    """
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    # Count of each sample type
    crude_count = CrudeSample.objects.count()
    aliquot_count = Aliquot.objects.count()
    extract_count = Extract.objects.count()
    library_count = SequenceLibrary.objects.count()

    # Recent counts (last 7 days)
    recent_crude = CrudeSample.objects.filter(date_created__gte=week_ago).count()
    recent_aliquot = Aliquot.objects.filter(date_created__gte=week_ago).count()
    recent_extract = Extract.objects.filter(date_created__gte=week_ago).count()
    recent_library = SequenceLibrary.objects.filter(date_created__gte=week_ago).count()

    # Samples by source
    source_distribution = CrudeSample.objects.values('sample_source') \
                                       .annotate(count=Count('id')) \
                                       .order_by('-count')

    # Libraries awaiting sequencing
    awaiting_sequencing = SequenceLibrary.objects.filter(date_sequenced__isnull=True).count()

    # Library types distribution
    library_types = SequenceLibrary.objects.values('library_type') \
                                     .annotate(count=Count('id')) \
                                     .order_by('-count')

    # Extract types distribution
    extract_types = Extract.objects.values('extract_type') \
                                  .annotate(count=Count('id')) \
                                  .order_by('-count')

    # Recent samples
    recent_samples = CrudeSample.objects.order_by('-date_created')[:10]

    context = {
        'crude_count': crude_count,
        'aliquot_count': aliquot_count,
        'extract_count': extract_count,
        'library_count': library_count,
        'recent_crude': recent_crude,
        'recent_aliquot': recent_aliquot,
        'recent_extract': recent_extract,
        'recent_library': recent_library,
        'source_distribution': source_distribution,
        'awaiting_sequencing': awaiting_sequencing,
        'library_types': library_types,
        'extract_types': extract_types,
        'recent_samples': recent_samples,
    }

    return render(request, 'sampletracking/dashboard.html', context)
