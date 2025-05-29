"""
Firebase configuration for authentication and database
"""
import os
import json
import logging
from pathlib import Path
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, auth, firestore
import empyrebase
from django.conf import settings

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Firebase Admin SDK (for Firestore and server-side auth)
def initialize_firebase_admin():
    """
    Initialize Firebase Admin SDK using the service account credential file
    """
    # Check if already initialized
    if len(firebase_admin._apps) > 0:
        return

    try:
        # Try to load service account from file
        service_account_path = os.path.join(settings.BASE_DIR, 'firebase-service-account.json')
        
        if os.path.exists(service_account_path):
            cred = credentials.Certificate(service_account_path)
            firebase_admin.initialize_app(cred)
            logger.info("Firebase Admin SDK initialized with service account file")
        else:
            # Fall back to environment variables
            logger.warning("Service account file not found, using default credentials")
            firebase_admin.initialize_app()
            
    except Exception as e:
        logger.error(f"Error initializing Firebase Admin SDK: {e}")
        raise

# Cache for Firebase configuration
_firebase_config = None

def get_firebase_config():
    """
    Get Firebase configuration from environment variables
    
    Returns:
        dict: Firebase configuration for client-side use
    """
    global _firebase_config
    
    # Return cached config if available
    if _firebase_config is not None:
        return _firebase_config
    
    # Load config from environment variables
    _firebase_config = {
        "apiKey": os.getenv("FIREBASE_API_KEY", ""),
        "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN", ""),
        "projectId": os.getenv("FIREBASE_PROJECT_ID", ""),
        "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET", ""),
        "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID", ""),
        "appId": os.getenv("FIREBASE_APP_ID", ""),
        "databaseURL": os.getenv("FIREBASE_DATABASE_URL", "")
    }
    
    # Try to load project ID from service account file if not in environment
    if not _firebase_config["projectId"]:
        try:
            service_account_path = os.path.join(settings.BASE_DIR, 'firebase-service-account.json')
            if os.path.exists(service_account_path):
                with open(service_account_path, 'r') as f:
                    service_account = json.load(f)
                    _firebase_config["projectId"] = service_account.get("project_id", "")
        except Exception as e:
            logger.error(f"Error loading project ID from service account: {e}")
    
    # Log warning if essential config is missing
    if not _firebase_config["apiKey"] or not _firebase_config["projectId"]:
        logger.warning("Firebase configuration is incomplete. Check your environment variables or service account.")
    
    return _firebase_config

# Get Pyrebase client instance
def get_firebase_client():
    """
    Get Firebase client instance for client-side operations
    
    Returns:
        pyrebase.Firebase: Initialized Firebase client
    """
    try:
        config = get_firebase_config()
        firebase = empyrebase.initialize_app(config)
        return firebase
    except Exception as e:
        logger.error(f"Error initializing Firebase client: {e}")
        raise

# Cache for firestore client
_firestore_db = None

def get_firestore_db():
    """
    Get a Firestore database instance
    
    Returns:
        firestore.Client: Firestore client instance
    """
    global _firestore_db
    
    if _firestore_db is not None:
        return _firestore_db
    
    if len(firebase_admin._apps) == 0:
        initialize_firebase_admin()
    
    try:
        _firestore_db = firestore.client()
        return _firestore_db
    except Exception as e:
        logger.error(f"Error getting Firestore client: {e}")
        raise

# Firestore operation helper functions
def save_discussion_to_firestore(user_id, discussion_data):
    """
    Save a discussion to Firestore
    
    Args:
        user_id (str): Firebase user ID
        discussion_data (dict): Discussion data to save
        
    Returns:
        bool: True if successful
    """
    try:
        db = get_firestore_db()
        db.collection('users').document(user_id).collection('discussions').document(str(discussion_data['id'])).set(discussion_data)
        return True
    except Exception as e:
        logger.error(f"Error saving discussion to Firestore: {e}")
        return False

def get_user_discussions_from_firestore(user_id):
    """
    Get all discussions for a user from Firestore
    
    Args:
        user_id (str): Firebase user ID
        
    Returns:
        list: List of discussion dictionaries
    """
    try:
        db = get_firestore_db()
        discussions_ref = db.collection('users').document(user_id).collection('discussions')
        docs = discussions_ref.order_by('created_at', direction=firestore.Query.DESCENDING).stream()
        return [doc.to_dict() for doc in docs]
    except Exception as e:
        logger.error(f"Error getting discussions from Firestore: {e}")
        return []

def delete_discussion_from_firestore(user_id, discussion_id):
    """
    Delete a discussion and its messages from Firestore
    
    Args:
        user_id (str): Firebase user ID
        discussion_id (str): Discussion ID to delete
        
    Returns:
        int: Number of deleted messages
    """
    try:
        db = get_firestore_db()
        
        # Delete the discussion document
        db.collection('users').document(user_id).collection('discussions').document(str(discussion_id)).delete()
        
        # Delete all messages in the discussion
        messages_ref = db.collection('users').document(user_id).collection('discussions') \
                      .document(str(discussion_id)).collection('messages')
        
        # Delete in batches (Firestore doesn't support collection deletion)
        batch_size = 500
        docs = messages_ref.limit(batch_size).stream()
        deleted = 0
        
        for doc in docs:
            doc.reference.delete()
            deleted += 1
            
        return deleted
    except Exception as e:
        logger.error(f"Error deleting discussion from Firestore: {e}")
        return 0

def save_message_to_firestore(user_id, discussion_id, message_data):
    """
    Save a message to Firestore
    
    Args:
        user_id (str): Firebase user ID
        discussion_id (str): Discussion ID
        message_data (dict): Message data to save
        
    Returns:
        bool: True if successful
    """
    try:
        db = get_firestore_db()
        db.collection('users').document(user_id).collection('discussions').document(discussion_id).collection('messages').add(message_data)
        return True
    except Exception as e:
        logger.error(f"Error saving message to Firestore: {e}")
        return False

def get_discussion_messages_from_firestore(user_id, discussion_id):
    """
    Get all messages for a discussion from Firestore
    
    Args:
        user_id (str): Firebase user ID
        discussion_id (str): Discussion ID
        
    Returns:
        list: List of message dictionaries
    """
    try:
        db = get_firestore_db()
        messages_ref = db.collection('users').document(user_id).collection('discussions') \
                      .document(str(discussion_id)).collection('messages')
        docs = messages_ref.order_by('created_at').stream()
        return [doc.to_dict() for doc in docs]
    except Exception as e:
        logger.error(f"Error getting messages from Firestore: {e}")
        return []

def update_discussion_in_firestore(user_id, discussion_id, updates):
    """
    Update a discussion in Firestore
    
    Args:
        user_id (str): Firebase user ID
        discussion_id (str): Discussion ID
        updates (dict): Fields to update
        
    Returns:
        bool: True if successful
    """
    try:
        db = get_firestore_db()
        db.collection('users').document(user_id).collection('discussions').document(discussion_id).update(updates)
        return True
    except Exception as e:
        logger.error(f"Error updating discussion in Firestore: {e}")
        return False 