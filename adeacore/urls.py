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
from django.contrib.auth import views as auth_views
from django.urls import path, include
from . import views


def home(request):
    return render(request, 'home.html')


urlpatterns = [
    path('', home, name='home'),
    # Django Admin (Security by Obscurity - versteckte URL)
    path('management-console-secure/', admin.site.urls),
    # Redirect von /admin/ zu /management-console-secure/ für bessere UX
    path('admin/', lambda request: redirect('/management-console-secure/'), name='admin-redirect'),
    # Admin Dashboard
    path('management-dashboard/', views.admin_dashboard, name='admin-dashboard'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('global-logout/', views.global_logout, name='global-logout'),
    path('desk/', include('adeadesk.urls', namespace='adeadesk')),
    path('zeit/', include('adeazeit.urls', namespace='adeazeit')),
    path('lohn/', include('adealohn.urls', namespace='adealohn')),
]
