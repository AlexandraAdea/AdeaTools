"""
URL configuration for adeacore project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from django.shortcuts import render
from django.contrib import admin
from django.urls import path, include
from . import views


def home(request):
    return render(request, 'home.html')


urlpatterns = [
    path('', home, name='home'),
    # Security: Unvorhersagbare Admin-URL (nicht /admin/)
    path('management-console-secure/', admin.site.urls),
    path('management-dashboard/', views.admin_dashboard, name='admin-dashboard'),
    path('desk/', include('adeadesk.urls', namespace='adeadesk')),
    path('zeit/', include('adeazeit.urls', namespace='adeazeit')),
    path('lohn/', include('adealohn.urls', namespace='adealohn')),
]
