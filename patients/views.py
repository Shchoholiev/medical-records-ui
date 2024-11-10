from django.urls import reverse
import datetime
import logging
from django.shortcuts import redirect, render
from patients.decorators import login_required, role_required
from services.blockchain import create_medical_record
from services.cosmosdb_helper import create_user_and_patient, get_age_risk_data, get_patient_details, get_patient_id_by_user_id, get_patients_page, update_patient_data, verify_user 
from django.contrib import messages
import matplotlib.pyplot as plt
import io
import base64
from collections import defaultdict

logger = logging.getLogger(__name__)

@login_required
@role_required(['Doctor'])
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

@login_required
@role_required(['Patient', 'Doctor'])
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

@login_required
@role_required(['Doctor'])
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

@login_required
@role_required(['Doctor'])
def add_patient_view(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        password = request.POST.get("password")
        date_of_birth = request.POST.get("date_of_birth")
        sex = request.POST.get("sex")
        ever_married = request.POST.get("ever_married") == "on"  # Checkbox

        if create_user_and_patient(name, email, password, date_of_birth, sex, ever_married):
            return redirect('view_patients')  
        else:
            return render(request, 'patients/add_patient.html', {'error_message': "Failed to add patient. Please try again."})

    return render(request, 'patients/add_patient.html')

@login_required
@role_required(['Doctor'])
def update_patient_view(request, patient_id):
    patient, user, _, _ = get_patient_details(patient_id)

    if not patient or not user:
        messages.error(request, "Patient not found.")
        return redirect('view_patients')
    
    if patient.get("date_of_birth"):
        patient["date_of_birth"] = datetime.datetime.fromisoformat(patient["date_of_birth"]).strftime("%Y-%m-%d")

    if request.method == "POST":
        patient["name"] = request.POST.get("name", patient["name"])
        patient["date_of_birth"] = request.POST.get("date_of_birth", patient["date_of_birth"])
        patient["sex"] = request.POST.get("sex", patient["sex"])
        patient["ever_married"] = "ever_married" in request.POST

        user["name"] = request.POST.get("name", user["name"])
        user["email"] = request.POST.get("email", user["email"])

        if update_patient_data(patient_id, patient, user):
            messages.success(request, "Patient updated successfully.")
            return redirect('patient_user_details', patient_id=patient_id)
        else:
            messages.error(request, "Failed to update patient. Please try again.")

    context = {
        "patient": patient,
        "user": user
    }
    return render(request, "patients/update_patient.html", context)

def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        user = verify_user(email, password)
        
        if user:
            request.session['user_id'] = user['id']
            request.session['user_name'] = user['name']  
            request.session['user_roles'] = user['roles']  
            if "Patient" in user['roles']:
                patient_id = get_patient_id_by_user_id(user['id'])
                if patient_id:
                    return redirect('patient_user_details', patient_id=patient_id)
                
            return redirect('view_patients')
        else:
            messages.error(request, "Invalid email or password.")
            return render(request, 'patients/login.html')

    return render(request, 'patients/login.html')

def logout_view(request):
    request.session.clear()  
    return redirect('login')

def access_denied_view(request):
    return render(request, 'patients/access_denied.html')

@login_required
@role_required(['Doctor'])
def age_risk_distribution_view(request):
    # Step 1: Retrieve age and risk data from CosmosDB
    data = get_age_risk_data()
    
    # Step 2: Organize data into age groups and count stroke risk
    age_groups = {
        "0-18": 0,
        "19-30": 0,
        "31-40": 0,
        "41-50": 0,
        "51-60": 0,
        "61+": 0
    }
    risk_counts = defaultdict(int)

    for entry in data:
        age = entry["age"]
        at_risk = entry["at_risk_for_stroke"]
        
        if age is not None:
            if age <= 18:
                group = "0-18"
            elif age <= 30:
                group = "19-30"
            elif age <= 40:
                group = "31-40"
            elif age <= 50:
                group = "41-50"
            elif age <= 60:
                group = "51-60"
            else:
                group = "61+"
            
            age_groups[group] += 1
            if at_risk:
                risk_counts[group] += 1

    # Step 3: Prepare data for charting
    labels = list(age_groups.keys())
    total_counts = [age_groups[group] for group in labels]
    risk_counts_values = [risk_counts[group] for group in labels]
    
    # Step 4: Generate the chart
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(labels, total_counts, label="Total Patients", color='skyblue')
    ax.bar(labels, risk_counts_values, label="At Risk for Stroke", color='salmon')

    ax.set_xlabel("Age Group")
    ax.set_ylabel("Number of Patients")
    ax.set_title("Age-Based Disease Risk Distribution")
    ax.legend()

    # Step 5: Save plot to a PNG image in memory, then encode to base64
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    buffer.close()

    # Step 6: Pass the chart to the template
    return render(request, 'patients/age_risk_distribution.html', {"chart": image_base64})

def custom_page_not_found_view(request, exception):
    return redirect('login')