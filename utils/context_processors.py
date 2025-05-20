"""
Context processors for Django templates
"""
import json
from django.conf import settings
from utils.firebase_config import get_firebase_config

def firebase_config(request):
    """
    Provide Firebase configuration for templates
    
    Returns a dictionary with:
    - firebase_config: Python dict with Firebase config
    - firebase_config_json: JSON string of Firebase config for direct use in JavaScript
    """
    # Get config as a Python dict
    config = get_firebase_config()
    
    # Also provide a JSON serialized version for direct use in templates
    config_json = json.dumps(config)
    
    return {
        'firebase_config': config,
        'firebase_config_json': config_json
    } 