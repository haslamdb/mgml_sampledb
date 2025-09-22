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
from django.http import HttpResponse, JsonResponse

from .models import CrudeSample, Aliquot, Extract, SequenceLibrary
from .forms import (
    CrudeSampleForm,
    AliquotForm,
    ExtractForm,
    SequenceLibraryForm,
    AccessioningForm,
    ReportForm,
    QuickAliquotForm,
    AdvancedFilterForm
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


class AliquotUpdateView(PermissionRequiredMixin, UpdateView):
    """
    Update an existing aliquot
    """
    permission_required = 'sampletracking.change_aliquot'
    model = Aliquot
    form_class = AliquotForm
    template_name = 'sampletracking/aliquot_form.html'

    def get_success_url(self):
        return reverse_lazy('aliquot_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, "Aliquot updated successfully.")
        return super().form_valid(form)


class QuickAliquotCreateView(PermissionRequiredMixin, FormView):
    """
    Create both a crude sample and aliquot in one step
    """
    permission_required = ['sampletracking.add_crudesample', 'sampletracking.add_aliquot']
    form_class = QuickAliquotForm
    template_name = 'sampletracking/quick_aliquot_form.html'

    def form_valid(self, form):
        """
        Create both crude sample and aliquot from the form data
        """
        data = form.cleaned_data

        try:
            # Create crude sample
            crude_sample = CrudeSample(
                barcode=data['crude_barcode'],
                subject_id=data['subject_id'],
                collection_date=data['collection_date'],
                sample_source=data['sample_source'],
                date_created=timezone.now().date(),
                status='AVAILABLE' if data.get('store_crude_sample', True) else 'IN_USE',
                freezer_ID=data.get('freezer_ID', ''),
                box_ID=data.get('box_ID', ''),
                notes=data.get('notes', ''),
                created_by=self.request.user,
                updated_by=self.request.user
            )
            crude_sample.save()

            # Create aliquot
            aliquot = Aliquot(
                barcode=data['aliquot_barcode'],
                parent_barcode=crude_sample,
                volume=data.get('aliquot_volume'),
                concentration=data.get('aliquot_concentration'),
                date_created=timezone.now().date(),
                status='AVAILABLE',
                freezer_ID=data.get('freezer_ID', ''),
                box_ID=data.get('box_ID', ''),
                notes=data.get('notes', ''),
                created_by=self.request.user,
                updated_by=self.request.user
            )
            aliquot.save()

            # Log the creation
            logger.info(f"Quick create: crude sample {crude_sample.barcode} and aliquot {aliquot.barcode} by {self.request.user.username}")

            messages.success(
                self.request,
                f"Successfully created crude sample ({crude_sample.barcode}) and aliquot ({aliquot.barcode})"
            )

            # Store the aliquot pk for success URL
            self.aliquot_pk = aliquot.pk

            return super().form_valid(form)

        except Exception as e:
            logger.error(f"Error in quick aliquot creation: {str(e)}")
            messages.error(self.request, f"Error creating samples: {str(e)}")
            return self.form_invalid(form)

    def get_success_url(self):
        """
        Redirect to the aliquot detail page
        """
        return reverse('aliquot_detail', kwargs={'pk': self.aliquot_pk})


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


class ExtractUpdateView(PermissionRequiredMixin, UpdateView):
    """
    Update an existing extract
    """
    permission_required = 'sampletracking.change_extract'
    model = Extract
    form_class = ExtractForm
    template_name = 'sampletracking/extract_form.html'
    
    def get_success_url(self):
        return reverse_lazy('extract_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, "Extract updated successfully.")
        return super().form_valid(form)


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


class SequenceLibraryUpdateView(PermissionRequiredMixin, UpdateView):
    """
    Update an existing sequence library
    """
    permission_required = 'sampletracking.change_sequencelibrary'
    model = SequenceLibrary
    form_class = SequenceLibraryForm
    template_name = 'sampletracking/sequence_library_form.html'
    
    def get_success_url(self):
        return reverse_lazy('library_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, "Sequence library updated successfully.")
        return super().form_valid(form)


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
                    'type': 'Parent Sample',
                    'object': sample,
                    'barcode': sample.barcode,
                    'sample_id': sample.sample_id if sample.sample_id else 'N/A',
                    'date': sample.date_created,
                    'url': reverse('crude_sample_detail', kwargs={'pk': sample.pk})
                })
            for sample in aliquots:
                results.append({
                    'type': 'Aliquot',
                    'object': sample,
                    'barcode': sample.barcode,
                    'sample_id': sample.sample_id if sample.sample_id else 'N/A',
                    'date': sample.date_created,
                    'url': reverse('aliquot_detail', kwargs={'pk': sample.pk})
                })
            for sample in extracts:
                results.append({
                    'type': 'Extract',
                    'object': sample,
                    'barcode': sample.barcode,
                    'sample_id': sample.sample_id if sample.sample_id else 'N/A',
                    'date': sample.date_created,
                    'url': reverse('extract_detail', kwargs={'pk': sample.pk})
                })
            for sample in libraries:
                results.append({
                    'type': 'Sequence Library',
                    'object': sample,
                    'barcode': sample.barcode,
                    'sample_id': sample.sample_id if sample.sample_id else 'N/A',
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

        # Write comprehensive headers based on sample type
        if model_type == 'crudesample':
            writer.writerow([
                'SampleID', 'SubjectID', 'Barcode', 'Sample Source', 'Collection Date',
                'Date Created', 'Status', 'Project', 'Investigator', 'Patient Type',
                'Study ID', 'Isolate Source', 'Source Details',
                'Freezer ID', 'Box ID', 'Well ID', 'Notes'
            ])
            queryset = CrudeSample.objects.filter(pk__in=sample_pks)
            for sample in queryset:
                writer.writerow([
                    sample.sample_id, sample.subject_id, sample.barcode,
                    sample.get_sample_source_display() if hasattr(sample, 'get_sample_source_display') else sample.sample_source or '',
                    sample.collection_date or '',
                    sample.date_created, sample.get_status_display(), sample.project_name or '',
                    sample.investigator or '', sample.patient_type or '', sample.study_id or '',
                    sample.isolate_source or '', sample.source_details or '',
                    sample.freezer_ID or '', sample.box_ID or '',
                    sample.well_ID or '', sample.notes or ''
                ])
        elif model_type == 'aliquot':
            writer.writerow([
                'SampleID', 'SubjectID', 'Barcode', 'Parent Barcode', 'Volume (µL)',
                'Concentration (ng/µL)', 'Date Created', 'Status', 'Project',
                'Investigator', 'Patient Type', 'Study ID', 'Freezer ID',
                'Box ID', 'Well ID', 'Notes'
            ])
            queryset = Aliquot.objects.filter(pk__in=sample_pks).select_related('parent_barcode')
            for sample in queryset:
                subject_id = sample.parent_barcode.subject_id if sample.parent_barcode else ''
                parent_barcode = sample.parent_barcode.barcode if sample.parent_barcode else ''
                writer.writerow([
                    sample.sample_id, subject_id, sample.barcode, parent_barcode,
                    sample.volume or '', sample.concentration or '', sample.date_created,
                    sample.get_status_display(), sample.project_name or '',
                    sample.investigator or '', sample.patient_type or '', sample.study_id or '',
                    sample.freezer_ID or '', sample.box_ID or '',
                    sample.well_ID or '', sample.notes or ''
                ])
        elif model_type == 'extract':
            writer.writerow([
                'SampleID', 'SubjectID', 'Barcode', 'Parent Aliquot', 'Extract Type',
                'Extract Volume (µL)', 'Concentration (ng/µL)', 'Date Created', 'Status',
                'Project', 'Investigator', 'Patient Type', 'Study ID', 'Freezer ID',
                'Box ID', 'Well ID', 'Quality Score', 'Notes'
            ])
            queryset = Extract.objects.filter(pk__in=sample_pks).select_related('parent__parent_barcode')
            for sample in queryset:
                subject_id = sample.parent.parent_barcode.subject_id if sample.parent and sample.parent.parent_barcode else ''
                parent_barcode = sample.parent.barcode if sample.parent else ''
                writer.writerow([
                    sample.sample_id, subject_id, sample.barcode, parent_barcode,
                    sample.get_extract_type_display(), sample.extract_volume or '',
                    sample.concentration or '', sample.date_created, sample.get_status_display(),
                    sample.project_name or '', sample.investigator or '', sample.patient_type or '',
                    sample.study_id or '', sample.freezer_ID or '',
                    sample.box_ID or '', sample.well_ID or '', sample.quality_score or '', sample.notes or ''
                ])
        elif model_type == 'sequencelibrary':
            writer.writerow([
                'SampleID', 'SubjectID', 'Barcode', 'Parent Extract', 'Library Type',
                'N-Index', 'S-Index', 'Plate', 'Well', 'Date Created', 'Date Sequenced',
                'Status', 'Project', 'Investigator', 'Patient Type', 'Study ID',
                'Freezer ID', 'Box ID', 'Well ID', 'Notes'
            ])
            queryset = SequenceLibrary.objects.filter(pk__in=sample_pks).select_related('parent__parent__parent_barcode')
            for sample in queryset:
                subject_id = sample.parent.parent.parent_barcode.subject_id if sample.parent and sample.parent.parent and sample.parent.parent.parent_barcode else ''
                parent_barcode = sample.parent.barcode if sample.parent else ''
                writer.writerow([
                    sample.sample_id, subject_id, sample.barcode, parent_barcode,
                    sample.get_library_type_display(), sample.nindex or '',
                    sample.sindex or '', sample.plate or '', sample.well or '',
                    sample.date_created, sample.date_sequenced or '', sample.get_status_display(),
                    sample.project_name or '', sample.investigator or '', sample.patient_type or '',
                    sample.study_id or '', sample.freezer_ID or '',
                    sample.box_ID or '', sample.well_ID or '', sample.notes or ''
                ])

        return response


class AdvancedFilterView(LoginRequiredMixin, FormView):
    """
    Advanced filtering view for comprehensive sample reports
    """
    template_name = 'sampletracking/advanced_filter.html'
    form_class = AdvancedFilterForm

    def form_valid(self, form):
        # Get filter criteria
        sample_type = form.cleaned_data.get('sample_type')
        project_name = form.cleaned_data.get('project_name')
        investigator = form.cleaned_data.get('investigator')
        patient_type = form.cleaned_data.get('patient_type')
        study_id = form.cleaned_data.get('study_id')
        subject_id = form.cleaned_data.get('subject_id')
        date_from = form.cleaned_data.get('date_from')
        date_to = form.cleaned_data.get('date_to')
        sample_source = form.cleaned_data.get('sample_source')
        isolate_source = form.cleaned_data.get('isolate_source')
        library_type = form.cleaned_data.get('library_type')
        status = form.cleaned_data.get('status')
        legacy_only = form.cleaned_data.get('legacy_only')
        export_format = form.cleaned_data.get('export_format')

        # Build results based on sample type
        results = []

        # Helper function to apply common filters
        def apply_filters(queryset, model_class):
            if project_name:
                queryset = queryset.filter(project_name__icontains=project_name)
            if investigator:
                queryset = queryset.filter(investigator__icontains=investigator)
            if patient_type:
                queryset = queryset.filter(patient_type__icontains=patient_type)
            if study_id:
                queryset = queryset.filter(study_id__icontains=study_id)
            if date_from:
                queryset = queryset.filter(date_created__gte=date_from)
            if date_to:
                queryset = queryset.filter(date_created__lte=date_to)
            if status:
                queryset = queryset.filter(status=status)
            return queryset

        # Query each sample type as needed
        if not sample_type or sample_type == 'crude':
            crude_qs = CrudeSample.objects.all()
            crude_qs = apply_filters(crude_qs, CrudeSample)
            if subject_id:
                crude_qs = crude_qs.filter(subject_id__icontains=subject_id)
            if sample_source:
                crude_qs = crude_qs.filter(sample_source=sample_source)
            if isolate_source:
                crude_qs = crude_qs.filter(isolate_source=isolate_source)

            for sample in crude_qs:
                results.append({
                    'type': 'Parent Sample',
                    'sample_id': sample.sample_id,
                    'barcode': sample.barcode,
                    'subject_id': sample.subject_id,
                    'project': sample.project_name or '-',
                    'investigator': sample.investigator or '-',
                    'patient_type': sample.patient_type or '-',
                    'study_id': sample.study_id or '-',
                    'date': sample.date_created,
                    'status': sample.get_status_display(),
                    'source': sample.get_sample_source_display(),
                    'pk': sample.pk,
                    'url': reverse('crude_sample_detail', kwargs={'pk': sample.pk})
                })

        if not sample_type or sample_type == 'aliquot':
            aliquot_qs = Aliquot.objects.select_related('parent_barcode').all()
            aliquot_qs = apply_filters(aliquot_qs, Aliquot)
            if subject_id:
                aliquot_qs = aliquot_qs.filter(parent_barcode__subject_id__icontains=subject_id)

            for sample in aliquot_qs:
                results.append({
                    'type': 'Aliquot',
                    'sample_id': sample.sample_id,
                    'barcode': sample.barcode,
                    'subject_id': sample.parent_barcode.subject_id if sample.parent_barcode else '-',
                    'project': sample.project_name or '-',
                    'investigator': sample.investigator or '-',
                    'patient_type': sample.patient_type or '-',
                    'study_id': sample.study_id or '-',
                    'date': sample.date_created,
                    'status': sample.get_status_display(),
                    'source': '-',
                    'pk': sample.pk,
                    'url': reverse('aliquot_detail', kwargs={'pk': sample.pk})
                })

        if not sample_type or sample_type == 'extract':
            extract_qs = Extract.objects.select_related('parent__parent_barcode').all()
            extract_qs = apply_filters(extract_qs, Extract)
            if subject_id:
                extract_qs = extract_qs.filter(parent__parent_barcode__subject_id__icontains=subject_id)

            for sample in extract_qs:
                subj_id = '-'
                if sample.parent and sample.parent.parent_barcode:
                    subj_id = sample.parent.parent_barcode.subject_id
                results.append({
                    'type': 'Extract',
                    'sample_id': sample.sample_id,
                    'barcode': sample.barcode,
                    'subject_id': subj_id,
                    'project': sample.project_name or '-',
                    'investigator': sample.investigator or '-',
                    'patient_type': sample.patient_type or '-',
                    'study_id': sample.study_id or '-',
                    'date': sample.date_created,
                    'status': sample.get_status_display(),
                    'source': sample.get_extract_type_display(),
                    'pk': sample.pk,
                    'url': reverse('extract_detail', kwargs={'pk': sample.pk})
                })

        if not sample_type or sample_type == 'library':
            library_qs = SequenceLibrary.objects.select_related('parent__parent__parent_barcode').all()
            library_qs = apply_filters(library_qs, SequenceLibrary)
            if subject_id:
                library_qs = library_qs.filter(parent__parent__parent_barcode__subject_id__icontains=subject_id)
            if library_type:
                library_qs = library_qs.filter(library_type=library_type)
            if legacy_only:
                library_qs = library_qs.filter(is_legacy_import=True)

            for sample in library_qs:
                subj_id = '-'
                if sample.parent and sample.parent.parent and sample.parent.parent.parent_barcode:
                    subj_id = sample.parent.parent.parent_barcode.subject_id

                # Get sequence filenames
                filenames = sample.get_sequence_filenames()

                results.append({
                    'type': 'Sequence Library',
                    'sample_id': sample.sample_id,
                    'barcode': sample.barcode,
                    'subject_id': subj_id,
                    'project': sample.project_name or '-',
                    'investigator': sample.investigator or '-',
                    'patient_type': sample.patient_type or '-',
                    'study_id': sample.study_id or '-',
                    'date': sample.date_created,
                    'status': sample.get_status_display(),
                    'source': sample.get_library_type_display(),
                    'pk': sample.pk,
                    'url': reverse('library_detail', kwargs={'pk': sample.pk}),
                    'is_legacy': sample.is_legacy_import,
                    'sequence_r1': filenames.get('R1', '-'),
                    'sequence_r2': filenames.get('R2', '-'),
                    'legacy_filename': sample.legacy_sequence_filename or '-'
                })

        # Sort results by date
        results.sort(key=lambda x: x['date'], reverse=True)

        # Handle export formats
        if export_format == 'csv':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="filtered_samples.csv"'
            writer = csv.writer(response)

            # Write header - include sequence filenames for libraries
            header = ['Type', 'Sample ID', 'Barcode', 'Subject ID', 'Project',
                     'Investigator', 'Patient Group', 'Study ID', 'Date',
                     'Status', 'Source/Type']

            # Check if we have any sequence libraries in results
            has_libraries = any(r['type'] == 'Sequence Library' for r in results)
            if has_libraries:
                header.extend(['Sequence R1', 'Sequence R2', 'Legacy Filename'])

            writer.writerow(header)

            # Write data
            for r in results:
                row = [
                    r['type'], r['sample_id'], r['barcode'], r['subject_id'],
                    r['project'], r['investigator'], r['patient_type'],
                    r['study_id'], r['date'], r['status'], r['source']
                ]

                # Add sequence filenames if this is a library or if we're including them for all
                if has_libraries:
                    if r['type'] == 'Sequence Library':
                        row.extend([r.get('sequence_r1', '-'), r.get('sequence_r2', '-'),
                                   r.get('legacy_filename', '-')])
                    else:
                        row.extend(['-', '-', '-'])  # Empty columns for non-libraries

                writer.writerow(row)

            return response

        elif export_format == 'labels':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="filtered_labels.csv"'
            writer = csv.writer(response)
            writer.writerow(['SampleID', 'SubjectID', 'Barcode', 'Type', 'Project'])

            for r in results:
                writer.writerow([
                    r['sample_id'], r['subject_id'], r['barcode'],
                    r['type'], r['project']
                ])

            return response

        # Default: render in browser
        return self.render_to_response(self.get_context_data(
            form=form,
            results=results,
            result_count=len(results)
        ))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Advanced Sample Filtering'
        return context


@login_required
def get_all_crude_sample_ids(request):
    ids = list(CrudeSample.objects.values_list('pk', flat=True))
    return JsonResponse({'ids': ids})


@login_required
def get_all_aliquot_ids(request):
    ids = list(Aliquot.objects.values_list('pk', flat=True))
    return JsonResponse({'ids': ids})


@login_required
def get_all_extract_ids(request):
    ids = list(Extract.objects.values_list('pk', flat=True))
    return JsonResponse({'ids': ids})


@login_required
def get_all_library_ids(request):
    ids = list(SequenceLibrary.objects.values_list('pk', flat=True))
    return JsonResponse({'ids': ids})