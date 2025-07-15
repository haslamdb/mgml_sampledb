from django.views.generic import ListView, CreateView, UpdateView, DetailView, TemplateView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.db.models import Q

from .models import CrudeSample, Aliquot, Extract, SequenceLibrary
from .forms import (
    CrudeSampleForm, 
    AliquotForm, 
    ExtractForm, 
    SequenceLibraryForm,
    AccessioningForm
)


class HomeView(TemplateView):
    """
    Home page view
    """
    template_name = 'sampletracking/home.html'


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
                Q(your_id__icontains=query) |
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
                    'url': reverse_lazy('crude_sample_detail', kwargs={'pk': sample.pk})
                })
            for sample in aliquots:
                results.append({
                    'type': 'Aliquot',
                    'object': sample,
                    'barcode': sample.barcode,
                    'date': sample.date_created,
                    'url': reverse_lazy('aliquot_detail', kwargs={'pk': sample.pk})
                })
            for sample in extracts:
                results.append({
                    'type': 'Extract',
                    'object': sample,
                    'barcode': sample.barcode,
                    'date': sample.date_created,
                    'url': reverse_lazy('extract_detail', kwargs={'pk': sample.pk})
                })
            for sample in libraries:
                results.append({
                    'type': 'Sequence Library',
                    'object': sample,
                    'barcode': sample.barcode,
                    'date': sample.date_created,
                    'url': reverse_lazy('library_detail', kwargs={'pk': sample.pk})
                })
            
            return sorted(results, key=lambda x: x['date'], reverse=True)
        return []
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        return context