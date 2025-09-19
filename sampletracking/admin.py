from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Q
from django.utils.safestring import mark_safe
from .models import CrudeSample, Aliquot, Extract, SequenceLibrary, Plate

from django.contrib.admin import AdminSite
from django.urls import path
from datetime import timedelta
from django.utils import timezone

# Customize admin site header and title with better styling
admin.site.site_header = "🧬 MGML Sample Database Administration"
admin.site.site_title = "MGML Sample DB"
admin.site.index_title = "📊 Laboratory Sample Management Dashboard"

class MyAdminSite(AdminSite):
    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('', self.admin_view(self.index))
        ]
        return my_urls + urls

    def index(self, request, extra_context=None):
        extra_context = extra_context or {}
        
        # Total Samples
        total_samples = CrudeSample.objects.count()
        
        # Recent Activity (last 30 days)
        thirty_days_ago = timezone.localtime() - timedelta(days=30)
        recent_activity = CrudeSample.objects.filter(created_at__gte=thirty_days_ago).count()
        
        # Available Samples
        available_samples = CrudeSample.objects.filter(status='AVAILABLE').count()
        
        # Attention Needed (barcode overrides)
        attention_needed = CrudeSample.objects.filter(barcode_override_used=True).count()
        
        extra_context['total_samples'] = total_samples
        extra_context['recent_activity'] = recent_activity
        extra_context['available_samples'] = available_samples
        extra_context['attention_needed'] = attention_needed
        
        return super().index(request, extra_context=extra_context)

# This is not used, but we keep it here as a reference if we need to replace the default admin site
# admin_site = MyAdminSite()

# Note: enable_nav_sidebar was deprecated in Django 3.1+


