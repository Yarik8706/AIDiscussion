"""
Firebase configuration for authentication and database
"""
import os
import firebase_admin
from firebase_admin import credentials, auth, firestore
import pyrebase
from django.conf import settings

# Initialize Firebase Admin SDK (for Firestore and server-side auth)
def initialize_firebase_admin():
    """Initialize Firebase Admin SDK with credentials"""
    try:
        if not firebase_admin._apps:
            # For local development, use a service account key json file
            if os.path.exists(os.path.join(settings.BASE_DIR, 'firebase-service-account.json')):
                cred = credentials.Certificate(os.path.join(settings.BASE_DIR, 'firebase-service-account.json'))
                firebase_admin.initialize_app(cred)
            # For production, use environment variables
            elif os.environ.get('FIREBASE_SERVICE_ACCOUNT'):
                import json
                service_account_info = json.loads(os.environ.get('FIREBASE_SERVICE_ACCOUNT'))
                cred = credentials.Certificate(service_account_info)
                firebase_admin.initialize_app(cred)
            else:
                raise ValueError("Firebase credentials not found")
    except Exception as e:
        print(f"Firebase Admin SDK initialization error: {e}")

# Initialize Pyrebase (for client-side auth)
def get_firebase_config():
    """Get Firebase configuration from environment variables"""
    config = {
        "apiKey": os.environ.get('FIREBASE_API_KEY'),
        "authDomain": os.environ.get('FIREBASE_AUTH_DOMAIN'),
        "projectId": os.environ.get('FIREBASE_PROJECT_ID'),
        "storageBucket": os.environ.get('FIREBASE_STORAGE_BUCKET'),
        "messagingSenderId": os.environ.get('FIREBASE_MESSAGING_SENDER_ID'),
        "appId": os.environ.get('FIREBASE_APP_ID'),
    }
    return config

def get_firebase_client():
    """Get Firebase client instance"""
    config = get_firebase_config()
    firebase = pyrebase.initialize_app(config)
    return firebase

def get_firestore_db():
    """Get Firestore database instance"""
    initialize_firebase_admin()
    return firestore.client() 