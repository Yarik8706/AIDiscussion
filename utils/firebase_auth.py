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
        auth_header = request.headers.get('Authorization')
        
        if auth_header and auth_header.startswith('Bearer '):
            id_token = auth_header.split(' ')[1]
            firebase_user_id = verify_firebase_token(id_token)
            if firebase_user_id:
                request.firebase_user_id = firebase_user_id
        
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