# Custom filters for better data organization
class StatusFilter(admin.SimpleListFilter):
    title = 'Sample Status'
    parameter_name = 'status'

    def lookups(self, request, model_admin):
        return [
            ('active', '🟢 Active Samples'),
            ('processing', '🟡 In Process'),
            ('completed', '🔵 Completed'),
            ('issues', '🔴 Issues'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'active':
            return queryset.filter(status__in=['AVAILABLE', 'AWAITING_RECEIPT'])
        if self.value() == 'processing':
            return queryset.filter(status='IN_PROCESS')
        if self.value() == 'completed':
            return queryset.filter(status='ARCHIVED')
        if self.value() == 'issues':
            return queryset.filter(status__in=['EXHAUSTED', 'CONTAMINATED'])


class RecentSamplesFilter(admin.SimpleListFilter):
    title = 'Creation Date'
    parameter_name = 'recent'

    def lookups(self, request, model_admin):
        return [
            ('today', '📅 Today'),
            ('week', '📅 This Week'),
            ('month', '📅 This Month'),
            ('quarter', '📅 This Quarter'),
        ]

    def queryset(self, request, queryset):
        from datetime import timedelta
        from django.utils import timezone
        now = timezone.localtime()

        if self.value() == 'today':
            return queryset.filter(date_created=now.date())
        elif self.value() == 'week':
            start_week = now.date() - timedelta(days=7)
            return queryset.filter(date_created__gte=start_week)
        elif self.value() == 'month':
            start_month = now.date() - timedelta(days=30)
            return queryset.filter(date_created__gte=start_month)
        elif self.value() == 'quarter':
            start_quarter = now.date() - timedelta(days=90)
            return queryset.filter(date_created__gte=start_quarter)


@admin.action(description="📦 Mark selected samples as archived")
def mark_archived(modeladmin, request, queryset):
    updated = queryset.update(status='ARCHIVED')
    modeladmin.message_user(
        request,
        f"Successfully archived {updated} samples.",
        level='SUCCESS'
    )


@admin.action(description="✅ Mark selected samples as available")
def mark_available(modeladmin, request, queryset):
    updated = queryset.update(status='AVAILABLE')
    modeladmin.message_user(
        request,
        f"Successfully marked {updated} samples as available.",
        level='SUCCESS'
    )


@admin.action(description="⚠️ Mark selected samples as contaminated")
def mark_contaminated(modeladmin, request, queryset):
    updated = queryset.update(status='CONTAMINATED')
    modeladmin.message_user(
        request,
        f"Marked {updated} samples as contaminated.",
        level='WARNING'
    )


class SampleAdmin(admin.ModelAdmin):
    """
    Enhanced base admin configuration for all sample types with better formatting
    """
    list_display = ('sample_id_display', 'barcode_display', 'status_badge', 'date_display', 'created_by_display', 'last_updated')
    list_filter = (StatusFilter, RecentSamplesFilter, 'created_by')
    search_fields = ('barcode', 'sample_id', 'base_id', 'notes')
    readonly_fields = ('sample_id', 'base_id', 'created_at', 'updated_at', 'created_by', 'updated_by')
    date_hierarchy = 'date_created'
    actions = [mark_archived, mark_available, mark_contaminated]
    list_per_page = 25
    list_max_show_all = 100
    
    class Media:
        css = {
            'all': ('admin/css/custom_admin.css',)
        }
        js = ('admin/js/admin_enhancements.js',)
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['barcode'].widget.attrs.update({
            'class': 'custom-barcode-field',
            'placeholder': 'Enter barcode...'
        })
        return form
    
    def barcode_display(self, obj):
        return format_html(
            '<code style="background: #f8f9fa; padding: 2px 6px; border-radius: 3px; '
            'font-family: monospace; font-size: 12px; border: 1px solid #dee2e6;" '
            'title="Click to copy">{}</code>',
            obj.barcode
        )
    barcode_display.short_description = '🏷️ Barcode'
    barcode_display.admin_order_field = 'barcode'

    def sample_id_display(self, obj):
        """Display sample ID with formatting"""
        if obj.sample_id:
            return format_html(
                '<span style="color: #007bff; font-weight: bold; font-family: monospace;">{}</span>',
                obj.sample_id
            )
        return format_html('<span style="color: #999;">-</span>')
    sample_id_display.short_description = '🧬 Sample ID'
    sample_id_display.admin_order_field = 'sample_id'

    def status_badge(self, obj):
        status_config = {
            'AWAITING_RECEIPT': {'color': '#17a2b8', 'icon': '⏳', 'bg': '#d1ecf1'},
            'AVAILABLE': {'color': '#28a745', 'icon': '✅', 'bg': '#d4edda'},
            'IN_PROCESS': {'color': '#ffc107', 'icon': '⚙️', 'bg': '#fff3cd'},
            'EXHAUSTED': {'color': '#6c757d', 'icon': '🔳', 'bg': '#e2e3e5'},
            'CONTAMINATED': {'color': '#dc3545', 'icon': '⚠️', 'bg': '#f8d7da'},
            'ARCHIVED': {'color': '#495057', 'icon': '📦', 'bg': '#e9ecef'}
        }
        config = status_config.get(obj.status, {'color': '#000', 'icon': '❓', 'bg': '#fff'})
        return format_html(
            '<span style="background: {}; color: {}; padding: 3px 8px; border-radius: 12px; '
            'font-size: 11px; font-weight: 500; display: inline-block; min-width: 80px; '
            'text-align: center;">{} {}</span>',
            config['bg'], config['color'], config['icon'], obj.get_status_display()
        )
    status_badge.short_description = '📊 Status'
    status_badge.admin_order_field = 'status'
    
    def date_display(self, obj):
        from datetime import timedelta
        from django.utils import timezone
        now = timezone.localtime().date()
        created_date = obj.date_created
        if created_date == now:
            time_str = "Today"
            color = "#28a745"
        elif created_date >= now - timedelta(days=7):
            time_str = f"{(now - created_date).days} days ago"
            color = "#17a2b8"
        else:
            time_str = created_date.strftime("%Y-%m-%d")
            color = "#6c757d"
        return format_html(
            '<span style="color: {}; font-weight: 500;">{}</span><br>'
            '<small style="color: #6c757d;">{}</small>',
            color, time_str, created_date.strftime("%Y-%m-%d")
        )
    date_display.short_description = '📅 Created'
    date_display.admin_order_field = 'date_created'
    
    def created_by_display(self, obj):
        if obj.created_by:
            return format_html(
                '<span style="background: #e9ecef; padding: 2px 6px; border-radius: 3px; '
                'font-size: 11px;">👤 {}</span>',
                obj.created_by.get_full_name() or obj.created_by.username
            )
        return format_html('<span style="color: #6c757d;">—</span>')
    created_by_display.short_description = '👤 Created By'
    created_by_display.admin_order_field = 'created_by'
    
    def last_updated(self, obj):
        if hasattr(obj, 'updated_at') and obj.updated_at:
            return format_html(
                '<small style="color: #6c757d;">{}</small>',
                obj.updated_at.strftime("%m/%d %H:%M")
            )
        return format_html('<span style="color: #6c757d;">—</span>')
    last_updated.short_description = '🕐 Updated'
    last_updated.admin_order_field = 'updated_at'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(CrudeSample)
class CrudeSampleAdmin(SampleAdmin):
    list_display = ('sample_id_display', 'barcode_display', 'status_badge', 'subject_display', 'source_display',
                   'collection_display', 'aliquot_count_badge')
    list_filter = SampleAdmin.list_filter + ('sample_source',)
    search_fields = SampleAdmin.search_fields + ('subject_id', 'source_details')
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            _aliquot_count=Count('aliquots', distinct=True),
        )
        return queryset
    
    def subject_display(self, obj):
        if obj.subject_id:
            return format_html(
                '<span style="background: #e3f2fd; color: #1976d2; padding: 2px 6px; '
                'border-radius: 3px; font-family: monospace; font-size: 11px;">{}</span>',
                obj.subject_id
            )
        return format_html('<span style="color: #6c757d;">—</span>')
    subject_display.short_description = '🆔 Subject ID'
    subject_display.admin_order_field = 'subject_id'
    
    def source_display(self, obj):
        source_icons = {
            'BLOOD': '🩸',
            'STOOL': '💩',
            'TISSUE': '🧬',
            'SALIVA': '💧',
            'OTHER': '📝'
        }
        icon = source_icons.get(obj.sample_source.upper(), '📝')
        return format_html(
            '<span style="background: #f3e5f5; color: #7b1fa2; padding: 2px 6px; '
            'border-radius: 3px; font-size: 11px;">{} {}</span>',
            icon,
            obj.get_sample_source_display() if obj.sample_source else 'Unknown'
        )
    source_display.short_description = '🧪 Source'
    source_display.admin_order_field = 'sample_source'
    
    def collection_display(self, obj):
        if obj.collection_date:
            return format_html(
                '<span style="color: #795548; font-size: 11px;">{}</span>',
                obj.collection_date.strftime("%Y-%m-%d")
            )
        return format_html('<span style="color: #6c757d;">—</span>')
    collection_display.short_description = '📅 Collected'
    collection_display.admin_order_field = 'collection_date'
    
    def aliquot_count_badge(self, obj):
        count = obj._aliquot_count
        if count == 0:
            bg, color = ("#e2e3e5", "#6c757d")
        else:
            bg, color = ("#d4edda", "#28a745")
        return format_html(
            '<span style="background: {}; color: {}; padding: 2px 8px; border-radius: 10px; '
            'font-size: 11px; font-weight: 500;">{}</span>',
            bg, color, count
        )
    aliquot_count_badge.short_description = '🧪 Aliquots'
    aliquot_count_badge.admin_order_field = '_aliquot_count'
    
    fieldsets = (
        ('📋 Basic Information', {
            'fields': ('barcode', 'subject_id', 'date_created', 'collection_date', 'status'),
        }),
        ('🧪 Sample Source & Details', {
            'fields': ('sample_source', 'source_details'),
        }),
        ('🏪 Storage Location', {
            'fields': ('freezer_ID', 'container_type', 'box_ID', 'well_ID'),
            'classes': ('collapse',),
        }),
        ('📝 Notes & Comments', {
            'fields': ('notes',),
        }),
        ('🔍 System Metadata', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',),
        }),
    )


