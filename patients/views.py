import datetime
from django.shortcuts import render
from services.cosmosdb_helper import get_patients_page 

def view_patients(request):
    page_size = 10
    page = int(request.GET.get('page', 1)) 

    patients, has_more = get_patients_page(page_size=page_size, page=page)

    for patient in patients:
        dob = patient.get("date_of_birth")
        if dob:
            try:
                patient["date_of_birth"] = datetime.datetime.fromisoformat(dob).date()
            except ValueError:
                patient["date_of_birth"] = None

    context = {
        'patients': patients,
        'has_more': has_more,
        'page': page 
    }

    return render(request, 'patients/view_patients.html', context)
