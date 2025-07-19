"""
URL configuration for mgml_sampledb project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.contrib.auth import views as auth_views
from sampletracking import views
from sampletracking import sample_dashboard


urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Authentication URLs
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('accounts/', include('django.contrib.auth.urls')),
    
    # Main app URLs
    path('', views.HomeView.as_view(), name='home'),
    path('dashboard/', sample_dashboard.dashboard, name='dashboard'),
    path('search/', views.SampleSearchView.as_view(), name='search'),
    
    # Collection staff portal
    path('collection/', views.collection_landing, name='collection_landing'),
    
    # New workflow URLs for accessioning and receiving
    path('register/', views.AccessioningCreateView.as_view(), name='accessioning_create'),
    path('receive/', views.find_sample_to_receive, name='find_sample_to_receive'),
    path('receive/<str:barcode>/', views.ReceiveSampleView.as_view(), name='receive_sample'),
    
    # Crude Sample URLs
    path('crude-samples/', views.CrudeSampleListView.as_view(), name='crude_sample_list'),
    path('crude-samples/create/', views.CrudeSampleCreateView.as_view(), name='create_crude_sample'),
    path('crude-samples/<int:pk>/', views.CrudeSampleDetailView.as_view(), name='crude_sample_detail'),
    path('crude-samples/<int:pk>/edit/', views.CrudeSampleUpdateView.as_view(), name='crude_sample_update'),
    
    # Aliquot URLs
    path('aliquots/', views.AliquotListView.as_view(), name='aliquot_list'),
    path('aliquots/create/', views.AliquotCreateView.as_view(), name='create_aliquot'),
    path('aliquots/<int:pk>/', views.AliquotDetailView.as_view(), name='aliquot_detail'),
    
    # Extract URLs
    path('extracts/', views.ExtractListView.as_view(), name='extract_list'),
    path('extracts/create/', views.ExtractCreateView.as_view(), name='create_extract'),
    path('extracts/<int:pk>/', views.ExtractDetailView.as_view(), name='extract_detail'),
    
    # Sequence Library URLs
    path('libraries/', views.SequenceLibraryListView.as_view(), name='library_list'),
    path('libraries/create/', views.SequenceLibraryCreateView.as_view(), name='create_sequence_library'),
    path('libraries/<int:pk>/', views.SequenceLibraryDetailView.as_view(), name='library_detail'),
    
    # Submission confirmation
    path('sample-submitted/', TemplateView.as_view(template_name='sampletracking/sample_submitted.html'), name='sample_submitted'),
    
    # Reporting URLs
    path('reports/daily_status/', views.ReportView.as_view(), name='daily_status_report'),
]