@admin.register(Aliquot)
class AliquotAdmin(SampleAdmin):
    list_display = ('sample_id_display', 'barcode_display', 'status_badge', 'parent_link', 'volume_display',
                   'concentration_display', 'extract_count_badge')
    list_filter = SampleAdmin.list_filter
    search_fields = SampleAdmin.search_fields
    autocomplete_fields = ('parent_barcode',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('parent_barcode').annotate(
            _extract_count=Count('extracts', distinct=True)
        )
    
    def extract_count_badge(self, obj):
        count = obj._extract_count
        if count == 0:
            bg, color, icon = ("#e2e3e5", "#6c757d", "🔬")
        else:
            bg, color, icon = ("#d4edda", "#28a745", "🧪")
        return format_html(
            '<span style="background: {}; color: {}; padding: 2px 8px; border-radius: 10px; '
            'font-size: 11px; font-weight: 500;">{} {}</span>',
            bg, color, icon, count
        )
    extract_count_badge.short_description = '🧪 Extracts'
    extract_count_badge.admin_order_field = '_extract_count'
    
    def parent_link(self, obj):
        if obj.parent_barcode:
            return format_html(
                '<a href="/admin/sampletracking/crudesample/{}/change/" '
                'style="background: #e8f5e8; color: #2e7d32; padding: 2px 6px; '
                'border-radius: 3px; text-decoration: none; font-size: 11px;">'
                '🔗 {}</a>',
                obj.parent_barcode.pk, obj.parent_barcode.barcode
            )
        return format_html('<span style="color: #6c757d;">—</span>')
    parent_link.short_description = '🔗 Parent Sample'
    
    def volume_display(self, obj):
        if obj.volume:
            return format_html(
                '<span style="font-family: monospace;">{} µL</span>',
                obj.volume
            )
        return format_html('<span style="color: #6c757d;">—</span>')
    volume_display.short_description = '💧 Volume'
    volume_display.admin_order_field = 'volume'
    
    def concentration_display(self, obj):
        if obj.concentration:
            return format_html(
                '<span style="font-family: monospace;">{} ng/µL</span>',
                obj.concentration
            )
        return format_html('<span style="color: #6c757d;">—</span>')
    concentration_display.short_description = '⚗️ Concentration'
    concentration_display.admin_order_field = 'concentration'
    
    fieldsets = (
        ('📋 Basic Information', {
            'fields': ('barcode', 'date_created', 'parent_barcode', 'status'),
        }),
        ('🧪 Sample Properties', {
            'fields': ('volume', 'concentration'),
        }),
        ('🏪 Storage Location', {
            'fields': ('freezer_ID', 'container_type', 'box_ID', 'well_ID'),
            'classes': ('collapse',),
        }),
        ('📝 Notes & Comments', {
            'fields': ('notes',),
        }),
        ('🔍 System Metadata', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',),
        }),
    )


