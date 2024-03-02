from django.shortcuts import render, redirect
from .forms import SampleForm, CrudeSampleForm, AliquotForm, ExtractForm, SequenceLibraryForm
from .models import Sample, CrudeSample, Aliquot, Extract, SequenceLibrary


def create_crude_sample(request):
    if request.method == 'POST':
        form = CrudeSampleForm(request.POST)
        if form.is_valid():
            sample = form.save(commit=False)

            return redirect('sample_submitted')
    else:
        form = CrudeSampleForm()

    return render(request, 'sampletracking/CrudeSampleForm.html', {'form': form})

def create_aliquot(request):
    if request.method == 'POST':
        form = AliquotForm(request.POST)
        if form.is_valid():
            form.save()

            return redirect('sample_submitted')
    else:
        form = AliquotForm()
    return render(request, 'sampletracking/AliquotForm.html', {'form': form})

def create_extract(request):
    if request.method == 'POST':
        form = ExtractForm(request.POST)
        if form.is_valid():
            form.save()

            return redirect('sample_submitted')
    else:
        form = ExtractForm()
    return render(request, 'sampletracking/ExtractForm.html', {'form': form})

def create_sequence_library(request):
    if request.method == 'POST':
        form = SequenceLibraryForm(request.POST)
        if form.is_valid():
            form.save()

            return redirect('sample_submitted')
    else:
        form = SequenceLibraryForm()
    return render(request, 'sampletracking/SequenceLibraryForm.html', {'form': form})

def sample_submitted(request):
    return render(request, 'sampletracking/sample_submitted.html')

def home(request):
    return render(request, 'sampletracking/home.html')



