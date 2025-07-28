from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Q
from django.utils.safestring import mark_safe
from .models import CrudeSample, Aliquot, Extract, SequenceLibrary, Plate

# Customize admin site header and title with better styling
admin.site.site_header = "🧬 MGML Sample Database Administration"
admin.site.site_title = "MGML Sample DB"
admin.site.index_title = "📊 Laboratory Sample Management Dashboard"

# Enable modern sidebar navigation
admin.site.enable_nav_sidebar = True


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
        from datetime import datetime, timedelta
        now = datetime.now()
        
        if self.value() == 'today':
            return queryset.filter(date_created__date=now.date())
        elif self.value() == 'week':
            start_week = now - timedelta(days=7)
            return queryset.filter(date_created__gte=start_week)
        elif self.value() == 'month':
            start_month = now - timedelta(days=30)
            return queryset.filter(date_created__gte=start_month)
        elif self.value() == 'quarter':
            start_quarter = now - timedelta(days=90)
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
    list_display = ('barcode_display', 'status_badge', 'date_display', 'created_by_display', 'last_updated')
    list_filter = (StatusFilter, RecentSamplesFilter, 'created_by')
    search_fields = ('barcode', 'notes')
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')
    date_hierarchy = 'date_created'
    actions = [mark_archived, mark_available, mark_contaminated]
    list_per_page = 25
    list_max_show_all = 100
    
    # Enhanced styling and organization
    class Media:
        css = {
            'all': ('admin/css/custom_admin.css',)
        }
        js = ('admin/js/admin_enhancements.js',)
    
    def get_form(self, request, obj=None, **kwargs):
        """Override to add our custom CSS class to forms"""
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['barcode'].widget.attrs.update({
            'class': 'custom-barcode-field',
            'placeholder': 'Enter barcode...'
        })
        return form
    
    def barcode_display(self, obj):
        """Enhanced barcode display with copy functionality"""
        return format_html(
            '<code style="background: #f8f9fa; padding: 2px 6px; border-radius: 3px; '
            'font-family: monospace; font-size: 12px; border: 1px solid #dee2e6;" '
            'title="Click to copy">{}</code>',
            obj.barcode
        )
    barcode_display.short_description = '🏷️ Barcode'
    barcode_display.admin_order_field = 'barcode'
    
    def status_badge(self, obj):
        """Enhanced status display with icons and colors"""
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
            config['bg'],
            config['color'],
            config['icon'],
            obj.get_status_display()
        )
    status_badge.short_description = '📊 Status'
    status_badge.admin_order_field = 'status'
    
    def date_display(self, obj):
        """Enhanced date display with relative time"""
        from datetime import datetime, timedelta
        now = datetime.now().date()
        created_date = obj.date_created
        
        if created_date == now:
            time_str = "Today"
            color = "#28a745"
        elif created_date >= now - timedelta(days=7):
            time_str = f"{(now - created_date).days} days ago"
            color = "#17a2b8"
        elif created_date >= now - timedelta(days=30):
            time_str = f"{(now - created_date).days} days ago"
            color = "#ffc107"
        else:
            time_str = created_date.strftime("%Y-%m-%d")
            color = "#6c757d"
            
        return format_html(
            '<span style="color: {}; font-weight: 500;">{}</span><br>'
            '<small style="color: #6c757d;">{}</small>',
            color,
            time_str,
            created_date.strftime("%Y-%m-%d")
        )
    date_display.short_description = '📅 Created'
    date_display.admin_order_field = 'date_created'
    
    def created_by_display(self, obj):
        """Enhanced user display"""
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
        """Show last update time"""
        if hasattr(obj, 'updated_at') and obj.updated_at:
            return format_html(
                '<small style="color: #6c757d;">{}</small>',
                obj.updated_at.strftime("%m/%d %H:%M")
            )
        return format_html('<span style="color: #6c757d;">—</span>')
    last_updated.short_description = '🕐 Updated'
    last_updated.admin_order_field = 'updated_at'
    
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
    Enhanced admin configuration for crude samples with improved formatting
    """
    list_display = ('barcode_display', 'status_badge', 'subject_display', 'source_display', 
                   'collection_display', 'aliquot_count_badge', 'override_indicator')
    list_filter = SampleAdmin.list_filter + ('sample_source', 'barcode_override_used')
    search_fields = SampleAdmin.search_fields + ('subject_id', 'source_details')
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            _aliquot_count=Count('aliquots', distinct=True),
        )
        return queryset
    
    def subject_display(self, obj):
        """Enhanced subject ID display"""
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
        """Enhanced sample source display"""
        source_icons = {
            'BLOOD': '🩸',
            'URINE': '💧',
            'FECES': '💩',
            'TISSUE': '🧬',
            'SALIVA': '💧',
            'OTHER': '📝'
        }
        icon = source_icons.get(obj.sample_source, '📝')
        return format_html(
            '<span style="background: #f3e5f5; color: #7b1fa2; padding: 2px 6px; '
            'border-radius: 3px; font-size: 11px;">{} {}</span>',
            icon,
            obj.get_sample_source_display() if obj.sample_source else 'Unknown'
        )
    source_display.short_description = '🧪 Source'
    source_display.admin_order_field = 'sample_source'
    
    def collection_display(self, obj):
        """Enhanced collection date display"""
        if obj.collection_date:
            return format_html(
                '<span style="color: #795548; font-size: 11px;">{}</span>',
                obj.collection_date.strftime("%Y-%m-%d")
            )
        return format_html('<span style="color: #6c757d;">—</span>')
    collection_display.short_description = '📅 Collected'
    collection_display.admin_order_field = 'collection_date'
    
    def aliquot_count_badge(self, obj):
        """Enhanced aliquot count display with badge"""
        count = obj._aliquot_count
        if count == 0:
            color = "#6c757d"
            bg = "#e2e3e5"
        elif count <= 3:
            color = "#28a745"
            bg = "#d4edda"
        elif count <= 10:
            color = "#ffc107"
            bg = "#fff3cd"
        else:
            color = "#17a2b8"
            bg = "#d1ecf1"
            
        return format_html(
            '<span style="background: {}; color: {}; padding: 2px 8px; border-radius: 10px; '
            'font-size: 11px; font-weight: 500; min-width: 30px; text-align: center; '
            'display: inline-block;">🧪 {}</span>',
            bg, color, count
        )
    aliquot_count_badge.short_description = '🧪 Aliquots'
    aliquot_count_badge.admin_order_field = '_aliquot_count'
    
    def override_indicator(self, obj):
        """Enhanced override indicator"""
        if obj.barcode_override_used:
            return format_html(
                '<span style="background: #fff3cd; color: #856404; padding: 2px 6px; '
                'border-radius: 3px; font-size: 10px; font-weight: 500;" '
                'title="Barcode validation was overridden">⚠️ Override</span>'
            )
        return format_html('<span style="color: #28a745; font-size: 10px;">✓</span>')
    override_indicator.short_description = '⚠️ Override'
    override_indicator.admin_order_field = 'barcode_override_used'
    
    fieldsets = (
        ('📋 Basic Information', {
            'fields': ('barcode', 'subject_id', 'date_created', 'collection_date', 'status'),
            'classes': ('wide',),
            'description': 'Core sample identification and status information'
        }),
        ('🧪 Sample Source & Details', {
            'fields': ('sample_source', 'source_details'),
            'classes': ('wide',),
            'description': 'Information about the sample origin and collection details'
        }),
        ('🏪 Storage Location', {
            'fields': ('freezer_ID', 'rack_ID', 'container_type', 'box_ID', 'well_ID'),
            'classes': ('collapse', 'wide'),
            'description': 'Physical storage location in the laboratory'
        }),
        ('📝 Notes & Comments', {
            'fields': ('notes',),
            'classes': ('wide',),
            'description': 'Additional notes and observations about this sample'
        }),
        ('🔍 System Metadata', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by', 'barcode_override_used'),
            'classes': ('collapse', 'wide'),
            'description': 'System-generated tracking information'
        }),
    )


@admin.register(Aliquot)
class AliquotAdmin(SampleAdmin):
    """
    Enhanced admin configuration for aliquots with improved formatting
    """
    list_display = ('barcode_display', 'status_badge', 'parent_link', 'volume_display', 
                   'concentration_display', 'extract_count_badge')
    list_filter = SampleAdmin.list_filter
    search_fields = SampleAdmin.search_fields
    autocomplete_fields = ('parent_barcode',)
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('parent_barcode').annotate(
            _extract_count=Count('extracts', distinct=True),
        )
        return queryset
    
    def extract_count_badge(self, obj):
        """Enhanced extract count display with badge"""
        count = obj._extract_count
        if count == 0:
            color = "#6c757d"
            bg = "#e2e3e5"
            icon = "🔬"
        elif count <= 2:
            color = "#28a745"
            bg = "#d4edda"
            icon = "🧪"
        else:
            color = "#17a2b8"
            bg = "#d1ecf1"
            icon = "⚗️"
            
        return format_html(
            '<span style="background: {}; color: {}; padding: 2px 8px; border-radius: 10px; '
            'font-size: 11px; font-weight: 500; min-width: 30px; text-align: center; '
            'display: inline-block;">{} {}</span>',
            bg, color, icon, count
        )
    extract_count_badge.short_description = '🧪 Extracts'
    extract_count_badge.admin_order_field = '_extract_count'
    
    def parent_link(self, obj):
        """Enhanced parent sample link"""
        if obj.parent_barcode:
            return format_html(
                '<a href="/admin/sampletracking/crudesample/{}/change/" '
                'style="background: #e8f5e8; color: #2e7d32; padding: 2px 6px; '
                'border-radius: 3px; text-decoration: none; font-size: 11px;">'
                '🔗 {}</a>',
                obj.parent_barcode.pk,
                obj.parent_barcode.barcode
            )
        return format_html('<span style="color: #6c757d;">—</span>')
    parent_link.short_description = '🔗 Parent Sample'
    
    def volume_display(self, obj):
        """Enhanced volume display"""
        if obj.volume:
            return format_html(
                '<span style="background: #e1f5fe; color: #0277bd; padding: 2px 6px; '
                'border-radius: 3px; font-size: 11px; font-family: monospace;">{} mL</span>',
                obj.volume
            )
        return format_html('<span style="color: #6c757d;">—</span>')
    volume_display.short_description = '💧 Volume'
    volume_display.admin_order_field = 'volume'
    
    def concentration_display(self, obj):
        """Enhanced concentration display"""
        if obj.concentration:
            return format_html(
                '<span style="background: #fce4ec; color: #c2185b; padding: 2px 6px; '
                'border-radius: 3px; font-size: 11px; font-family: monospace;">{}</span>',
                obj.concentration
            )
        return format_html('<span style="color: #6c757d;">—</span>')
    concentration_display.short_description = '⚗️ Concentration'
    concentration_display.admin_order_field = 'concentration'
    
    fieldsets = (
        ('📋 Basic Information', {
            'fields': ('barcode', 'date_created', 'parent_barcode', 'status'),
            'classes': ('wide',),
            'description': 'Core aliquot identification and parent sample relationship'
        }),
        ('🧪 Sample Properties', {
            'fields': ('volume', 'concentration'),
            'classes': ('wide',),
            'description': 'Physical and chemical properties of the aliquot'
        }),
        ('🏪 Storage Location', {
            'fields': ('freezer_ID', 'rack_ID', 'container_type', 'box_ID', 'well_ID'),
            'classes': ('collapse', 'wide'),
            'description': 'Physical storage location in the laboratory'
        }),
        ('📝 Notes & Comments', {
            'fields': ('notes',),
            'classes': ('wide',),
            'description': 'Additional notes and observations about this aliquot'
        }),
        ('🔍 System Metadata', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse', 'wide'),
            'description': 'System-generated tracking information'
        }),
    )


@admin.register(Extract)
class ExtractAdmin(SampleAdmin):
    """
    Enhanced admin configuration for extracts with improved formatting
    """
    list_display = ('barcode_display', 'status_badge', 'parent_link', 'extract_type_display', 
                   'quality_display', 'library_count_badge')
    list_filter = SampleAdmin.list_filter + ('extract_type',)
    search_fields = SampleAdmin.search_fields + ('protocol_used', 'extraction_method', 'extraction_solvent')
    autocomplete_fields = ('parent',)
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('parent').annotate(
            _library_count=Count('libraries', distinct=True),
        )
        return queryset
    
    def library_count_badge(self, obj):
        """Enhanced library count display with badge"""
        count = obj._library_count
        if count == 0:
            color = "#6c757d"
            bg = "#e2e3e5"
            icon = "📚"
        elif count <= 2:
            color = "#28a745"
            bg = "#d4edda"
            icon = "📖"
        else:
            color = "#17a2b8"
            bg = "#d1ecf1"
            icon = "📗"
            
        return format_html(
            '<span style="background: {}; color: {}; padding: 2px 8px; border-radius: 10px; '
            'font-size: 11px; font-weight: 500; min-width: 30px; text-align: center; '
            'display: inline-block;">{} {}</span>',
            bg, color, icon, count
        )
    library_count_badge.short_description = '📚 Libraries'
    library_count_badge.admin_order_field = '_library_count'
    
    def parent_link(self, obj):
        """Enhanced parent aliquot link"""
        if obj.parent:
            return format_html(
                '<a href="/admin/sampletracking/aliquot/{}/change/" '
                'style="background: #e8f5e8; color: #2e7d32; padding: 2px 6px; '
                'border-radius: 3px; text-decoration: none; font-size: 11px;">'
                '🔗 {}</a>',
                obj.parent.pk,
                obj.parent.barcode
            )
        return format_html('<span style="color: #6c757d;">—</span>')
    parent_link.short_description = '🔗 Parent Aliquot'
    
    def extract_type_display(self, obj):
        """Enhanced extract type display"""
        type_config = {
            'DNA': {'color': '#1976d2', 'bg': '#e3f2fd', 'icon': '🧬'},
            'RNA': {'color': '#7b1fa2', 'bg': '#f3e5f5', 'icon': '🧮'},
            'cfDNA': {'color': '#388e3c', 'bg': '#e8f5e8', 'icon': '💎'},
            'METABOLOMICS': {'color': '#f57c00', 'bg': '#fff3e0', 'icon': '⚗️'},
            'ANTIMICROBIALS': {'color': '#d32f2f', 'bg': '#ffebee', 'icon': '💊'},
        }
        
        config = type_config.get(obj.extract_type, {'color': '#6c757d', 'bg': '#e2e3e5', 'icon': '🔬'})
        
        return format_html(
            '<span style="background: {}; color: {}; padding: 2px 6px; '
            'border-radius: 3px; font-size: 11px; font-weight: 500;">{} {}</span>',
            config['bg'],
            config['color'],
            config['icon'],
            obj.get_extract_type_display() if obj.extract_type else 'Unknown'
        )
    extract_type_display.short_description = '🔬 Extract Type'
    extract_type_display.admin_order_field = 'extract_type'
    
    def quality_display(self, obj):
        """Enhanced quality score display"""
        if obj.quality_score is not None:
            if obj.quality_score >= 80:
                color = "#28a745"
                bg = "#d4edda"
                icon = "🟢"
            elif obj.quality_score >= 60:
                color = "#ffc107"
                bg = "#fff3cd"
                icon = "🟡"
            else:
                color = "#dc3545"
                bg = "#f8d7da"
                icon = "🔴"
                
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
            'classes': ('wide',),
            'description': 'Core extract identification and type information'
        }),
        ('🧬 DNA/RNA Extract Details', {
            'fields': ('extraction_method', 'protocol_used', 'quality_score'),
            'classes': ('collapse', 'wide'),
            'description': 'Fields specific to DNA, RNA, and cfDNA extracts'
        }),
        ('⚗️ Metabolomics/Antimicrobials Extract Details', {
            'fields': ('sample_weight', 'extraction_solvent', 'solvent_volume', 'extract_volume'),
            'classes': ('collapse', 'wide'),
            'description': 'Fields specific to Metabolomics and Antimicrobials extracts'
        }),
        ('🏪 Storage Location', {
            'fields': ('freezer_ID', 'rack_ID', 'container_type', 'box_ID', 'well_ID'),
            'classes': ('collapse', 'wide'),
            'description': 'Physical storage location in the laboratory'
        }),
        ('📝 Notes & Comments', {
            'fields': ('notes',),
            'classes': ('wide',),
            'description': 'Additional notes and observations about this extract'
        }),
        ('🔍 System Metadata', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse', 'wide'),
            'description': 'System-generated tracking information'
        }),
    )


@admin.register(SequenceLibrary)
class SequenceLibraryAdmin(SampleAdmin):
    """
    Enhanced admin configuration for sequence libraries with improved formatting
    """
    list_display = ('barcode_display', 'status_badge', 'parent_link', 'library_type_display', 
                   'plate_well_display', 'sequencing_status_badge')
    list_filter = SampleAdmin.list_filter + ('library_type', 'date_sequenced')
    search_fields = SampleAdmin.search_fields + ('sequencing_run_id', 'sequencing_platform', 'well')
    autocomplete_fields = ('parent', 'plate')
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('parent', 'plate')
        return queryset
    
    def sequencing_status_badge(self, obj):
        """Enhanced sequencing status display"""
        if obj.date_sequenced:
            return format_html(
                '<span style="background: #d4edda; color: #28a745; padding: 2px 8px; '
                'border-radius: 10px; font-size: 11px; font-weight: 500;">'
                '✅ Sequenced</span>'
            )
        return format_html(
            '<span style="background: #fff3cd; color: #856404; padding: 2px 8px; '
            'border-radius: 10px; font-size: 11px; font-weight: 500;">'
            '⏳ Pending</span>'
        )
    sequencing_status_badge.short_description = '📊 Sequencing'
    
    def parent_link(self, obj):
        """Enhanced parent extract link"""
        if obj.parent:
            return format_html(
                '<a href="/admin/sampletracking/extract/{}/change/" '
                'style="background: #e8f5e8; color: #2e7d32; padding: 2px 6px; '
                'border-radius: 3px; text-decoration: none; font-size: 11px;">'
                '🔗 {}</a>',
                obj.parent.pk,
                obj.parent.barcode
            )
        return format_html('<span style="color: #6c757d;">—</span>')
    parent_link.short_description = '🔗 Parent Extract'
    
    def library_type_display(self, obj):
        """Enhanced library type display"""
        type_config = {
            'WGS': {'color': '#1976d2', 'bg': '#e3f2fd', 'icon': '🌐'},
            'RNA_SEQ': {'color': '#7b1fa2', 'bg': '#f3e5f5', 'icon': '🧮'},
            'AMPLICON': {'color': '#388e3c', 'bg': '#e8f5e8', 'icon': '🎯'},
            'METAGENOMICS': {'color': '#f57c00', 'bg': '#fff3e0', 'icon': '🦠'},
        }
        
        config = type_config.get(obj.library_type, {'color': '#6c757d', 'bg': '#e2e3e5', 'icon': '📚'})
        
        return format_html(
            '<span style="background: {}; color: {}; padding: 2px 6px; '
            'border-radius: 3px; font-size: 11px; font-weight: 500;">{} {}</span>',
            config['bg'],
            config['color'],
            config['icon'],
            obj.get_library_type_display() if obj.library_type else 'Unknown'
        )
    library_type_display.short_description = '📚 Library Type'
    library_type_display.admin_order_field = 'library_type'
    
    def plate_well_display(self, obj):
        """Enhanced plate and well display"""
        if obj.plate and obj.well:
            return format_html(
                '<span style="background: #e1f5fe; color: #0277bd; padding: 2px 6px; '
                'border-radius: 3px; font-size: 11px; font-family: monospace;">'
                '🧪 {}:{}</span>',
                obj.plate.barcode,
                obj.well
            )
        return format_html('<span style="color: #6c757d;">—</span>')
    plate_well_display.short_description = '🧪 Plate:Well'
    
    fieldsets = (
        ('📋 Basic Information', {
            'fields': ('barcode', 'date_created', 'parent', 'library_type', 'status'),
            'classes': ('wide',),
            'description': 'Core library identification and type information'
        }),
        ('🧬 Indexing Information', {
            'fields': ('nindex', 'sindex'),
            'classes': ('wide',),
            'description': 'Sequencing indexes for multiplexing'
        }),
        ('📊 Quality Control', {
            'fields': ('qubit_conc', 'diluted_qubit_conc', 'clean_library_conc'),
            'classes': ('wide',),
            'description': 'Concentration measurements and quality metrics'
        }),
        ('🔬 Sequencing Information', {
            'fields': ('date_sequenced', 'sequencing_platform', 'sequencing_run_id'),
            'classes': ('wide',),
            'description': 'Sequencing run details and platform information'
        }),
        ('🧪 Plate Information', {
            'fields': ('plate', 'well'),
            'classes': ('wide',),
            'description': 'Physical plate location information'
        }),
        ('🏪 Storage Location', {
            'fields': ('freezer_ID', 'rack_ID', 'container_type', 'box_ID', 'well_ID'),
            'classes': ('collapse', 'wide'),
            'description': 'Physical storage location in the laboratory'
        }),
        ('📝 Notes & Comments', {
            'fields': ('notes',),
            'classes': ('wide',),
            'description': 'Additional notes and observations about this library'
        }),
        ('🔍 System Metadata', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse', 'wide'),
            'description': 'System-generated tracking information'
        }),
    )


@admin.register(Plate)
class PlateAdmin(admin.ModelAdmin):
    """
    Enhanced admin configuration for plates with improved formatting
    """
    list_display = ('barcode_display', 'plate_type_display', 'library_count_badge', 
                   'date_display', 'created_by_display')
    list_filter = ('plate_type', 'created_at', 'created_by')
    search_fields = ('barcode', 'notes')
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')
    date_hierarchy = 'created_at'
    list_per_page = 25
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            _library_count=Count('libraries', distinct=True),
        )
        return queryset
    
    def barcode_display(self, obj):
        """Enhanced barcode display"""
        return format_html(
            '<code style="background: #f8f9fa; padding: 2px 6px; border-radius: 3px; '
            'font-family: monospace; font-size: 12px; border: 1px solid #dee2e6;">{}</code>',
            obj.barcode
        )
    barcode_display.short_description = '🏷️ Plate Barcode'
    barcode_display.admin_order_field = 'barcode'
    
    def plate_type_display(self, obj):
        """Enhanced plate type display"""
        type_config = {
            'PCR_PLATE': {'color': '#1976d2', 'bg': '#e3f2fd', 'icon': '🧪'},
            'DEEP_WELL': {'color': '#388e3c', 'bg': '#e8f5e8', 'icon': '🕳️'},
            'STORAGE': {'color': '#7b1fa2', 'bg': '#f3e5f5', 'icon': '📦'},
        }
        
        config = type_config.get(obj.plate_type, {'color': '#6c757d', 'bg': '#e2e3e5', 'icon': '🔬'})
        
        return format_html(
            '<span style="background: {}; color: {}; padding: 2px 6px; '
            'border-radius: 3px; font-size: 11px; font-weight: 500;">{} {}</span>',
            config['bg'],
            config['color'],
            config['icon'],
            obj.get_plate_type_display() if obj.plate_type else 'Unknown'
        )
    plate_type_display.short_description = '🧪 Plate Type'
    plate_type_display.admin_order_field = 'plate_type'
    
    def library_count_badge(self, obj):
        """Enhanced library count display"""
        count = obj._library_count
        if count == 0:
            color = "#6c757d"
            bg = "#e2e3e5"
        elif count <= 24:
            color = "#28a745"
            bg = "#d4edda"
        elif count <= 96:
            color = "#ffc107"
            bg = "#fff3cd"
        else:
            color = "#17a2b8"
            bg = "#d1ecf1"
            
        return format_html(
            '<span style="background: {}; color: {}; padding: 2px 8px; border-radius: 10px; '
            'font-size: 11px; font-weight: 500; min-width: 30px; text-align: center; '
            'display: inline-block;">📚 {}</span>',
            bg, color, count
        )
    library_count_badge.short_description = '📚 Libraries'
    library_count_badge.admin_order_field = '_library_count'
    
    def date_display(self, obj):
        """Enhanced date display"""
        from datetime import datetime, timedelta
        now = datetime.now().date()
        created_date = obj.created_at.date()
        
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
            color,
            time_str,
            created_date.strftime("%Y-%m-%d")
        )
    date_display.short_description = '📅 Created'
    date_display.admin_order_field = 'created_at'
    
    def created_by_display(self, obj):
        """Enhanced user display"""
        if obj.created_by:
            return format_html(
                '<span style="background: #e9ecef; padding: 2px 6px; border-radius: 3px; '
                'font-size: 11px;">👤 {}</span>',
                obj.created_by.get_full_name() or obj.created_by.username
            )
        return format_html('<span style="color: #6c757d;">—</span>')
    created_by_display.short_description = '👤 Created By'
    created_by_display.admin_order_field = 'created_by'
    
    def save_model(self, request, obj, form, change):
        """
        Track the user who creates or updates a plate
        """
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    fieldsets = (
        ('📋 Basic Information', {
            'fields': ('barcode', 'plate_type'),
            'classes': ('wide',),
            'description': 'Core plate identification and type information'
        }),
        ('🏪 Storage Location', {
            'fields': ('freezer_ID', 'rack_ID', 'container_type', 'box_ID', 'well_ID'),
            'classes': ('wide',),
            'description': 'Physical storage location in the laboratory'
        }),
        ('📝 Notes & Comments', {
            'fields': ('notes',),
            'classes': ('wide',),
            'description': 'Additional notes and observations about this plate'
        }),
        ('🔍 System Metadata', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse', 'wide'),
            'description': 'System-generated tracking information'
        }),
    )