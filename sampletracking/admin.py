from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from django.utils.safestring import mark_safe
from .models import CrudeSample, Aliquot, Extract, SequenceLibrary, Plate

# Customize admin site header and title
admin.site.site_header = "MGML Sample Database Administration"
admin.site.site_title = "MGML Admin"
admin.site.index_title = "Sample Management Dashboard"


@admin.action(description="Mark selected samples as archived")
def mark_archived(modeladmin, request, queryset):
    queryset.update(status='ARCHIVED')


class SampleAdmin(admin.ModelAdmin):
    """
    Base admin configuration for all sample types
    """
    list_display = ('barcode', 'colored_status', 'date_created', 'created_by', 'updated_at')
    list_filter = ('status', 'date_created', 'created_by')
    search_fields = ('barcode', 'notes')
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')
    date_hierarchy = 'date_created'
    actions = [mark_archived]
    
    def colored_status(self, obj):
        """Display status with color coding."""
        colors = {
            'AWAITING_RECEIPT': '#17a2b8',
            'AVAILABLE': '#28a745',
            'IN_PROCESS': '#ffc107',
            'EXHAUSTED': '#6c757d',
            'CONTAMINATED': '#dc3545',
            'ARCHIVED': '#495057'
        }
        return format_html(
            '<span style="color: {}; font-weight: 500;">{}</span>',
            colors.get(obj.status, '#000'),
            obj.get_status_display()
        )
    colored_status.short_description = 'Status'
    colored_status.admin_order_field = 'status'
    
    def save_model(self, request, obj, form, change):
        """
        Track the user who creates or updates a sample
        """
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(CrudeSample)
class CrudeSampleAdmin(SampleAdmin):
    """
    Admin configuration for crude samples
    """
    list_display = SampleAdmin.list_display + ('your_id', 'sample_source', 'collection_date', 'aliquot_count')
    list_filter = SampleAdmin.list_filter + ('sample_source',)
    search_fields = SampleAdmin.search_fields + ('your_id', 'source_details')
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            _aliquot_count=Count('aliquots', distinct=True),
        )
        return queryset
    
    def aliquot_count(self, obj):
        return obj._aliquot_count
    aliquot_count.short_description = 'Aliquots'
    aliquot_count.admin_order_field = '_aliquot_count'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('barcode', 'your_id', 'date_created', 'collection_date', 'status')
        }),
        ('Source Information', {
            'fields': ('sample_source', 'source_details')
        }),
        ('Storage Location', {
            'fields': ('freezer_ID', 'shelf_ID', 'box_ID')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Aliquot)
class AliquotAdmin(SampleAdmin):
    """
    Admin configuration for aliquots
    """
    list_display = SampleAdmin.list_display + ('parent_link', 'volume', 'concentration', 'extract_count')
    list_filter = SampleAdmin.list_filter
    search_fields = SampleAdmin.search_fields
    autocomplete_fields = ('parent_barcode',)
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            _extract_count=Count('extracts', distinct=True),
        )
        return queryset
    
    def extract_count(self, obj):
        return obj._extract_count
    extract_count.short_description = 'Extracts'
    extract_count.admin_order_field = '_extract_count'
    
    def parent_link(self, obj):
        if obj.parent_barcode:
            url = f"/admin/sampletracking/crudesample/{obj.parent_barcode.pk}/change/"
            return format_html('<a href="{}">{}</a>', url, obj.parent_barcode.barcode)
        return "-"
    parent_link.short_description = 'Parent Sample'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('barcode', 'date_created', 'parent_barcode', 'status')
        }),
        ('Properties', {
            'fields': ('volume', 'concentration')
        }),
        ('Storage Location', {
            'fields': ('freezer_ID', 'shelf_ID', 'box_ID')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Extract)
class ExtractAdmin(SampleAdmin):
    """
    Admin configuration for extracts
    """
    list_display = SampleAdmin.list_display + ('parent_link', 'extract_type', 'quality_score', 'library_count')
    list_filter = SampleAdmin.list_filter + ('extract_type',)
    search_fields = SampleAdmin.search_fields + ('protocol_used',)
    autocomplete_fields = ('parent',)
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            _library_count=Count('libraries', distinct=True),
        )
        return queryset
    
    def library_count(self, obj):
        return obj._library_count
    library_count.short_description = 'Libraries'
    library_count.admin_order_field = '_library_count'
    
    def parent_link(self, obj):
        if obj.parent:
            url = f"/admin/sampletracking/aliquot/{obj.parent.pk}/change/"
            return format_html('<a href="{}">{}</a>', url, obj.parent.barcode)
        return "-"
    parent_link.short_description = 'Parent Aliquot'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('barcode', 'date_created', 'parent', 'extract_type', 'status')
        }),
        ('Properties', {
            'fields': ('protocol_used', 'quality_score')
        }),
        ('Storage Location', {
            'fields': ('freezer_ID', 'shelf_ID', 'box_ID')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SequenceLibrary)
class SequenceLibraryAdmin(SampleAdmin):
    """
    Admin configuration for sequence libraries
    """
    list_display = SampleAdmin.list_display + ('parent_link', 'library_type', 'plate_well', 'sequencing_status')
    list_filter = SampleAdmin.list_filter + ('library_type', 'date_sequenced')
    search_fields = SampleAdmin.search_fields + ('sequencing_run_id', 'sequencing_platform', 'well')
    autocomplete_fields = ('parent', 'plate')
    
    def sequencing_status(self, obj):
        if obj.date_sequenced:
            return format_html('<span style="color: green;">Sequenced</span>')
        return format_html('<span style="color: red;">Pending</span>')
    sequencing_status.short_description = 'Status'
    
    def parent_link(self, obj):
        if obj.parent:
            url = f"/admin/sampletracking/extract/{obj.parent.pk}/change/"
            return format_html('<a href="{}">{}</a>', url, obj.parent.barcode)
        return "-"
    parent_link.short_description = 'Parent Extract'
    
    def plate_well(self, obj):
        if obj.plate and obj.well:
            return f"{obj.plate.barcode}: {obj.well}"
        return "-"
    plate_well.short_description = 'Plate:Well'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('barcode', 'date_created', 'parent', 'library_type', 'status')
        }),
        ('Indexing', {
            'fields': ('nindex', 'sindex')
        }),
        ('Quality Control', {
            'fields': ('qubit_conc', 'diluted_qubit_conc', 'clean_library_conc')
        }),
        ('Sequencing', {
            'fields': ('date_sequenced', 'sequencing_platform', 'sequencing_run_id')
        }),
        ('Plate Information', {
            'fields': ('plate', 'well')
        }),
        ('Storage Location', {
            'fields': ('freezer_ID', 'shelf_ID', 'box_ID')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Plate)
class PlateAdmin(admin.ModelAdmin):
    """
    Admin configuration for plates
    """
    list_display = ('barcode', 'plate_type', 'library_count', 'created_at', 'created_by')
    list_filter = ('plate_type', 'created_at', 'created_by')
    search_fields = ('barcode', 'notes')
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')
    date_hierarchy = 'created_at'
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            _library_count=Count('libraries', distinct=True),
        )
        return queryset
    
    def library_count(self, obj):
        return obj._library_count
    library_count.short_description = 'Libraries'
    library_count.admin_order_field = '_library_count'
    
    def save_model(self, request, obj, form, change):
        """
        Track the user who creates or updates a plate
        """
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('barcode', 'plate_type')
        }),
        ('Storage Location', {
            'fields': ('freezer_ID', 'shelf_ID', 'box_ID')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )