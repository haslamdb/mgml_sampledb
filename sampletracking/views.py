from django.views.generic import ListView, CreateView, UpdateView, DetailView, TemplateView, FormView, View
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.db.models import Q
from datetime import datetime, time
import logging
import re
import csv
from django.http import HttpResponse

from .models import CrudeSample, Aliquot, Extract, SequenceLibrary
from .forms import (
    CrudeSampleForm, 
    AliquotForm, 
    ExtractForm, 
    SequenceLibraryForm,
    AccessioningForm,
    ReportForm
)

# Set up logging for security events
logger = logging.getLogger('sampletracking')

# Security constants
MAX_LOGIN_ATTEMPTS = 5
BARCODE_PATTERN = re.compile(r'^[A-Za-z0-9_-]+$')
MAX_SEARCH_QUERY_LENGTH = 100
MIN_SEARCH_QUERY_LENGTH = 2


class HomeView(TemplateView):
    """
    Home page view with role-based redirects
    """
    template_name = 'sampletracking/home.html'
    
    def get(self, request, *args, **kwargs):
        # Check if user is authenticated and belongs to Sample Collectors group
        if request.user.is_authenticated:
            if request.user.groups.filter(name='Sample Collectors').exists():
                # Redirect sample collectors to their dedicated portal
                return redirect('collection_landing')
        return super().get(request, *args, **kwargs)


class CrudeSampleListView(PermissionRequiredMixin, ListView):
    """
    Display a list of all crude samples
    """
    permission_required = 'sampletracking.view_crudesample'
    model = CrudeSample
    template_name = 'sampletracking/crude_sample_list.html'
    context_object_name = 'samples'
    paginate_by = 10
    
    def get_queryset(self):
        return CrudeSample.objects.all().order_by('-date_created')


class CrudeSampleCreateView(PermissionRequiredMixin, CreateView):
    """
    Create a new crude sample
    """
    permission_required = 'sampletracking.add_crudesample'
    model = CrudeSample
    form_class = CrudeSampleForm
    template_name = 'sampletracking/crude_sample_form.html'

    def get_success_url(self):
        return f"{reverse('sample_submitted')}?next_url=create_crude_sample&next_text=Create Another Crude Sample"
    
    def form_valid(self, form):
        # Log sample creation
        logger.info(f"New crude sample created by user {self.request.user.username}")
        
        # Add the current user as the creator
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        messages.success(self.request, "Crude sample created successfully.")
        return super().form_valid(form)


class CrudeSampleDetailView(PermissionRequiredMixin, DetailView):
    """
    Display details of a crude sample
    """
    permission_required = 'sampletracking.view_crudesample'
    model = CrudeSample
    template_name = 'sampletracking/crude_sample_detail.html'
    context_object_name = 'sample'
    
    def get_queryset(self):
        return CrudeSample.objects.prefetch_related('aliquots')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Use prefetched aliquots instead of querying again
        context['aliquots'] = self.object.aliquots.all()
        return context


class CrudeSampleUpdateView(PermissionRequiredMixin, UpdateView):
    """
    Update an existing crude sample
    """
    permission_required = 'sampletracking.change_crudesample'
    model = CrudeSample
    form_class = CrudeSampleForm
    template_name = 'sampletracking/crude_sample_form.html'
    
    def get_success_url(self):
        return reverse_lazy('crude_sample_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, "Crude sample updated successfully.")
        return super().form_valid(form)


class AccessioningCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    View for collection staff to register a new sample into the system.
    """
    model = CrudeSample
    form_class = AccessioningForm
    template_name = 'sampletracking/accessioning_form.html'
    permission_required = 'sampletracking.add_crudesample'

    def get_success_url(self):
        return f"{reverse('sample_submitted')}?next_url=accessioning_create&next_text=Register Another Sample"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Register New Sample"
        return context

    def form_valid(self, form):
        # Log sample registration
        logger.info(f"Sample registration by user {self.request.user.username}")
        
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        form.instance.date_created = timezone.now().date()
        form.instance.status = 'AWAITING_RECEIPT'
        
        # Save the crude sample first
        response = super().form_valid(form)

        # Check if we need to auto-create an aliquot
        if form.cleaned_data.get('auto_create_aliquot'):
            crude_sample = self.object
            aliquot_barcode = form.cleaned_data.get('aliquot_barcode')
            
            # Create the aliquot
            Aliquot.objects.create(
                parent_barcode=crude_sample,
                barcode=aliquot_barcode,
                date_created=crude_sample.collection_date, # Match collection date
                status='AWAITING_RECEIPT',
                created_by=self.request.user,
                updated_by=self.request.user
            )
            logger.info(f"Automatically created aliquot {aliquot_barcode} for crude sample {crude_sample.barcode} by user {self.request.user.username}")
            messages.success(self.request, f"Aliquot {aliquot_barcode} was also created automatically.")

        messages.success(self.request, f"Sample {form.instance.barcode} registered and is awaiting receipt.")
        return response


class ReceiveSampleView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    View for lab staff to receive a sample that has been registered.
    This view finds the sample by barcode and allows staff to update its
    status and storage location.
    """
    model = CrudeSample
    form_class = CrudeSampleForm
    template_name = 'sampletracking/receive_sample_form.html'
    permission_required = 'sampletracking.change_crudesample'

    def get_object(self, queryset=None):
        barcode = self.kwargs.get('barcode')
        sample = get_object_or_404(CrudeSample, barcode=barcode)
        return sample

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Receive Sample: {self.object.barcode}"
        return context

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        form.instance.status = 'AVAILABLE'
        messages.success(self.request, f"Sample {form.instance.barcode} has been received and stored.")
        return super().form_valid(form)
        
    def get_success_url(self):
        return reverse_lazy('crude_sample_detail', kwargs={'pk': self.object.pk})


@login_required
def find_sample_to_receive(request):
    """
    A simple view to handle the barcode scan/search before the update
    """
    if request.method == 'POST':
        barcode = request.POST.get('barcode', '').strip()
        
        # Log barcode search attempts
        logger.info(f"Barcode search attempt by user {request.user.username}: {barcode}")
        
        # Input validation for barcode
        if not barcode:
            messages.error(request, "Please enter a barcode.")
            return render(request, 'sampletracking/find_sample_form.html')
        
        if len(barcode) > 255:  # Match the model field max_length
            logger.warning(f"Oversized barcode attempted by user {request.user.username}: {len(barcode)} characters")
            messages.error(request, "Barcode is too long.")
            return render(request, 'sampletracking/find_sample_form.html')
        
        # Check for valid barcode format (alphanumeric, underscore, hyphen)
        if not BARCODE_PATTERN.match(barcode):
            logger.warning(f"Invalid barcode format attempted by user {request.user.username}: {barcode}")
            messages.error(request, "Barcode contains invalid characters. Only letters, numbers, underscores, and hyphens are allowed.")
            return render(request, 'sampletracking/find_sample_form.html')
        
        # Check for suspicious patterns
        suspicious_patterns = ['<script', 'javascript:', 'DROP', 'DELETE', 'INSERT', 'UPDATE', '--', ';']
        if any(pattern.lower() in barcode.lower() for pattern in suspicious_patterns):
            logger.critical(f"Suspicious barcode pattern detected from user {request.user.username}: {barcode}")
            messages.error(request, "Invalid barcode format.")
            return render(request, 'sampletracking/find_sample_form.html')
        
        try:
            if CrudeSample.objects.filter(barcode=barcode).exists():
                logger.info(f"Barcode search successful by user {request.user.username}: {barcode}")
                return redirect('receive_sample', barcode=barcode)
            else:
                logger.info(f"Barcode not found by user {request.user.username}: {barcode}")
                messages.error(request, f"No sample found with barcode '{barcode}'. Please register it first.")
        except Exception as e:
            logger.error(f"Database error during barcode search by user {request.user.username}: {str(e)}")
            messages.error(request, "An error occurred while searching. Please try again.")
            
    return render(request, 'sampletracking/find_sample_form.html')


@login_required
def collection_landing(request):
    """
    Simplified landing page for sample collectors
    """
    # Check if user belongs to appropriate group
    if not (request.user.groups.filter(name='Sample Collectors').exists() or 
            request.user.is_staff):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('home')
    
    # Get samples registered by this user today
    today_start = datetime.combine(timezone.now().date(), time.min)
    today_end = datetime.combine(timezone.now().date(), time.max)
    
    recent_samples = CrudeSample.objects.filter(
        created_by=request.user,
        created_at__range=(today_start, today_end)
    ).order_by('-created_at')[:10]
    
    context = {
        'recent_samples': recent_samples,
    }
    
    return render(request, 'sampletracking/collection_landing.html', context)


class AliquotListView(PermissionRequiredMixin, ListView):
    """
    Display a list of all aliquots
    """
    permission_required = 'sampletracking.view_aliquot'
    model = Aliquot
    template_name = 'sampletracking/aliquot_list.html'
    context_object_name = 'aliquots'
    paginate_by = 10
    
    def get_queryset(self):
        return Aliquot.objects.select_related('parent_barcode').order_by('-date_created')


class AliquotCreateView(PermissionRequiredMixin, CreateView):
    """
    Create a new aliquot
    """
    permission_required = 'sampletracking.add_aliquot'
    model = Aliquot
    form_class = AliquotForm
    template_name = 'sampletracking/aliquot_form.html'

    def get_success_url(self):
        return f"{reverse('sample_submitted')}?next_url=create_aliquot&next_text=Create Another Aliquot"
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        messages.success(self.request, "Aliquot created successfully.")
        return super().form_valid(form)


class AliquotDetailView(PermissionRequiredMixin, DetailView):
    """
    Display details of an aliquot
    """
    permission_required = 'sampletracking.view_aliquot'
    model = Aliquot
    template_name = 'sampletracking/aliquot_detail.html'
    context_object_name = 'aliquot'
    
    def get_queryset(self):
        return Aliquot.objects.select_related('parent_barcode').prefetch_related('extracts')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Use prefetched extracts instead of querying again
        context['extracts'] = self.object.extracts.all()
        return context


class ExtractListView(PermissionRequiredMixin, ListView):
    """
    Display a list of all extracts
    """
    permission_required = 'sampletracking.view_extract'
    model = Extract
    template_name = 'sampletracking/extract_list.html'
    context_object_name = 'extracts'
    paginate_by = 10
    
    def get_queryset(self):
        return Extract.objects.select_related('parent').order_by('-date_created')


class ExtractCreateView(PermissionRequiredMixin, CreateView):
    """
    Create a new extract
    """
    permission_required = 'sampletracking.add_extract'
    model = Extract
    form_class = ExtractForm
    template_name = 'sampletracking/extract_form.html'

    def get_success_url(self):
        return f"{reverse('sample_submitted')}?next_url=create_extract&next_text=Create Another Extract"
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        messages.success(self.request, "Extract created successfully.")
        return super().form_valid(form)


class ExtractDetailView(PermissionRequiredMixin, DetailView):
    """
    Display details of an extract
    """
    permission_required = 'sampletracking.view_extract'
    model = Extract
    template_name = 'sampletracking/extract_detail.html'
    context_object_name = 'extract'
    
    def get_queryset(self):
        return Extract.objects.select_related('parent').prefetch_related('libraries')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Use prefetched libraries instead of querying again
        context['libraries'] = self.object.libraries.all()
        return context


class SequenceLibraryListView(PermissionRequiredMixin, ListView):
    """
    Display a list of all sequence libraries
    """
    permission_required = 'sampletracking.view_sequencelibrary'
    model = SequenceLibrary
    template_name = 'sampletracking/sequence_library_list.html'
    context_object_name = 'libraries'
    paginate_by = 10
    
    def get_queryset(self):
        return SequenceLibrary.objects.select_related('parent', 'plate').order_by('-date_created')


class SequenceLibraryCreateView(PermissionRequiredMixin, CreateView):
    """
    Create a new sequence library
    """
    permission_required = 'sampletracking.add_sequencelibrary'
    model = SequenceLibrary
    form_class = SequenceLibraryForm
    template_name = 'sampletracking/sequence_library_form.html'

    def get_success_url(self):
        return f"{reverse('sample_submitted')}?next_url=create_sequence_library&next_text=Create Another Library"
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        messages.success(self.request, "Sequence library created successfully.")
        return super().form_valid(form)


class SequenceLibraryDetailView(PermissionRequiredMixin, DetailView):
    """
    Display details of a sequence library
    """
    permission_required = 'sampletracking.view_sequencelibrary'
    model = SequenceLibrary
    template_name = 'sampletracking/sequence_library_detail.html'
    context_object_name = 'library'


class SampleSearchView(PermissionRequiredMixin, ListView):
    """
    Search for samples across all types
    """
    permission_required = ['sampletracking.view_crudesample', 'sampletracking.view_aliquot', 'sampletracking.view_extract', 'sampletracking.view_sequencelibrary']
    template_name = 'sampletracking/search_results.html'
    context_object_name = 'results'
    paginate_by = 20
    
    def get_queryset(self):
        query = self.request.GET.get('q', '').strip()
        
        # Log search attempts for security monitoring
        logger.info(f"Search attempt by user {self.request.user.username} with query: {query[:50]}...")
        
        # Basic input validation and sanitization
        if not query or len(query) < MIN_SEARCH_QUERY_LENGTH:
            return []
        
        # Limit query length to prevent potential DoS
        if len(query) > MAX_SEARCH_QUERY_LENGTH:
            logger.warning(f"Oversized search query attempted by user {self.request.user.username}: {len(query)} characters")
            query = query[:MAX_SEARCH_QUERY_LENGTH]
        
        # Check for suspicious patterns that might indicate injection attempts
        suspicious_patterns = ['<script', 'javascript:', 'DROP TABLE', 'DELETE FROM', 'INSERT INTO', 'UPDATE ', '--', ';']
        if any(pattern.lower() in query.lower() for pattern in suspicious_patterns):
            logger.warning(f"Suspicious search query detected from user {self.request.user.username}: {query}")
            return []
        
        try:
            # Search across all sample types with optimized queries
            crude_samples = CrudeSample.objects.filter(
                Q(barcode__icontains=query) | 
                Q(subject_id__icontains=query) |
                Q(notes__icontains=query)
            ).select_related('created_by', 'updated_by')
            
            aliquots = Aliquot.objects.filter(
                Q(barcode__icontains=query) |
                Q(notes__icontains=query)
            ).select_related('parent_barcode', 'created_by', 'updated_by')
            
            extracts = Extract.objects.filter(
                Q(barcode__icontains=query) |
                Q(notes__icontains=query) |
                Q(extract_type__icontains=query)
            ).select_related('parent', 'parent__parent_barcode', 'created_by', 'updated_by')

            libraries = SequenceLibrary.objects.filter(
                Q(barcode__icontains=query) |
                Q(notes__icontains=query) |
                Q(library_type__icontains=query)
            ).select_related('parent', 'parent__parent', 'parent__parent__parent_barcode', 'plate', 'created_by', 'updated_by')
            
            # Combine results with type information
            results = []
            for sample in crude_samples:
                results.append({
                    'type': 'Crude Sample',
                    'object': sample,
                    'barcode': sample.barcode,
                    'sample_id': sample.subject_id if sample.subject_id else 'N/A',
                    'date': sample.date_created,
                    'url': reverse('crude_sample_detail', kwargs={'pk': sample.pk})
                })
            for sample in aliquots:
                results.append({
                    'type': 'Aliquot',
                    'object': sample,
                    'barcode': sample.barcode,
                    'sample_id': sample.parent_barcode.subject_id if sample.parent_barcode and sample.parent_barcode.subject_id else 'N/A',
                    'date': sample.date_created,
                    'url': reverse('aliquot_detail', kwargs={'pk': sample.pk})
                })
            for sample in extracts:
                # Get subject_id through parent aliquot -> crude sample chain
                sample_id = 'N/A'
                if sample.parent and sample.parent.parent_barcode:
                    sample_id = sample.parent.parent_barcode.subject_id if sample.parent.parent_barcode.subject_id else 'N/A'
                results.append({
                    'type': 'Extract',
                    'object': sample,
                    'barcode': sample.barcode,
                    'sample_id': sample_id,
                    'date': sample.date_created,
                    'url': reverse('extract_detail', kwargs={'pk': sample.pk})
                })
            for sample in libraries:
                # Get subject_id through parent extract -> aliquot -> crude sample chain
                sample_id = 'N/A'
                if sample.parent and sample.parent.parent and sample.parent.parent.parent_barcode:
                    sample_id = sample.parent.parent.parent_barcode.subject_id if sample.parent.parent.parent_barcode.subject_id else 'N/A'
                results.append({
                    'type': 'Sequence Library',
                    'object': sample,
                    'barcode': sample.barcode,
                    'sample_id': sample_id,
                    'date': sample.date_created,
                    'url': reverse('library_detail', kwargs={'pk': sample.pk})
                })
            
            logger.info(f"Search completed by user {self.request.user.username}: {len(results)} results found")
            return sorted(results, key=lambda x: x['date'], reverse=True)
            
        except Exception as e:
            logger.error(f"Search error for user {self.request.user.username}: {str(e)}")
            messages.error(self.request, "An error occurred during search. Please try again.")
            return []
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        return context


class ReportView(LoginRequiredMixin, FormView):
    """
    View for generating and displaying a daily sample status report.
    """
    template_name = 'sampletracking/report_form.html'
    form_class = ReportForm

    def form_valid(self, form):
        report_date = form.cleaned_data['report_date']
        
        # 1. Get all crude samples for the selected day.
        crude_samples = list(CrudeSample.objects.filter(collection_date=report_date).order_by('subject_id'))
        
        # Get all barcodes from these crude samples to use in subsequent queries.
        crude_barcodes = [cs.barcode for cs in crude_samples]

        # 2. Get all aliquots that are children of these crude samples.
        aliquots = Aliquot.objects.filter(parent_barcode__barcode__in=crude_barcodes).select_related('parent_barcode')
        aliquot_barcodes = [a.barcode for a in aliquots]

        # 3. Get all extracts that are children of these aliquots.
        extracts = Extract.objects.filter(parent__barcode__in=aliquot_barcodes).select_related('parent')
        extract_pks = [e.pk for e in extracts]

        # 4. Get all libraries that are children of these extracts.
        libraries = SequenceLibrary.objects.filter(parent_id__in=extract_pks).select_related('parent')

        # Create sets for quick lookups
        aliquot_parent_barcodes = {a.parent_barcode.barcode for a in aliquots}
        extract_parent_barcodes = {e.parent.barcode for e in extracts}
        library_parent_pks = {l.parent.pk for l in libraries}

        # Build the final report data structure
        report_data = []
        for cs in crude_samples:
            # Get the earliest aliquot date for this crude sample
            aliquot_date = None
            child_aliquots = [a for a in aliquots if a.parent_barcode.barcode == cs.barcode]
            if child_aliquots:
                aliquot_date = min(a.date_created for a in child_aliquots)
            
            # Get the earliest extract date for the children of this crude sample
            extract_date = None
            child_aliquot_barcodes = {a.barcode for a in child_aliquots}
            child_extracts = [e for e in extracts if e.parent.barcode in child_aliquot_barcodes]
            if child_extracts:
                extract_date = min(e.date_created for e in child_extracts)

            # Get the earliest library date for the grandchildren of this crude sample
            library_date = None
            child_extract_pks = {e.pk for e in child_extracts}
            child_libraries = [l for l in libraries if l.parent.pk in child_extract_pks]
            if child_libraries:
                library_date = min(l.date_created for l in child_libraries)

            report_data.append({
                'patient_id': cs.subject_id,
                'sample_type': cs.get_sample_source_display(),
                'collection_date': cs.collection_date,
                'aliquot_date': aliquot_date,
                'extract_date': extract_date,
                'library_date': library_date,
            })

        # Pass the processed data and the date back to the template context
        context = self.get_context_data(form=form, report_data=report_data, report_date=report_date)
        return self.render_to_response(context)


class ComprehensiveReportView(LoginRequiredMixin, TemplateView):
    """
    View for generating comprehensive sample reports with filtering options.
    """
    template_name = 'sampletracking/comprehensive_report.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get filter parameters from request
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        sample_type = self.request.GET.get('sample_type')
        
        # Start with all crude samples
        crude_samples = CrudeSample.objects.all()
        
        # Apply date filters
        if date_from:
            crude_samples = crude_samples.filter(collection_date__gte=date_from)
        if date_to:
            crude_samples = crude_samples.filter(collection_date__lte=date_to)
        
        # Apply sample type filter
        if sample_type and sample_type != 'all':
            crude_samples = crude_samples.filter(sample_source=sample_type)
        
        # Order by collection date and prefetch related objects to avoid N+1 queries
        crude_samples = crude_samples.order_by('-collection_date', 'subject_id').prefetch_related(
            'aliquots',
            'aliquots__extracts', 
            'aliquots__extracts__libraries'
        )
        
        # Build report data efficiently
        report_data = []
        for cs in crude_samples:
            # Get all related objects from prefetched data
            aliquots = list(cs.aliquots.all())
            extracts = []
            libraries = []
            
            for aliquot in aliquots:
                aliquot_extracts = list(aliquot.extracts.all())
                extracts.extend(aliquot_extracts)
                
                for extract in aliquot_extracts:
                    libraries.extend(list(extract.libraries.all()))
            
            # Calculate counts and latest items
            latest_aliquot = max(aliquots, key=lambda x: x.date_created) if aliquots else None
            latest_extract = max(extracts, key=lambda x: x.date_created) if extracts else None
            latest_library = max(libraries, key=lambda x: x.date_created) if libraries else None
            
            report_data.append({
                'crude_sample': cs,
                'aliquot_count': len(aliquots),
                'extract_count': len(extracts),
                'library_count': len(libraries),
                'latest_aliquot': latest_aliquot,
                'latest_extract': latest_extract,
                'latest_library': latest_library,
            })
        
        # Get sample type choices for filter dropdown
        sample_type_choices = CrudeSample.SAMPLE_SOURCE_CHOICES
        
        context.update({
            'report_data': report_data,
            'sample_type_choices': sample_type_choices,
            'date_from': date_from,
            'date_to': date_to,
            'selected_sample_type': sample_type,
            'total_samples': len(report_data),
        })
        
        return context

class SampleSubmittedView(TemplateView):
    """
    A generic success page that can link back to the creation form.
    """
    template_name = 'sampletracking/sample_submitted.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        next_url_name = self.request.GET.get('next_url')
        next_text = self.request.GET.get('next_text')
        
        if next_url_name:
            try:
                context['next_url'] = reverse(next_url_name)
                context['next_text'] = next_text or "Go Back"
            except Exception:
                # Fail silently if the URL name is invalid
                pass
        return context

class ExportLabelsView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        sample_pks = request.POST.getlist('selected_samples')
        model_type = request.POST.get('model_type')

        if not sample_pks:
            messages.error(request, "You didn\'t select any samples to export.")
            # Redirect back to the referring page, or a default
            return redirect(request.META.get('HTTP_REFERER', 'home'))

        response = HttpResponse(
            content_type='text/csv',
            headers={'Content-Disposition': 'attachment; filename="sample_labels.csv"'},
        )

        writer = csv.writer(response)
        writer.writerow(['SubjectID', 'Barcode'])

        queryset = None
        if model_type == 'crudesample':
            queryset = CrudeSample.objects.filter(pk__in=sample_pks)
            for sample in queryset:
                writer.writerow([sample.subject_id, sample.barcode])
        elif model_type == 'aliquot':
            queryset = Aliquot.objects.filter(pk__in=sample_pks).select_related('parent_barcode')
            for sample in queryset:
                writer.writerow([sample.parent_barcode.subject_id, sample.barcode])
        elif model_type == 'extract':
            queryset = Extract.objects.filter(pk__in=sample_pks).select_related('parent__parent_barcode')
            for sample in queryset:
                writer.writerow([sample.parent.parent_barcode.subject_id, sample.barcode])
        elif model_type == 'sequencelibrary':
            queryset = SequenceLibrary.objects.filter(pk__in=sample_pks).select_related('parent__parent__parent_barcode')
            for sample in queryset:
                writer.writerow([sample.parent.parent.parent_barcode.subject_id, sample.barcode])

        return response