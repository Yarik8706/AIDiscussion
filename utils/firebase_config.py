"""
Firebase configuration for authentication and database
"""
import os
import json
from pathlib import Path
import firebase_admin
from firebase_admin import credentials, auth, firestore
import pyrebase
from django.conf import settings

# Initialize Firebase Admin SDK (for Firestore and server-side auth)
def initialize_firebase_admin():
    """
    Initialize Firebase Admin SDK
    """
    # Check if already initialized
    if len(firebase_admin._apps) > 0:
        return

    # Try to load from service account file first
    if os.path.exists('firebase-service-account.json'):
        cred = credentials.Certificate('firebase-service-account.json')
        firebase_admin.initialize_app(cred)
    else:
        # Otherwise use environment variables
        firebase_admin.initialize_app()

# Initialize Pyrebase (for client-side auth)
def get_firebase_config():
    """Get Firebase configuration from environment variables"""
    config = {
        "apiKey": "AIzaSyAGGqYx0DrkoGdD3foKAdEjyF_amkFcH-Q",  # Direct hardcoding for debugging
        "authDomain": "aidiscussion-533c1.firebaseapp.com",
        "projectId": "aidiscussion-533c1",
        "storageBucket": "aidiscussion-533c1.appspot.com",  # Corrected bucket name
        "messagingSenderId": "968757275141",
        "appId": "1:968757275141:web:7aff9f40b9e41d3bcb4a6c"
    }
    return config

# Get a formatted config for template contexts
def get_firebase_config_for_template():
    """Get Firebase configuration formatted for templates"""
    config = get_firebase_config()
    return json.dumps(config)

def get_firebase_client():
    """Get Firebase client instance"""
    config = get_firebase_config()
    firebase = pyrebase.initialize_app(config)
    return firebase

# Cache for firestore client
_firestore_db = None

def get_firestore_db():
    """Get a Firestore database instance"""
    if len(firebase_admin._apps) == 0:
        initialize_firebase_admin()
    return firestore.client()

# Discussion operations for Firestore
def save_discussion_to_firestore(user_id, discussion_data):
    """Save a discussion to Firestore"""
    db = get_firestore_db()
    db.collection('users').document(user_id).collection('discussions').document(str(discussion_data['id'])).set(discussion_data)
    return True

def get_user_discussions_from_firestore(user_id):
    """Get all discussions for a user from Firestore"""
    db = get_firestore_db()
    discussions_ref = db.collection('users').document(user_id).collection('discussions')
    docs = discussions_ref.order_by('created_at', direction=firestore.Query.DESCENDING).stream()
    return [doc.to_dict() for doc in docs]

def delete_discussion_from_firestore(user_id, discussion_id):
    """Delete a discussion from Firestore"""
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
        
    # If we have deleted all documents, we're done
    return deleted

def save_message_to_firestore(user_id, discussion_id, message_data):
    """Save a message to Firestore"""
    db = get_firestore_db()
    db.collection('users').document(user_id).collection('discussions').document(discussion_id).collection('messages').add(message_data)
    return True

def get_discussion_messages_from_firestore(user_id, discussion_id):
    """Get all messages for a discussion from Firestore"""
    db = get_firestore_db()
    messages_ref = db.collection('users').document(user_id).collection('discussions') \
                    .document(str(discussion_id)).collection('messages')
    docs = messages_ref.order_by('created_at').stream()
    return [doc.to_dict() for doc in docs]

def update_discussion_in_firestore(user_id, discussion_id, updates):
    """Update a discussion in Firestore"""
    db = get_firestore_db()
    db.collection('users').document(user_id).collection('discussions').document(discussion_id).update(updates)
    return True 