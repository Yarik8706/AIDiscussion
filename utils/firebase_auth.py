"""
Firebase authentication middleware and decorators for Django

This module provides tools for authenticating users through Firebase in a Django application.
It includes a middleware for processing authentication tokens and a decorator for restricting
access to authenticated users only.
"""
import os
import json
import logging
from functools import wraps
from pathlib import Path

from django.http import JsonResponse
from django.conf import settings
from django.contrib.auth.models import User

import firebase_admin
from firebase_admin import auth, credentials

# Configure logging
logger = logging.getLogger(__name__)

# Initialize Firebase Admin SDK
def initialize_firebase_admin():
    """
    Initialize Firebase Admin SDK using the service account credentials file
    """
    if len(firebase_admin._apps) > 0:
        return

    try:
        # Get the path to the service account file
        service_account_path = os.path.join(settings.BASE_DIR, 'firebase-service-account.json')
        
        if os.path.exists(service_account_path):
            cred = credentials.Certificate(service_account_path)
            firebase_admin.initialize_app(cred)
            logger.info("Firebase Admin SDK initialized with service account file")
        else:
            # Fall back to environment variables if file not found
            firebase_admin.initialize_app()
            logger.info("Firebase Admin SDK initialized with default credentials")
    except Exception as e:
        logger.error(f"Failed to initialize Firebase Admin SDK: {e}")
        raise

# Initialize Firebase on module load
initialize_firebase_admin()

def verify_firebase_token(id_token):
    """
    Verify the Firebase ID token
    
    Args:
        id_token (str): The Firebase ID token to verify
        
    Returns:
        dict: The decoded token claims if valid
        None: If the token is invalid
    """
    if not id_token:
        return None
        
    try:
        # Verify the ID token while checking if the token has been revoked
        decoded_token = auth.verify_id_token(id_token, check_revoked=True)
        return decoded_token
    except auth.RevokedIdTokenError:
        # Token has been revoked
        logger.warning("The Firebase ID token has been revoked")
        return None
    except auth.ExpiredIdTokenError:
        # Token has expired
        logger.warning("The Firebase ID token has expired")
        return None
    except auth.InvalidIdTokenError:
        # Token is invalid
        logger.warning("The Firebase ID token is invalid")
        return None
    except Exception as e:
        # Other verification errors
        logger.error(f"Firebase token verification failed: {e}")
        return None

def get_firebase_user_data(uid):
    """
    Get additional user data from Firebase
    
    Args:
        uid (str): The Firebase user ID
        
    Returns:
        dict: User data from Firebase
        None: If an error occurs
    """
    try:
        user = auth.get_user(uid)
        return {
            'uid': user.uid,
            'email': user.email,
            'display_name': user.display_name,
            'phone_number': user.phone_number,
            'photo_url': user.photo_url,
            'email_verified': user.email_verified
        }
    except Exception as e:
        logger.error(f"Error getting Firebase user data: {e}")
        return None

def get_or_create_user(firebase_user):
    """
    Get or create a Django user from Firebase user data
    
    Args:
        firebase_user (dict): Firebase user data
        
    Returns:
        User: Django user object
        None: If user creation fails
    """
    try:
        # Try to get existing user by username (which is the Firebase UID)
        user, created = User.objects.get_or_create(username=firebase_user['uid'])
        
        if created:
            # Set user fields for a new user
            user.email = firebase_user.get('email', '')
            
            # Set display name as first name if available
            if firebase_user.get('display_name'):
                name_parts = firebase_user['display_name'].split(' ', 1)
                user.first_name = name_parts[0]
                if len(name_parts) > 1:
                    user.last_name = name_parts[1]
            
            # Save the user
            user.save()
            logger.info(f"Created new user from Firebase auth: {user.username}")
        
        return user
    except Exception as e:
        logger.error(f"Error creating/retrieving user from Firebase data: {e}")
        return None

class FirebaseAuthMiddleware:
    """
    Middleware to handle Firebase authentication
    Adds firebase_user_id to the request if the user is authenticated
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Default - not authenticated
        request.firebase_user_id = None
        request.firebase_user = None
        request.auth_source = None
        
        # Try to authenticate from Authorization header first (API requests)
        self._authenticate_from_header(request)
        
        # If not authenticated via header, try cookies (browser requests)
        if not request.firebase_user_id:
            self._authenticate_from_cookie(request)
            
        # Process the request
        response = self.get_response(request)
        return response
    
    def _authenticate_from_header(self, request):
        """Authenticate using the Authorization header"""
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            id_token = auth_header.split(' ')[1]
            self._process_token(request, id_token, 'header')
    
    def _authenticate_from_cookie(self, request):
        """Authenticate using cookies"""
        firebase_token = None
        
        # Look for the token in cookies (case-insensitive)
        for cookie_name, cookie_value in request.COOKIES.items():
            if cookie_name.lower() == 'firebasetoken':
                firebase_token = cookie_value
                break
        
        if firebase_token:
            self._process_token(request, firebase_token, 'cookie')
        else:
            request.auth_source = 'no_cookie_token'
    
    def _process_token(self, request, token, source):
        """Process and validate the authentication token"""
        decoded_token = verify_firebase_token(token)
        
        if decoded_token:
            # Get the Firebase user ID from the decoded token
            firebase_user_id = decoded_token.get('uid')
            
            if firebase_user_id:
                # Store the Firebase user ID in the request
                request.firebase_user_id = firebase_user_id
                
                # Get additional user data (optional)
                user_data = get_firebase_user_data(firebase_user_id)
                request.firebase_user = user_data
                
                # Set the authentication source
                request.auth_source = source
            else:
                request.auth_source = f'invalid_{source}_token_no_uid'
        else:
            request.auth_source = f'invalid_{source}_token'

def firebase_auth_required(view_func):
    """
    Decorator to require Firebase authentication for a view
    
    If the user is not authenticated, returns a 401 Unauthorized response
    """
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        if not request.firebase_user_id:
            return JsonResponse({
                'error': 'Unauthorized',
                'message': 'Authentication required'
            }, status=401)
        return view_func(request, *args, **kwargs)
    return wrapped_view 