@admin.register(Extract)
class ExtractAdmin(SampleAdmin):
    list_display = ('sample_id_display', 'barcode_display', 'status_badge', 'parent_link', 'extract_type_display',
                   'quality_display', 'library_count_badge')
    list_filter = SampleAdmin.list_filter + ('extract_type',)
    search_fields = SampleAdmin.search_fields + ('extraction_method', 'extraction_solvent')
    autocomplete_fields = ('parent',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('parent').annotate(
            _library_count=Count('libraries', distinct=True)
        )
    
    def library_count_badge(self, obj):
        count = obj._library_count
        if count == 0:
            bg, color, icon = ("#e2e3e5", "#6c757d", "📚")
        else:
            bg, color, icon = ("#d4edda", "#28a745", "📖")
        return format_html(
            '<span style="background: {}; color: {}; padding: 2px 8px; border-radius: 10px; '
            'font-size: 11px; font-weight: 500;">{} {}</span>',
            bg, color, icon, count
        )
    library_count_badge.short_description = '📚 Libraries'
    library_count_badge.admin_order_field = '_library_count'
    
    def parent_link(self, obj):
        if obj.parent:
            return format_html(
                '<a href="/admin/sampletracking/aliquot/{}/change/" '
                'style="background: #e8f5e8; color: #2e7d32; padding: 2px 6px; '
                'border-radius: 3px; text-decoration: none; font-size: 11px;">'
                '🔗 {}</a>',
                obj.parent.pk, obj.parent.barcode
            )
        return format_html('<span style="color: #6c757d;">—</span>')
    parent_link.short_description = '🔗 Parent Aliquot'
    
    def extract_type_display(self, obj):
        type_config = {
            'DNA': {'color': '#1976d2', 'bg': '#e3f2fd', 'icon': '🧬'},
            'RNA': {'color': '#7b1fa2', 'bg': '#f3e5f5', 'icon': '🧮'},
            'cfDNA': {'color': '#388e3c', 'bg': '#e8f5e8', 'icon': '💎'},
        }
        config = type_config.get(obj.extract_type, {'color': '#6c757d', 'bg': '#e2e3e5', 'icon': '🔬'})
        return format_html(
            '<span style="background: {}; color: {}; padding: 2px 6px; '
            'border-radius: 3px; font-size: 11px; font-weight: 500;">{} {}</span>',
            config['bg'], config['color'], config['icon'], obj.get_extract_type_display()
        )
    extract_type_display.short_description = '🔬 Extract Type'
    extract_type_display.admin_order_field = 'extract_type'
    
    def quality_display(self, obj):
        if obj.quality_score is not None:
            if obj.quality_score >= 1.8:
                bg, color, icon = ("#d4edda", "#28a745", "🟢")
            else:
                bg, color, icon = ("#f8d7da", "#dc3545", "🔴")
            return format_html(
                '<span style="background: {}; color: {}; padding: 2px 6px; '
                'border-radius: 3px; font-size: 11px; font-weight: 500;">{} {}</span>',
                bg, color, icon, obj.quality_score
            )
        return format_html('<span style="color: #6c757d;">—</span>')
    quality_display.short_description = '📊 Quality'
    quality_display.admin_order_field = 'quality_score'
    
    fieldsets = (
        ('📋 Basic Information', {
            'fields': ('barcode', 'date_created', 'parent', 'extract_type', 'status'),
        }),
        ('🧬 DNA/RNA Extract Details', {
            'fields': ('extraction_method', 'quality_score', 'concentration'),
            'classes': ('collapse',),
        }),
        ('⚗️ Metabolomics/Antimicrobials Extract Details', {
            'fields': ('sample_weight', 'extraction_solvent', 'solvent_volume', 'extract_volume'),
            'classes': ('collapse',),
        }),
        ('🏪 Storage Location', {
            'fields': ('freezer_ID', 'container_type', 'box_ID', 'well_ID'),
            'classes': ('collapse',),
        }),
        ('📝 Notes & Comments', {
            'fields': ('notes',),
        }),
        ('🔍 System Metadata', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',),
        }),
    )


