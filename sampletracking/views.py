from django.shortcuts import render, redirect
from .forms import SampleForm, CrudeSampleForm, AliquotForm, ExtractForm, SequenceLibraryForm
from .models import Sample, CrudeSample, Aliquot, Extract, SequenceLibrary

def create_crude_sample(request):
    if request.method == 'POST':
        form = CrudeSampleForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = CrudeSampleForm()
    return render(request, 'create.html', {'form': form})

def create_aliquot(request):
    if request.method == 'POST':
        form = AliquotForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = AliquotForm()
    return render(request, 'create.html', {'form': form})

def create_extract(request):
    if request.method == 'POST':
        form = ExtractForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = ExtractForm()
    return render(request, 'create.html', {'form': form})

def create_sequence_library(request):
    if request.method == 'POST':
        form = SequenceLibraryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = SequenceLibraryForm()
    return render(request, 'create.html', {'form': form})
