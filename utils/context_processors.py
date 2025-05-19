"""
Context processors for Django templates
"""
from utils.firebase_config import get_firebase_config

def firebase_config(request):
    """
    Provide Firebase configuration for templates
    """
    # Get config as a Python dict
    config = get_firebase_config()
    
    return {
        'firebase_config': config
    } 