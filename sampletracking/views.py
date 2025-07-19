from django.views.generic import ListView, CreateView, UpdateView, DetailView, TemplateView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.db.models import Q
from datetime import datetime, time

from .models import CrudeSample, Aliquot, Extract, SequenceLibrary
from .forms import (
    CrudeSampleForm, 
    AliquotForm, 
    ExtractForm, 
    SequenceLibraryForm,
    AccessioningForm,
    ReportForm
)


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
    success_url = reverse_lazy('sample_submitted')
    
    def form_valid(self, form):
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
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add aliquots derived from this sample
        context['aliquots'] = Aliquot.objects.filter(parent_barcode=self.object.barcode)
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
    success_url = reverse_lazy('sample_submitted')
    permission_required = 'sampletracking.add_crudesample'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Register New Sample"
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        form.instance.date_created = timezone.now().date()
        form.instance.status = 'AWAITING_RECEIPT'
        
        # Track if barcode validation was overridden
        if form.cleaned_data.get('override_barcode_check'):
            form.instance.barcode_override_used = True
            existing_notes = form.instance.notes or ''
            override_note = "[BARCODE OVERRIDE] Generic barcode used - Subject ID validation was overridden during registration."
            form.instance.notes = f"{override_note}\n{existing_notes}".strip()
        
        messages.success(self.request, f"Sample {form.instance.barcode} registered and is awaiting receipt.")
        return super().form_valid(form)


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
        barcode = request.POST.get('barcode')
        if CrudeSample.objects.filter(barcode=barcode).exists():
            return redirect('receive_sample', barcode=barcode)
        else:
            messages.error(request, f"No sample found with barcode '{barcode}'. Please register it first.")
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
        return Aliquot.objects.all().order_by('-date_created')


class AliquotCreateView(PermissionRequiredMixin, CreateView):
    """
    Create a new aliquot
    """
    permission_required = 'sampletracking.add_aliquot'
    model = Aliquot
    form_class = AliquotForm
    template_name = 'sampletracking/aliquot_form.html'
    success_url = reverse_lazy('sample_submitted')
    
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
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add extracts derived from this aliquot
        context['extracts'] = Extract.objects.filter(parent=self.object.barcode)
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
        return Extract.objects.all().order_by('-date_created')


class ExtractCreateView(PermissionRequiredMixin, CreateView):
    """
    Create a new extract
    """
    permission_required = 'sampletracking.add_extract'
    model = Extract
    form_class = ExtractForm
    template_name = 'sampletracking/extract_form.html'
    success_url = reverse_lazy('sample_submitted')
    
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
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add libraries derived from this extract
        context['libraries'] = SequenceLibrary.objects.filter(parent=self.object)
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
        return SequenceLibrary.objects.all().order_by('-date_created')


class SequenceLibraryCreateView(PermissionRequiredMixin, CreateView):
    """
    Create a new sequence library
    """
    permission_required = 'sampletracking.add_sequencelibrary'
    model = SequenceLibrary
    form_class = SequenceLibraryForm
    template_name = 'sampletracking/sequence_library_form.html'
    success_url = reverse_lazy('sample_submitted')
    
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
        query = self.request.GET.get('q', '')
        if query:
            # Search across all sample types
            crude_samples = CrudeSample.objects.filter(
                Q(barcode__icontains=query) | 
                Q(subject_id__icontains=query) |
                Q(notes__icontains=query)
            )
            aliquots = Aliquot.objects.filter(
                Q(barcode__icontains=query) |
                Q(notes__icontains=query)
            )
            extracts = Extract.objects.filter(
                Q(barcode__icontains=query) |
                Q(notes__icontains=query) |
                Q(extract_type__icontains=query)
            )
            libraries = SequenceLibrary.objects.filter(
                Q(barcode__icontains=query) |
                Q(notes__icontains=query) |
                Q(library_type__icontains=query)
            )
            
            # Combine results with type information
            results = []
            for sample in crude_samples:
                results.append({
                    'type': 'Crude Sample',
                    'object': sample,
                    'barcode': sample.barcode,
                    'date': sample.date_created,
                    'url': reverse('crude_sample_detail', kwargs={'pk': sample.pk})
                })
            for sample in aliquots:
                results.append({
                    'type': 'Aliquot',
                    'object': sample,
                    'barcode': sample.barcode,
                    'date': sample.date_created,
                    'url': reverse('aliquot_detail', kwargs={'pk': sample.pk})
                })
            for sample in extracts:
                results.append({
                    'type': 'Extract',
                    'object': sample,
                    'barcode': sample.barcode,
                    'date': sample.date_created,
                    'url': reverse('extract_detail', kwargs={'pk': sample.pk})
                })
            for sample in libraries:
                results.append({
                    'type': 'Sequence Library',
                    'object': sample,
                    'barcode': sample.barcode,
                    'date': sample.date_created,
                    'url': reverse('library_detail', kwargs={'pk': sample.pk})
                })
            
            return sorted(results, key=lambda x: x['date'], reverse=True)
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