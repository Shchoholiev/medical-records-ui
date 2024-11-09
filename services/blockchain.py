import os
import requests
import logging

logger = logging.getLogger(__name__)

API_BASE_URL = os.getenv("BLOCKCHAIN_API_BASE_URL")

def authenticate():
    username = os.getenv("BLOCKCHAIN_API_USERNAME")
    password = os.getenv("BLOCKCHAIN_API_PASSWORD")
    
    if not username or not password:
        logger.error("Blockchain API username or password not set in environment variables.")
        return None

    auth_url = f"{API_BASE_URL}/auth/login"
    auth_payload = {
        "username": username,
        "password": password
    }
    
    try:
        response = requests.post(auth_url, json=auth_payload)
        
        if response.status_code == 200:
            access_token = response.json().get("access_token")
            if access_token:
                logger.info("Authentication successful. Access token retrieved.")
                return access_token
            else:
                logger.error("Authentication response did not contain an access token.")
                return None
        else:
            logger.error("Authentication failed. Status code: %s", response.status_code)
            return None
    except requests.RequestException as e:
        logger.error("An error occurred during authentication: %s", e)
        return None

import os
import requests
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Base API URL from environment variable
API_BASE_URL = os.getenv("BLOCKCHAIN_API_BASE_URL")

def authenticate():
    username = os.getenv("BLOCKCHAIN_API_USERNAME")
    password = os.getenv("BLOCKCHAIN_API_PASSWORD")
    
    if not username or not password:
        logger.error("Blockchain API username or password not set in environment variables.")
        return None

    auth_url = f"{API_BASE_URL}/auth/login"
    auth_payload = {
        "username": username,
        "password": password
    }
    
    try:
        response = requests.post(auth_url, json=auth_payload)
        
        if response.status_code == 200:
            access_token = response.json().get("access_token")
            if access_token:
                logger.info("Authentication successful. Access token retrieved.")
                return access_token
            else:
                logger.error("Authentication response did not contain an access token.")
                return None
        else:
            logger.error("Authentication failed. Status code: %s", response.status_code)
            return None
    except requests.RequestException as e:
        logger.error("An error occurred during authentication: %s", e)
        return None

def create_medical_record(patient_id, record_type, **data):
    access_token = authenticate()
    if not access_token:
        logger.error("Could not retrieve access token. Medical record creation aborted.")
        return False

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    record_payload = {
        "patient_id": patient_id,
        "type": record_type,
        **data  
    }
    
    try:
        create_url = f"{API_BASE_URL}/blocks"
        response = requests.post(create_url, json=record_payload, headers=headers)
        
        if response.status_code == 200:
            logger.info("Medical record created successfully on the blockchain.")
            return True
        else:
            logger.error("Failed to create medical record. Status code: %s, Response: %s", response.status_code, response.json())
            return False
    except requests.RequestException as e:
        logger.error("An error occurred while creating the medical record: %s", e)
        return False
