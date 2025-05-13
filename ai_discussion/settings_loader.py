import json
import os
import logging
from django.conf import settings
from .discusser import Discusser

def get_general_context_path():
    return os.path.join(settings.BASE_DIR, 'general_context.txt')

def load_participants(settings_path=None):
    if settings_path is None:
        settings_path = os.path.join(settings.BASE_DIR, 'discusser_settings.json')
    
    logging.info(f"Загрузка настроек участников из {settings_path}")
    
    # Читаем общий контекст
    general_context_path = get_general_context_path()
    try:
        with open(general_context_path, 'r', encoding='utf-8') as gf:
            general_context = gf.read().strip()
    except Exception as e:
        logging.error(f"Ошибка при чтении общего контекста: {e}")
        general_context = ''
    
    with open(settings_path, 'r', encoding='utf-8') as f:
        settings_data = json.load(f)
    
    participants = []
    for net in settings_data['settings']:
        api_key = os.getenv(net['env_token_name'])
        if not api_key:
            logging.error(f"Токен для {net['name']} не найден в переменных окружения: {net['env_token_name']}")
            continue
        try:
            character_path = os.path.join(settings.BASE_DIR, net['character_path'])
            with open(character_path, 'r', encoding='utf-8') as cf:
                context = cf.read().strip()
            full_context = context + '\n' + general_context 
            participants.append(Discusser(api_key, full_context, net['name']))
            logging.info(f"Загружен участник: {net['name']} ({character_path})")
        except Exception as e:
            logging.error(f"Ошибка при загрузке характера для {net['name']}: {e}")
    
    return participants 