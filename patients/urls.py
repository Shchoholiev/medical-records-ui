# patients/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('view/', views.view_patients, name='view_patients'),
    path('patient/<str:patient_id>/', views.patient_user_details, name='patient_user_details'),
    path('patients/<str:patient_id>/add_record/', views.create_medical_record_view, name='create_medical_record'),
    path('add/', views.add_patient_view, name='add_patient'),
    path('login/', views.login_view, name='login'), 
    path('logout/', views.logout_view, name='logout'),
    path('access_denied/', views.access_denied_view, name='access_denied')
]
