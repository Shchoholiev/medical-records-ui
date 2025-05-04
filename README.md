# medical-records-ui

A Django-based web application for managing medical records with role-based access, patient management, reporting, and integration with Cosmos DB and blockchain services.

## Table of Contents

- [Features](#features)
- [Stack](#stack)
- [Installation](#installation)
  - [Prerequisites](#prerequisites)
  - [Setup Instructions](#setup-instructions)
- [Configuration](#configuration)

## Features

- User login and role-based access control (Doctor, Patient)
- Patient management: add, view, update patient details
- Medical records creation for patients with multiple record types
- Pagination support for patient listing
- Age-based disease risk distribution reporting with visual charts
- Integration with Azure Cosmos DB for data storage
- Integration with blockchain services for medical record verification
- Custom session management middleware using Cosmos DB
- Tailwind CSS for modern responsive UI design

## Stack

- Python 3.12
- Django
- Azure Cosmos DB for NoSQL database storage

## Installation

### Prerequisites

- Python 3.12 or newer installed on your system
- Azure Cosmos DB account with Cosmos connection string
- Access credentials for the blockchain API service

### Setup Instructions

1. Clone the repository:
   ```bash
   git clone https://github.com/Shchoholiev/medical-records-ui.git
   cd medical-records-ui
   ```

2. (Optional) Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   ```

3. Install required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Prepare environment variables as described in the [Configuration](#configuration) section.

5. Apply any necessary database migrations (if applicable):
   ```bash
   python manage.py migrate
   ```

6. Run the development server:
   ```bash
   python manage.py runserver
   ```
   or use Gunicorn for production:
   ```bash
   gunicorn medicalrecords.wsgi:application --bind 0.0.0.0:8000
   ```

7. Access the application in your browser at http://localhost:8000/patients/login/

## Configuration

Create a `.env.local` file in the project root directory with the following environment variables set:

```dotenv
# Azure Cosmos DB connection string
COSMOS_CONNECTION_STRING=<your-cosmos-db-connection-string>

# Blockchain API credentials and base URL
BLOCKCHAIN_API_BASE_URL=<your-blockchain-api-base-url>
BLOCKCHAIN_API_USERNAME=<your-blockchain-api-username>
BLOCKCHAIN_API_PASSWORD=<your-blockchain-api-password>
```

- Replace `<your-cosmos-db-connection-string>` with your Azure Cosmos DB connection string.
- Replace `<your-blockchain-api-base-url>`, `<your-blockchain-api-username>`, and `<your-blockchain-api-password>` with credentials for the blockchain API authentication.

Additional settings:
- To change allowed hosts or debug mode, edit `medicalrecords/settings.py` accordingly.
- Static files and deployment configurations can be customized as needed.
