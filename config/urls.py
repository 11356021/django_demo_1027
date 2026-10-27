"""
URL configuration for config project.
"""
from django.contrib import admin
from django.urls import include, path
from django.shortcuts import redirect

urlpatterns = [
    path('', lambda request: redirect('course_list')),
    path('admin/', admin.site.urls),
    path('', include('enrollments.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
]
