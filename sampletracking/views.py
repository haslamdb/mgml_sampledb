from django.shortcuts import render, redirect

def sample_entry(request):
    if request.method == 'POST':
        base_form = SampleBaseForm(request.POST)
        crude_form = CrudeSampleForm(request.POST)
        if base_form.is_valid() and crude_form.is_valid():
            base_instance = base_form.save()
            crude_instance = crude_form.save(commit=False)
            crude_instance.base_sample = base_instance
            crude_instance.save()
            return redirect('success_url')  # Redirect to a new URL
    else:
        base_form = SampleBaseForm()
        crude_form = CrudeSampleForm()
    return render(request, 'sample_entry.html', {'base_form': base_form, 'crude_form': crude_form})

