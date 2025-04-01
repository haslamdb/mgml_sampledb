from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from .models import CrudeSample, Aliquot, Extract, SequenceLibrary


@admin.action(description="Mark selected samples as archived")
def mark_archived(modeladmin, request, queryset):
    queryset.update(notes=f"ARCHIVED: {queryset.first().notes}" if queryset.first().notes else "ARCHIVED")


class SampleAdmin(admin.ModelAdmin):
    """
    Base admin configuration for all sample types
    """
    list_display = ('barcode', 'date_created', 'created_by', 'updated_at')
    list_filter = ('date_created', 'created_by')
    search_fields = ('barcode', 'notes')
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')
    date_hierarchy = 'date_created'
    actions = [mark_archived]
    
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
            'fields': ('barcode', 'your_id', 'date_created', 'collection_date')
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
            'fields': ('barcode', 'date_created', 'parent_barcode')
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
            'fields': ('barcode', 'date_created', 'parent', 'extract_type')
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
    list_display = SampleAdmin.list_display + ('parent_link', 'library_type', 'sequencing_status')
    list_filter = SampleAdmin.list_filter + ('library_type', 'date_sequenced')
    search_fields = SampleAdmin.search_fields + ('sequencing_run_id', 'sequencing_platform')
    autocomplete_fields = ('parent',)
    
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
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('barcode', 'date_created', 'parent', 'library_type')
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
