from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from .models import CrudeSample, Aliquot, Extract, SequenceLibrary, Plate


def admin_stats(request):
    """
    Context processor to provide admin dashboard statistics
    """
    # Debug: write to file to see if this is being called
    import os
    with open('/tmp/debug_context.log', 'a') as f:
        f.write(f"Context processor called for: {request.path}\n")
    
    # Always provide stats for testing
    print(f"DEBUG: Request path: {request.path}")
    
    # Calculate date range for recent activity (last 30 days)
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    # Sample counts by type
    crude_samples = CrudeSample.objects.all()
    aliquots = Aliquot.objects.all()
    extracts = Extract.objects.all()
    libraries = SequenceLibrary.objects.all()
    plates = Plate.objects.all()
    
    # Recent activity
    recent_crude = crude_samples.filter(date_created__gte=start_date).count()
    recent_aliquots = aliquots.filter(date_created__gte=start_date).count()
    recent_extracts = extracts.filter(date_created__gte=start_date).count()
    recent_libraries = libraries.filter(date_created__gte=start_date).count()
    recent_plates = plates.filter(created_at__gte=start_date).count()
    
    # Status breakdowns
    sample_status_counts = crude_samples.values('status').annotate(count=Count('id'))
    
    # Problem indicators
    contaminated_samples = crude_samples.filter(status='CONTAMINATED').count()
    exhausted_samples = crude_samples.filter(status='EXHAUSTED').count()
    override_used = crude_samples.filter(barcode_override_used=True).count()
    
    # Quality metrics
    high_quality_extracts = extracts.filter(quality_score__gte=80).count()
    medium_quality_extracts = extracts.filter(quality_score__gte=60, quality_score__lt=80).count()
    low_quality_extracts = extracts.filter(quality_score__lt=60).count()
    
    # Sequencing status
    sequenced_libraries = libraries.filter(date_sequenced__isnull=False).count()
    pending_sequencing = libraries.filter(date_sequenced__isnull=True).count()
    
    return {
        'admin_stats': {
            'totals': {
                'crude_samples': crude_samples.count(),
                'aliquots': aliquots.count(),
                'extracts': extracts.count(),
                'libraries': libraries.count(),
                'plates': plates.count(),
            },
            'recent_activity': {
                'crude_samples': recent_crude,
                'aliquots': recent_aliquots,
                'extracts': recent_extracts,
                'libraries': recent_libraries,
                'plates': recent_plates,
                'total': recent_crude + recent_aliquots + recent_extracts + recent_libraries + recent_plates,
            },
            'status_breakdowns': {
                'available': crude_samples.filter(status='AVAILABLE').count(),
                'awaiting_receipt': crude_samples.filter(status='AWAITING_RECEIPT').count(),
                'in_process': crude_samples.filter(status='IN_PROCESS').count(),
                'contaminated': contaminated_samples,
                'exhausted': exhausted_samples,
                'archived': crude_samples.filter(status='ARCHIVED').count(),
            },
            'quality_metrics': {
                'high_quality': high_quality_extracts,
                'medium_quality': medium_quality_extracts,
                'low_quality': low_quality_extracts,
            },
            'sequencing': {
                'sequenced': sequenced_libraries,
                'pending': pending_sequencing,
            },
            'problems': {
                'contaminated': contaminated_samples,
                'exhausted': exhausted_samples,
                'overrides': override_used,
                'total_issues': contaminated_samples + exhausted_samples + override_used,
            }
        }
    }
