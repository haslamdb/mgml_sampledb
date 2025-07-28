from django.core.management.base import BaseCommand
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from sampletracking.models import CrudeSample, Aliquot, Extract, SequenceLibrary, Plate


class Command(BaseCommand):
    help = 'Generate a comprehensive dashboard report for the admin interface'

    def add_arguments(self, parser):
        parser.add_argument(
            '--format',
            type=str,
            default='console',
            choices=['console', 'json', 'html'],
            help='Output format for the dashboard report'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days to include in recent activity analysis'
        )

    def handle(self, *args, **options):
        format_type = options['format']
        days = options['days']
        
        # Calculate date range
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Gather statistics
        stats = self.gather_statistics(start_date, end_date)
        
        if format_type == 'console':
            self.output_console(stats, days)
        elif format_type == 'json':
            self.output_json(stats)
        elif format_type == 'html':
            self.output_html(stats, days)

    def gather_statistics(self, start_date, end_date):
        """Gather comprehensive statistics for the dashboard"""
        
        # Sample counts by type
        crude_samples = CrudeSample.objects.all()
        aliquots = Aliquot.objects.all()
        extracts = Extract.objects.all()
        libraries = SequenceLibrary.objects.all()
        plates = Plate.objects.all()
        
        # Status breakdowns
        sample_status_counts = crude_samples.values('status').annotate(count=Count('id'))
        aliquot_status_counts = aliquots.values('status').annotate(count=Count('id'))
        extract_status_counts = extracts.values('status').annotate(count=Count('id'))
        library_status_counts = libraries.values('status').annotate(count=Count('id'))
        
        # Recent activity
        recent_crude = crude_samples.filter(date_created__gte=start_date).count()
        recent_aliquots = aliquots.filter(date_created__gte=start_date).count()
        recent_extracts = extracts.filter(date_created__gte=start_date).count()
        recent_libraries = libraries.filter(date_created__gte=start_date).count()
        recent_plates = plates.filter(created_at__gte=start_date).count()
        
        # Sample source breakdown
        source_counts = crude_samples.values('sample_source').annotate(count=Count('id'))
        
        # Extract type breakdown
        extract_type_counts = extracts.values('extract_type').annotate(count=Count('id'))
        
        # Library type breakdown
        library_type_counts = libraries.values('library_type').annotate(count=Count('id'))
        
        # Quality metrics
        high_quality_extracts = extracts.filter(quality_score__gte=80).count()
        medium_quality_extracts = extracts.filter(quality_score__gte=60, quality_score__lt=80).count()
        low_quality_extracts = extracts.filter(quality_score__lt=60).count()
        
        # Sequencing status
        sequenced_libraries = libraries.filter(date_sequenced__isnull=False).count()
        pending_sequencing = libraries.filter(date_sequenced__isnull=True).count()
        
        # Storage utilization
        storage_locations = crude_samples.values('freezer_ID').annotate(count=Count('id')).order_by('-count')
        
        # User activity
        user_activity = crude_samples.values('created_by__username').annotate(count=Count('id')).order_by('-count')
        
        # Problem indicators
        contaminated_samples = crude_samples.filter(status='CONTAMINATED').count()
        exhausted_samples = crude_samples.filter(status='EXHAUSTED').count()
        override_used = crude_samples.filter(barcode_override_used=True).count()
        
        return {
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
            },
            'status_breakdowns': {
                'crude_samples': list(sample_status_counts),
                'aliquots': list(aliquot_status_counts),
                'extracts': list(extract_status_counts),
                'libraries': list(library_status_counts),
            },
            'sample_sources': list(source_counts),
            'extract_types': list(extract_type_counts),
            'library_types': list(library_type_counts),
            'quality_metrics': {
                'high_quality': high_quality_extracts,
                'medium_quality': medium_quality_extracts,
                'low_quality': low_quality_extracts,
            },
            'sequencing': {
                'sequenced': sequenced_libraries,
                'pending': pending_sequencing,
            },
            'storage_utilization': list(storage_locations[:10]),  # Top 10 freezers
            'user_activity': list(user_activity[:10]),  # Top 10 users
            'problems': {
                'contaminated': contaminated_samples,
                'exhausted': exhausted_samples,
                'overrides': override_used,
            }
        }

    def output_console(self, stats, days):
        """Output dashboard in console format"""
        self.stdout.write(self.style.SUCCESS('\n🧬 MGML Sample Database Dashboard'))
        self.stdout.write(self.style.SUCCESS('=' * 50))
        
        # Totals
        self.stdout.write(f"\n📊 Overall Statistics:")
        self.stdout.write(f"  • Crude Samples: {stats['totals']['crude_samples']:,}")
        self.stdout.write(f"  • Aliquots: {stats['totals']['aliquots']:,}")
        self.stdout.write(f"  • Extracts: {stats['totals']['extracts']:,}")
        self.stdout.write(f"  • Libraries: {stats['totals']['libraries']:,}")
        self.stdout.write(f"  • Plates: {stats['totals']['plates']:,}")
        
        # Recent activity
        self.stdout.write(f"\n📅 Recent Activity (Last {days} days):")
        self.stdout.write(f"  • New Crude Samples: {stats['recent_activity']['crude_samples']}")
        self.stdout.write(f"  • New Aliquots: {stats['recent_activity']['aliquots']}")
        self.stdout.write(f"  • New Extracts: {stats['recent_activity']['extracts']}")
        self.stdout.write(f"  • New Libraries: {stats['recent_activity']['libraries']}")
        self.stdout.write(f"  • New Plates: {stats['recent_activity']['plates']}")
        
        # Status breakdowns
        self.stdout.write(f"\n📈 Status Breakdowns:")
        for status_data in stats['status_breakdowns']['crude_samples']:
            status = status_data['status'] or 'Unknown'
            count = status_data['count']
            self.stdout.write(f"  • Crude Samples - {status}: {count}")
        
        # Quality metrics
        self.stdout.write(f"\n🎯 Quality Metrics:")
        self.stdout.write(f"  • High Quality Extracts (≥80): {stats['quality_metrics']['high_quality']}")
        self.stdout.write(f"  • Medium Quality Extracts (60-79): {stats['quality_metrics']['medium_quality']}")
        self.stdout.write(f"  • Low Quality Extracts (<60): {stats['quality_metrics']['low_quality']}")
        
        # Sequencing status
        self.stdout.write(f"\n🔬 Sequencing Status:")
        self.stdout.write(f"  • Sequenced Libraries: {stats['sequencing']['sequenced']}")
        self.stdout.write(f"  • Pending Sequencing: {stats['sequencing']['pending']}")
        
        # Problems
        problems = stats['problems']
        if any(problems.values()):
            self.stdout.write(self.style.WARNING(f"\n⚠️  Issues Requiring Attention:"))
            if problems['contaminated']:
                self.stdout.write(self.style.WARNING(f"  • Contaminated Samples: {problems['contaminated']}"))
            if problems['exhausted']:
                self.stdout.write(self.style.WARNING(f"  • Exhausted Samples: {problems['exhausted']}"))
            if problems['overrides']:
                self.stdout.write(self.style.WARNING(f"  • Barcode Overrides Used: {problems['overrides']}"))
        else:
            self.stdout.write(self.style.SUCCESS(f"\n✅ No Critical Issues Found"))
        
        # Top storage locations
        if stats['storage_utilization']:
            self.stdout.write(f"\n🏪 Top Storage Locations:")
            for location in stats['storage_utilization'][:5]:
                freezer = location['freezer_ID'] or 'Unknown'
                count = location['count']
                self.stdout.write(f"  • {freezer}: {count} samples")
        
        # Top users
        if stats['user_activity']:
            self.stdout.write(f"\n👤 Most Active Users:")
            for user in stats['user_activity'][:5]:
                username = user['created_by__username'] or 'Unknown'
                count = user['count']
                self.stdout.write(f"  • {username}: {count} samples created")
        
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 50))

    def output_json(self, stats):
        """Output dashboard in JSON format"""
        import json
        self.stdout.write(json.dumps(stats, indent=2, default=str))

    def output_html(self, stats, days):
        """Output dashboard in HTML format"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>MGML Sample Database Dashboard</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f8f9fa; }}
        .dashboard {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ text-align: center; color: #333; margin-bottom: 30px; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }}
        .card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .card h3 {{ margin-top: 0; color: #495057; border-bottom: 2px solid #dee2e6; padding-bottom: 10px; }}
        .metric {{ display: flex; justify-content: space-between; margin: 10px 0; }}
        .metric-value {{ font-weight: bold; color: #007bff; }}
        .warning {{ color: #dc3545; }}
        .success {{ color: #28a745; }}
        .info {{ color: #17a2b8; }}
        .badge {{ padding: 2px 8px; border-radius: 12px; font-size: 12px; }}
        .badge-success {{ background: #d4edda; color: #155724; }}
        .badge-warning {{ background: #fff3cd; color: #856404; }}
        .badge-danger {{ background: #f8d7da; color: #721c24; }}
    </style>
</head>
<body>
    <div class="dashboard">
        <div class="header">
            <h1>🧬 MGML Sample Database Dashboard</h1>
            <p>Generated on {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="stats-grid">
            <div class="card">
                <h3>📊 Overall Statistics</h3>
                <div class="metric">
                    <span>Crude Samples:</span>
                    <span class="metric-value">{stats['totals']['crude_samples']:,}</span>
                </div>
                <div class="metric">
                    <span>Aliquots:</span>
                    <span class="metric-value">{stats['totals']['aliquots']:,}</span>
                </div>
                <div class="metric">
                    <span>Extracts:</span>
                    <span class="metric-value">{stats['totals']['extracts']:,}</span>
                </div>
                <div class="metric">
                    <span>Libraries:</span>
                    <span class="metric-value">{stats['totals']['libraries']:,}</span>
                </div>
                <div class="metric">
                    <span>Plates:</span>
                    <span class="metric-value">{stats['totals']['plates']:,}</span>
                </div>
            </div>
            
            <div class="card">
                <h3>📅 Recent Activity ({days} days)</h3>
                <div class="metric">
                    <span>New Crude Samples:</span>
                    <span class="metric-value info">{stats['recent_activity']['crude_samples']}</span>
                </div>
                <div class="metric">
                    <span>New Aliquots:</span>
                    <span class="metric-value info">{stats['recent_activity']['aliquots']}</span>
                </div>
                <div class="metric">
                    <span>New Extracts:</span>
                    <span class="metric-value info">{stats['recent_activity']['extracts']}</span>
                </div>
                <div class="metric">
                    <span>New Libraries:</span>
                    <span class="metric-value info">{stats['recent_activity']['libraries']}</span>
                </div>
                <div class="metric">
                    <span>New Plates:</span>
                    <span class="metric-value info">{stats['recent_activity']['plates']}</span>
                </div>
            </div>
            
            <div class="card">
                <h3>🎯 Quality Metrics</h3>
                <div class="metric">
                    <span>High Quality (≥80):</span>
                    <span class="metric-value success">{stats['quality_metrics']['high_quality']}</span>
                </div>
                <div class="metric">
                    <span>Medium Quality (60-79):</span>
                    <span class="metric-value info">{stats['quality_metrics']['medium_quality']}</span>
                </div>
                <div class="metric">
                    <span>Low Quality (<60):</span>
                    <span class="metric-value warning">{stats['quality_metrics']['low_quality']}</span>
                </div>
            </div>
            
            <div class="card">
                <h3>🔬 Sequencing Status</h3>
                <div class="metric">
                    <span>Sequenced Libraries:</span>
                    <span class="metric-value success">{stats['sequencing']['sequenced']}</span>
                </div>
                <div class="metric">
                    <span>Pending Sequencing:</span>
                    <span class="metric-value warning">{stats['sequencing']['pending']}</span>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
        """
        self.stdout.write(html)
