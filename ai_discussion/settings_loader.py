import json
import os
import logging
from typing import Dict, List, Any
from django.conf import settings

from .discusser_base import BaseDiscusser
from .discusser_factory import DiscusserFactory

def get_general_context_path():
    """Get the path to the general context file."""
    return os.path.join(settings.BASE_DIR, 'general_context.txt')

async def load_static_participants():
    """Load static participants from settings without initializing them.
    
    This is used to get information about available participants without
    creating the actual discusser objects.
    
    Returns:
        List of initialized discusser participants
    """
    settings_path = os.path.join(settings.BASE_DIR, 'discusser_settings.json')
    
    logging.info(f"Загрузка статических участников из {settings_path}")
    
    # Read the settings file
    with open(settings_path, 'r', encoding='utf-8') as f:
        settings_data = json.load(f)
    
    # Create participants
    participants = await DiscusserFactory.create_discussers_from_settings(settings_data)
    
    # Add ID attribute to participants based on index
    for i, participant in enumerate(participants):
        setattr(participant, 'id', str(i+1))
    
    logging.info(f"Загружено {len(participants)} статических участников")
    return participants

async def load_participants():
    """Load and initialize discusser participants from settings.
    
    Args:
        settings_path: Optional path to the settings JSON file
        
    Returns:
        List of initialized discusser participants
    """
    settings_path = os.path.join(settings.BASE_DIR, 'discusser_settings.json')
    
    logging.info(f"Загрузка настроек участников из {settings_path}")
    
    # Prepare settings data with general context path
    general_context_path = get_general_context_path()
    
    # Read the settings file
    with open(settings_path, 'r', encoding='utf-8') as f:
        settings_data = json.load(f)
    
    # Add general context path to settings
    settings_data['general_context_path'] = general_context_path
    
    # Create discussers using the factory
    participants = await DiscusserFactory.create_discussers_from_settings(settings_data)
    
    # Add ID attribute to participants based on index
    for i, participant in enumerate(participants):
        setattr(participant, 'id', str(i+1))
    
    logging.info(f"Загружено {len(participants)} участников обсуждения")
    return participants 