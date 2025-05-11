import json
import os
import logging
from discusser import Disscuser

GENERAL_CONTEXT_PATH = 'general_context.txt'

def load_participants(settings_path='discusser_settings.json'):
    logging.info(f"Загрузка настроек участников из {settings_path}")
    # Читаем общий контекст
    try:
        with open(GENERAL_CONTEXT_PATH, 'r', encoding='utf-8') as gf:
            general_context = gf.read().strip()
    except Exception as e:
        logging.error(f"Ошибка при чтении общего контекста: {e}")
        general_context = ''
    with open(settings_path, 'r', encoding='utf-8') as f:
        settings = json.load(f)
    participants = []
    for net in settings['settings']:
        api_key = os.getenv(net['env_token_name'])
        if not api_key:
            logging.error(f"Токен для {net['name']} не найден в переменных окружения: {net['env_token_name']}")
            continue
        try:
            with open(net['character_path'], 'r', encoding='utf-8') as cf:
                context = cf.read().strip()
            full_context = context + '\n' + general_context 
            participants.append(Disscuser(api_key, full_context, net['name']))
            logging.info(f"Загружен участник: {net['name']} ({net['character_path']})")
        except Exception as e:
            logging.error(f"Ошибка при загрузке характера для {net['name']}: {e}")
    return participants 