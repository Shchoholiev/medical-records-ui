# patients/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('view/', views.view_patients, name='view_patients'),
    path('patient/<str:patient_id>/', views.patient_user_details, name='patient_user_details'),
]
