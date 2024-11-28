"""
URL configuration for Hackathon project.

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
from novathon import views
from novathon.views import get_file_text,legal_analysis_view
urlpatterns = [
    path('admin/', admin.site.urls),
    path('search_case_files/', views.search_case_files_view, name='search_case_files'),
    path('get-file-text/<str:case_id>/', get_file_text, name='get_file_text'),
    path('legal-analysis/', legal_analysis_view, name='legal_analysis'),
]

