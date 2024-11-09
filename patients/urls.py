# patients/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('view/', views.view_patients, name='view_patients'),
]
