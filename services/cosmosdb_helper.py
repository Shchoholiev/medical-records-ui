from datetime import datetime
import os
import logging
import uuid
from azure.cosmos import CosmosClient, exceptions
from passlib.context import CryptContext

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Configuration
CONNECTION_STRING = os.getenv("COSMOS_CONNECTION_STRING")
DATABASE_NAME = "medical-records"
PATIENTS_CONTAINER_NAME = "patients"
MEDICAL_RECORDS_CONTAINER_NAME = "medical_records"
USERS_CONTAINER_NAME = "users"
HEALTH_NOTIFICATIONS_CONTAINER_NAME = "health_notifications"

# Initialize Cosmos DB client and containers
logger.info("Initializing Cosmos DB client and containers.")
client = CosmosClient.from_connection_string(CONNECTION_STRING)
database = client.get_database_client(DATABASE_NAME)
patients_container = database.get_container_client(PATIENTS_CONTAINER_NAME)
medical_records_container = database.get_container_client(MEDICAL_RECORDS_CONTAINER_NAME)
users_container = database.get_container_client(USERS_CONTAINER_NAME)
health_notifications_container = database.get_container_client(HEALTH_NOTIFICATIONS_CONTAINER_NAME)
session_container = database.get_container_client("sessions")

def get_patients_page(page_size=10, page=1):
    logger.info(f"Fetching page {page} of patients, page size: {page_size}")
    try:
        query = "SELECT * FROM c"
        
        results = patients_container.query_items(
            query=query,
            enable_cross_partition_query=True,
            max_item_count=page * page_size
        )
        
        patients = list(results)[(page - 1) * page_size: page * page_size]
        
        has_more = len(patients) == page_size
        logger.info(f"Retrieved {len(patients)} patients for page {page}, has_more: {has_more}")

        return patients, has_more
    except exceptions.CosmosHttpResponseError as e:
        logger.error(f"Error querying patients for page {page}: {e}")
        return [], False

def get_patient_details(patient_id):
    logger.info(f"Fetching details for patient ID: {patient_id}")
    try:
        patient = patients_container.read_item(item=patient_id, partition_key=patient_id)
        
        if not patient:
            logger.error(f"No patient found with patient ID: {patient_id}")
            return None, None, None, None

        logger.info(f"Patient found: {patient.get('name')} with ID: {patient_id}")

        user_id = patient.get("user_id")
        
        if user_id:
            user = users_container.read_item(item=user_id, partition_key=user_id)
            if user:
                logger.info(f"User associated with patient ID {patient_id}: {user.get('email')}")
            else:
                logger.warning(f"No user found for user ID associated with patient ID: {patient_id}")
        else:
            user = None
            logger.warning(f"No user ID associated with patient ID: {patient_id}")

        patient_params = [{"name": "@patient_id", "value": patient_id}]
        medical_records_query = "SELECT * FROM c WHERE c.patient_id = @patient_id ORDER BY c.created_date_utc ASC"
        medical_records_results = medical_records_container.query_items(
            query=medical_records_query,
            parameters=patient_params,
            enable_cross_partition_query=True
        )
        medical_records = list(medical_records_results)
        logger.info(f"Found {len(medical_records)} medical records for patient ID: {patient_id}")

        user_params = [{"name": "@user_id", "value": user_id}]
        health_notifications_query = "SELECT * FROM c WHERE c.patient_id = @user_id"
        health_notifications_results = health_notifications_container.query_items(
            query=health_notifications_query,
            parameters=user_params,
            enable_cross_partition_query=True
        )
        health_notifications = list(health_notifications_results)
        logger.info(f"Found {len(health_notifications)} health notifications for patient ID: {patient_id}")

        return patient, user, medical_records, health_notifications
    except exceptions.CosmosHttpResponseError as e:
        logger.error(f"Error querying Cosmos DB for patient ID {patient_id}: {e}")
        return None, None, None, None
    
