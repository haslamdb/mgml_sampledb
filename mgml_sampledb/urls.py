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
from django.urls import path
from django.urls import path
from sampletracking import views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('create_crude_sample/', views.create_crude_sample, name='create_crude_sample'),
    path('sampletracking/templates/create_aliquot/', views.create_aliquot, name='create_aliquot'),
    path('sampletracking/templates/create_extract/', views.create_extract, name='create_extract'),
    path('sampletracking/templates/create_sequence_library/', views.create_sequence_library, name='create_sequence_library')
    ]
