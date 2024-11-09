from django.urls import reverse
import datetime
import logging
from django.shortcuts import redirect, render
from services.blockchain import create_medical_record
from services.cosmosdb_helper import get_patient_details, get_patients_page 

# Set up a logger for this module
logger = logging.getLogger(__name__)

def view_patients(request):
    page_size = 10
    page = int(request.GET.get('page', 1))
    
    logger.info(f"Fetching patients list, page: {page}, page size: {page_size}")
    
    patients, has_more = get_patients_page(page_size=page_size, page=page)
    logger.info(f"Retrieved {len(patients)} patients for page {page}")

    for patient in patients:
        dob = patient.get("date_of_birth")
        patient["date_of_birth"] = datetime.datetime.fromisoformat(dob).date()

    context = {
        'patients': patients,
        'has_more': has_more,
        'page': page 
    }

    logger.info(f"Rendering view_patients.html with {len(patients)} patients for page {page}")
    return render(request, 'patients/view_patients.html', context)

def patient_user_details(request, patient_id):
    logger.info(f"Fetching details for patient with ID: {patient_id}")
    
    patient, user, medical_records, health_notifications = get_patient_details(patient_id)
    
    if not patient:
        logger.warning(f"No patient found with ID: {patient_id}")
        return render(request, '404.html', status=404)

    dob = patient.get("date_of_birth")
    patient["date_of_birth"] = datetime.datetime.fromisoformat(dob).date()

    logger.info(f"Patient found: {patient.get('name')} with ID: {patient_id}")

    record_type_names = {
        "PhysicalExam": "Physical Exam",
        "BloodWork": "Blood Work",
        "BloodPressure": "Blood Pressure",
        "DiseaseHistory": "Disease History",
    }

    for record in medical_records:
        record["display_name"] = record_type_names.get(record["type"], record["type"])


    context = {
        'patient': patient,
        'user': user,
        'medical_records': medical_records,
        'health_notifications': health_notifications
    }

    logger.info(f"Rendering patient_user_details.html for patient ID: {patient_id}")
    return render(request, 'patients/patient_user_details.html', context)

def create_medical_record_view(request, patient_id):
    if request.method == "POST":
        record_type = request.POST.get("record_type")
        
        data = {}
        if record_type == "PhysicalExam":
            data = {
                "work_type": request.POST.get("work_type"),
                "residency_type": request.POST.get("residency_type"),
                "height": request.POST.get("height"),
                "weight": request.POST.get("weight"),
                "smoking_status": request.POST.get("smoking_status"),
            }
        elif record_type == "BloodPressure":
            data = {
                "systolic_pressure": request.POST.get("systolic_pressure"),
                "diastolic_pressure": request.POST.get("diastolic_pressure"),
            }
        elif record_type == "BloodWork":
            data = {
                "glucose_level": request.POST.get("glucose_level"),
            }
        elif record_type == "DiseaseHistory":
            data = {
                "disease_type": request.POST.get("disease_type"),
            }
        
        if create_medical_record(patient_id, record_type, **data):
            logger.info(f"Medical record created successfully for patient ID {patient_id}.")
            return redirect(reverse('patient_user_details', args=[patient_id]))
        else:
            logger.error(f"Failed to create medical record for patient ID {patient_id}.")
            return render(request, 'patients/create_medical_record.html', {
                'error_message': "Failed to create medical record. Please try again.",
                'patient_id': patient_id,
            })

    return render(request, 'patients/create_medical_record.html', {'patient_id': patient_id})