@admin.register(SequenceLibrary)
class SequenceLibraryAdmin(SampleAdmin):
    list_display = ('sample_id_display', 'barcode_display', 'status_badge', 'parent_link', 'library_type_display',
                   'plate_well_display', 'sequencing_status_badge')
    list_filter = SampleAdmin.list_filter + ('library_type', 'date_sequenced')
    search_fields = SampleAdmin.search_fields + ('sequencing_run_id', 'sequencing_platform', 'well')
    autocomplete_fields = ('parent', 'plate')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('parent', 'plate')
    
    def sequencing_status_badge(self, obj):
        if obj.date_sequenced:
            return format_html('<span style="background: #d4edda; color: #28a745; padding: 3px 8px; border-radius: 12px; font-size: 11px; font-weight: 500;">✅ Sequenced</span>')
        return format_html('<span style="background: #e2e3e5; color: #6c757d; padding: 3px 8px; border-radius: 12px; font-size: 11px; font-weight: 500;">⏳ Pending</span>')
    sequencing_status_badge.short_description = '📊 Sequencing'
    
    def parent_link(self, obj):
        if obj.parent:
            return format_html(
                '<a href="/admin/sampletracking/extract/{}/change/">{}</a>',
                obj.parent.pk, obj.parent.barcode
            )
        return "-"
    parent_link.short_description = '🔗 Parent Extract'
    
    def library_type_display(self, obj):
        return obj.get_library_type_display()
    library_type_display.short_description = '📚 Library Type'
    
    def plate_well_display(self, obj):
        if obj.plate and obj.well:
            return f"{obj.plate.barcode}:{obj.well}"
        return "-"
    plate_well_display.short_description = '🧪 Plate:Well'
    
    fieldsets = (
        ('📋 Basic Information', {
            'fields': ('barcode', 'date_created', 'parent', 'library_type', 'status'),
        }),
        ('🧬 Indexing Information', {
            'fields': ('nindex', 'sindex'),
        }),
        ('📊 Quality Control', {
            'fields': ('qubit_conc', 'diluted_qubit_conc', 'clean_library_conc'),
        }),
        ('🔬 Sequencing Information', {
            'fields': ('date_sequenced', 'sequencing_platform', 'sequencing_run_id'),
        }),
        ('🧪 Plate Information', {
            'fields': ('plate', 'well'),
        }),
        ('🏪 Storage Location', {
            'fields': ('freezer_ID', 'container_type', 'box_ID', 'well_ID'),
            'classes': ('collapse',),
        }),
        ('📝 Notes & Comments', {
            'fields': ('notes',),
        }),
        ('🔍 System Metadata', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',),
        }),
    )


