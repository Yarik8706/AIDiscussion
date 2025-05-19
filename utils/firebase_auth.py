"""
Firebase authentication middleware and decorators
"""
import json
from django.http import JsonResponse
from functools import wraps
from firebase_admin import auth
from .firebase_config import initialize_firebase_admin

# Initialize Firebase Admin SDK
initialize_firebase_admin()

def verify_firebase_token(id_token):
    """
    Verify the Firebase ID token
    Returns the Firebase user ID if valid, None otherwise
    """
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token.get('uid')
    except Exception as e:
        print(f"Token verification error: {e}")
        return None

class FirebaseAuthMiddleware:
    """
    Middleware to handle Firebase authentication
    Adds firebase_user_id to the request if the user is authenticated
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.firebase_user_id = None
        
        # 1. Check Authorization header (API requests)
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            id_token = auth_header.split(' ')[1]
            firebase_user_id = verify_firebase_token(id_token)
            if firebase_user_id:
                request.firebase_user_id = firebase_user_id
                # Add authentication debug info to request
                request.auth_source = 'header'
        
        # 2. If not authenticated yet, check cookies (for browser requests)
        if not request.firebase_user_id:
            # Try to find the token in cookies, case-insensitive
            firebase_token = None
            for cookie_name, cookie_value in request.COOKIES.items():
                if cookie_name.lower() == 'firebasetoken':
                    firebase_token = cookie_value
                    break
            
            if firebase_token:
                firebase_user_id = verify_firebase_token(firebase_token)
                if firebase_user_id:
                    request.firebase_user_id = firebase_user_id
                    # Add authentication debug info to request
                    request.auth_source = 'cookie'
                else:
                    # Token was present but invalid
                    request.auth_source = 'invalid_cookie_token'
            else:
                # No token found in cookies
                request.auth_source = 'no_cookie_token'
        
        response = self.get_response(request)
        return response

def firebase_auth_required(view_func):
    """
    Decorator to require Firebase authentication for a view
    """
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        if not request.firebase_user_id:
            return JsonResponse({'error': 'Unauthorized'}, status=401)
        return view_func(request, *args, **kwargs)
    return wrapped_view 