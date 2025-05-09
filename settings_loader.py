import json
import os
import logging
from discusser import Disscuser

def load_participants(settings_path='discusser_settings.json'):
    logging.info(f"Загрузка настроек участников из {settings_path}")
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
            participants.append(Disscuser(api_key, context, net['name']))
            logging.info(f"Загружен участник: {net['name']} ({net['character_path']})")
        except Exception as e:
            logging.error(f"Ошибка при загрузке характера для {net['name']}: {e}")
    return participants 