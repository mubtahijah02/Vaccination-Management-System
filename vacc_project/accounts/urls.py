"""
URL configuration for vacc_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from . import views
urlpatterns = [
    path('', views.home, name='home'),
    path('register/parent/', views.register_parent, name='register_parent'),
    path('register/hospital/', views.register_hospital, name='register_hospital'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/hospital/', views.hospital_dashboard, name='hospital_dashboard'),
    path('dashboard/parent/', views.parent_dashboard, name='parent_dashboard'),
    path('dashboard/parent/profile/', views.parent_profile_update, name='parent_profile_update'),
    path('dashboard/parent/children/add/', views.child_add, name='child_add'),
    path('dashboard/parent/children/<int:child_id>/vaccinations/add/', views.vaccination_add, name='vaccination_add'),
    path('dashboard/parent/vaccinations/<int:vaccination_id>/complete/', views.vaccination_mark_completed, name='vaccination_mark_completed'),
]
