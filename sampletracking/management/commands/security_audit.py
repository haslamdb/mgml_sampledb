"""
Security audit management command for MGML Sample Database
Usage: python manage.py security_audit
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger('security')

class Command(BaseCommand):
    help = 'Perform security audit of the sample database'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days to analyze (default: 7)'
        )
        parser.add_argument(
            '--report-file',
            type=str,
            help='Save report to file'
        )
    
    def handle(self, *args, **options):
        days = options['days']
        report_file = options.get('report_file')
        
        self.stdout.write(f"🔍 Security Audit Report - Last {days} days")
        self.stdout.write("=" * 50)
        
        report_lines = []
        report_lines.append(f"Security Audit Report - Last {days} days")
        report_lines.append("=" * 50)
        
        # Check for users with excessive permissions
        self.audit_user_permissions(report_lines)
        
        # Check for inactive users with active sessions
        self.audit_inactive_users(report_lines, days)
        
        # Check for suspicious barcode patterns
        self.audit_barcode_patterns(report_lines, days)
        
        # Check for failed login attempts
        self.audit_login_attempts(report_lines, days)
        
        # Check for data integrity issues
        self.audit_data_integrity(report_lines)
        
        # Security recommendations
        self.security_recommendations(report_lines)
        
        # Output report
        for line in report_lines:
            self.stdout.write(line)
        
        # Save to file if requested
        if report_file:
            with open(report_file, 'w') as f:
                f.write('\n'.join(report_lines))
            self.stdout.write(f"\n📁 Report saved to: {report_file}")
    
    def audit_user_permissions(self, report_lines):
        """Audit user permissions and roles"""
        report_lines.append("\n👥 User Permissions Audit")
        report_lines.append("-" * 30)
        
        # Check for superusers
        superusers = User.objects.filter(is_superuser=True)
        report_lines.append(f"Superusers: {superusers.count()}")
        for user in superusers:
            last_login = user.last_login.strftime('%Y-%m-%d %H:%M') if user.last_login else 'Never'
            report_lines.append(f"  - {user.username} (last login: {last_login})")
        
        # Check for staff users
        staff_users = User.objects.filter(is_staff=True, is_superuser=False)
        report_lines.append(f"Staff users: {staff_users.count()}")
        
        # Check for users with multiple group memberships
        users_multiple_groups = User.objects.annotate(
            group_count=Count('groups')
        ).filter(group_count__gt=1)
        
        if users_multiple_groups.exists():
            report_lines.append("⚠️  Users with multiple group memberships:")
            for user in users_multiple_groups:
                groups = ', '.join([g.name for g in user.groups.all()])
                report_lines.append(f"  - {user.username}: {groups}")
    
    def audit_inactive_users(self, report_lines, days):
        """Check for inactive users"""
        report_lines.append("\n💤 Inactive Users Audit")
        report_lines.append("-" * 30)
        
        cutoff_date = timezone.now() - timedelta(days=days)
        inactive_users = User.objects.filter(
            last_login__lt=cutoff_date,
            is_active=True
        )
        
        report_lines.append(f"Users inactive for {days}+ days: {inactive_users.count()}")
        for user in inactive_users[:10]:  # Show first 10
            last_login = user.last_login.strftime('%Y-%m-%d') if user.last_login else 'Never'
            report_lines.append(f"  - {user.username} (last login: {last_login})")
        
        if inactive_users.count() > 10:
            report_lines.append(f"  ... and {inactive_users.count() - 10} more")
    
    def audit_barcode_patterns(self, report_lines, days):
        """Check for suspicious barcode patterns"""
        from sampletracking.models import CrudeSample, Aliquot, Extract, SequenceLibrary
        
        report_lines.append("\n🔢 Barcode Pattern Audit")
        report_lines.append("-" * 30)
        
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Check for barcode overrides
        override_samples = CrudeSample.objects.filter(
            barcode_override_used=True,
            created_at__gte=cutoff_date
        )
        
        report_lines.append(f"Samples with barcode overrides: {override_samples.count()}")
        if override_samples.exists():
            report_lines.append("⚠️  Recent barcode overrides:")
            for sample in override_samples[:5]:
                report_lines.append(f"  - {sample.barcode} by {sample.created_by}")
        
        # Check for duplicate-like barcodes
        all_models = [CrudeSample, Aliquot, Extract, SequenceLibrary]
        similar_barcodes = []
        
        for model in all_models:
            barcodes = model.objects.values_list('barcode', flat=True)
            for i, barcode1 in enumerate(barcodes):
                for barcode2 in list(barcodes)[i+1:]:
                    if self.are_similar_barcodes(barcode1, barcode2):
                        similar_barcodes.append((barcode1, barcode2))
        
        if similar_barcodes:
            report_lines.append("⚠️  Similar barcodes found:")
            for bc1, bc2 in similar_barcodes[:5]:
                report_lines.append(f"  - {bc1} / {bc2}")
    
    def audit_login_attempts(self, report_lines, days):
        """Audit login attempts from logs"""
        report_lines.append("\n🔐 Login Attempts Audit")
        report_lines.append("-" * 30)
        
        # This would require parsing log files
        # For now, provide placeholder
        report_lines.append("📋 Check application logs for:")
        report_lines.append("  - Failed login attempts")
        report_lines.append("  - Multiple rapid login attempts")
        report_lines.append("  - Login attempts from unusual IPs")
        report_lines.append("  - Login attempts outside business hours")
    
    def audit_data_integrity(self, report_lines):
        """Check data integrity issues"""
        from sampletracking.models import CrudeSample, Aliquot, Extract, SequenceLibrary
        
        report_lines.append("\n🔍 Data Integrity Audit")
        report_lines.append("-" * 30)
        
        # Check for orphaned records
        orphaned_aliquots = Aliquot.objects.filter(parent_barcode__isnull=True)
        orphaned_extracts = Extract.objects.filter(parent__isnull=True)
        orphaned_libraries = SequenceLibrary.objects.filter(parent__isnull=True)
        
        report_lines.append(f"Orphaned aliquots: {orphaned_aliquots.count()}")
        report_lines.append(f"Orphaned extracts: {orphaned_extracts.count()}")
        report_lines.append(f"Orphaned libraries: {orphaned_libraries.count()}")
        
        # Check for missing required fields
        samples_no_barcode = CrudeSample.objects.filter(Q(barcode='') | Q(barcode__isnull=True))
        report_lines.append(f"Samples without barcodes: {samples_no_barcode.count()}")
        
        # Check for future dates
        future_samples = CrudeSample.objects.filter(collection_date__gt=timezone.now().date())
        report_lines.append(f"Samples with future collection dates: {future_samples.count()}")
    
    def security_recommendations(self, report_lines):
        """Provide security recommendations"""
        report_lines.append("\n💡 Security Recommendations")
        report_lines.append("-" * 30)
        
        recommendations = [
            "✅ Regular password updates for all users",
            "✅ Review and remove inactive user accounts",
            "✅ Monitor failed login attempts",
            "✅ Regular database backups",
            "✅ Keep Django and dependencies updated",
            "✅ Review user permissions regularly",
            "✅ Enable two-factor authentication",
            "✅ Monitor for suspicious barcode patterns",
            "✅ Regular security audits",
            "✅ Log review and analysis"
        ]
        
        for rec in recommendations:
            report_lines.append(f"  {rec}")
    
    def are_similar_barcodes(self, bc1, bc2):
        """Check if two barcodes are suspiciously similar"""
        if len(bc1) != len(bc2):
            return False
        
        if len(bc1) < 3:
            return False
        
        # Check if they differ by only 1-2 characters
        differences = sum(c1 != c2 for c1, c2 in zip(bc1, bc2))
        return 1 <= differences <= 2
