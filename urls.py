"""
URL configuration for mgml_sampledb project.
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

from sampletracking import views
from sampletracking.views import (
    HomeView,
    CrudeSampleListView,
    CrudeSampleCreateView,
    CrudeSampleDetailView,
    CrudeSampleUpdateView,
    AliquotListView,
    AliquotCreateView,
    AliquotDetailView,
    ExtractListView,
    ExtractCreateView,
    ExtractDetailView,
    SequenceLibraryListView,
    SequenceLibraryCreateView,
    SequenceLibraryDetailView,
    SampleSearchView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Authentication URLs
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('accounts/password_change/', auth_views.PasswordChangeView.as_view(), name='password_change'),
    path('accounts/password_change/done/', auth_views.PasswordChangeDoneView.as_view(), name='password_change_done'),
    
    # Dashboard
    path('', HomeView.as_view(), name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Sample submission completion
    path('sample_submitted/', views.sample_submitted, name='sample_submitted'),
    
    # Extract URLs
    path('extracts/', ExtractListView.as_view(), name='extract_list'),
    path('extracts/new/', ExtractCreateView.as_view(), name='create_extract'),
    path('extracts/<int:pk>/', ExtractDetailView.as_view(), name='extract_detail'),
    path('api/extracts/ids/', views.get_all_extract_ids, name='get_all_extract_ids'),
    
    # Sequence Library URLs
    path('libraries/', SequenceLibraryListView.as_view(), name='library_list'),
    path('libraries/new/', SequenceLibraryCreateView.as_view(), name='create_sequence_library'),
    path('libraries/<int:pk>/', SequenceLibraryDetailView.as_view(), name='library_detail'),
    path('api/libraries/ids/', views.get_all_library_ids, name='get_all_library_ids'),
    
    # Crude Sample URLs
    path('crude_samples/', CrudeSampleListView.as_view(), name='crude_sample_list'),
    path('crude_samples/new/', CrudeSampleCreateView.as_view(), name='create_crude_sample'),
    path('crude_samples/<int:pk>/', CrudeSampleDetailView.as_view(), name='crude_sample_detail'),
    path('crude_samples/<int:pk>/edit/', CrudeSampleUpdateView.as_view(), name='crude_sample_edit'),
    path('api/crude_samples/ids/', views.get_all_crude_sample_ids, name='get_all_crude_sample_ids'),
    
    # Aliquot URLs
    path('aliquots/', AliquotListView.as_view(), name='aliquot_list'),
    path('aliquots/new/', AliquotCreateView.as_view(), name='create_aliquot'),
    path('aliquots/<int:pk>/', AliquotDetailView.as_view(), name='aliquot_detail'),
    path('api/aliquots/ids/', views.get_all_aliquot_ids, name='get_all_aliquot_ids'),
    
    # Search
    path('search/', SampleSearchView.as_view(), name='sample_search'),
]