def create_user_and_patient(name, email, password, date_of_birth, sex, ever_married):
    user_id = str(uuid.uuid4())
    password_hash = pwd_context.hash(password) 
    
    user = {
        "id": user_id,
        "name": name,
        "email": email,
        "password_hash": password_hash,
        "roles": ["Patient"],
        "validator_id": ""
    }
    
    try:
        users_container.create_item(body=user)
        logger.info(f"User created with ID: {user_id}")
    except exceptions.CosmosHttpResponseError as e:
        logger.error(f"Failed to create user: {e}")
        return False

    patient_id = str(uuid.uuid4())
    patient = {
        "id": patient_id,
        "name": name,
        "date_of_birth": date_of_birth,
        "sex": sex,
        "ever_married": bool(ever_married),
        "user_id": user_id,
    }
    
    try:
        patients_container.create_item(body=patient)
        logger.info(f"Patient created with ID: {patient_id}, linked to user ID: {user_id}")
        return True
    except exceptions.CosmosHttpResponseError as e:
        logger.error(f"Failed to create patient: {e}")
        return False
    
def verify_user(email, password):
    """Verify user credentials by matching email and bcrypt-hashed password."""
    try:
        query = "SELECT * FROM c WHERE c.email = @email"
        params = [{"name": "@email", "value": email}]
        
        results = list(users_container.query_items(
            query=query,
            parameters=params,
            enable_cross_partition_query=True
        ))
        
        if results:
            user = results[0]
            if pwd_context.verify(password, user['password_hash']):
                return user
        return None
    except exceptions.CosmosHttpResponseError as e:
        logger.error(f"Error verifying user: {e}")
        return None

def get_session_data(session_id):
    try:
        session = session_container.read_item(item=session_id, partition_key=session_id)
        return session.get("data", {})
    except exceptions.CosmosResourceNotFoundError:
        return {}

def save_session_data(session_id, data):
    session_item = {
        "id": session_id,
        "data": data
    }
    session_container.upsert_item(session_item)

def get_patient_id_by_user_id(user_id):
    """
    Fetch the patient ID associated with the given user ID.
    """
    try:
        query = "SELECT * FROM c WHERE c.user_id = @user_id"
        parameters = [{"name": "@user_id", "value": user_id}]
        results = list(patients_container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))

        if results:
            return results[0]['id']
    except Exception as e:
        logger.error(f"Error retrieving patient ID for user ID {user_id}: {e}")
    
    return None

def update_patient_data(patient_id, patient_data, user_data):
    try:
        user_id = patient_data["user_id"]
        users_container.replace_item(item=user_id, body=user_data)
        logger.info(f"User {user_id} updated successfully.")

        patients_container.replace_item(item=patient_id, body=patient_data)
        logger.info(f"Patient {patient_id} updated successfully.")

        return True
    except Exception as e:
        logger.error(f"Error updating patient {patient_id} and user {user_id}: {e}")
        return False

def get_age_risk_data():
    """
    Retrieve patient data and their risk of stroke for analysis.

    :return: A list of dictionaries containing patient id, age, and stroke risk status.
    """
    try:
        result = []
        
        patients_query = "SELECT c.id, c.date_of_birth, c.user_id FROM c"
        patients = list(patients_container.query_items(
            query=patients_query, enable_cross_partition_query=True
        ))
        
        for patient in patients:
            dob = patient.get("date_of_birth")
            if dob:
                birth_date = datetime.fromisoformat(dob).date()
                age = (datetime.now().date() - birth_date).days // 365
            else:
                age = None  
            
            stroke_notification_query = """
                SELECT * FROM c WHERE c.patient_id = @user_id AND c.disease = 'Stroke'
            """
            params = [{"name": "@user_id", "value": patient["user_id"]}]
            notifications = list(health_notifications_container.query_items(
                query=stroke_notification_query, parameters=params, enable_cross_partition_query=True
            ))
            
            at_risk_for_stroke = bool(notifications)
            
            result.append({
                "patient_id": patient["id"],
                "age": age,
                "at_risk_for_stroke": at_risk_for_stroke
            })
        
        return result
    
    except Exception as e:
        logger.error(f"Error retrieving age and risk data: {e}")
        return []