@admin.register(Plate)
class PlateAdmin(admin.ModelAdmin):
    list_display = ('barcode_display', 'plate_type_display', 'library_count_badge', 
                   'date_display', 'created_by_display')
    list_filter = ('plate_type', 'created_at', 'created_by')
    search_fields = ('barcode', 'notes')
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')
    date_hierarchy = 'created_at'
    list_per_page = 25
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _library_count=Count('libraries', distinct=True)
        )
    
    def barcode_display(self, obj):
        return format_html('<code>{}</code>', obj.barcode)
    barcode_display.short_description = '🏷️ Plate Barcode'
    
    def plate_type_display(self, obj):
        return obj.get_plate_type_display()
    plate_type_display.short_description = '🧪 Plate Type'
    
    def library_count_badge(self, obj):
        count = obj._library_count
        return format_html('<span style="background: #d1ecf1; color: #17a2b8; padding: 3px 8px; border-radius: 12px; font-size: 11px; font-weight: 500;">{}</span>', count)
    library_count_badge.short_description = '📚 Libraries'
    
    def date_display(self, obj):
        return obj.created_at.strftime("%Y-%m-%d")
    date_display.short_description = '📅 Created'
    
    def created_by_display(self, obj):
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.username
        return "-"
    created_by_display.short_description = '👤 Created By'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    fieldsets = (
        ('📋 Basic Information', {
            'fields': ('barcode', 'plate_type'),
        }),
        ('🏪 Storage Location', {
            'fields': ('freezer_ID', 'container_type', 'box_ID', 'well_ID'),
        }),
        ('📝 Notes & Comments', {
            'fields': ('notes',),
        }),
        ('🔍 System Metadata', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',),
        }),
    )