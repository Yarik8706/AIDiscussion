import os
import logging
import json
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from dotenv import load_dotenv
import asyncio
from settings_loader import load_participants
from discussion import run_discussion

# Загрузка переменных из .env
load_dotenv()

# Загрузка настроек нейросети
with open('discusser_settings.json', 'r', encoding='utf-8') as f:
    settings = json.load(f)
network = settings['settings'][0]  # используем первую нейросеть

# Получаем токен из .env
GENAI_API_KEY = os.getenv(network['env_token_name'])
# Читаем характер из txt-файла
with open(network['character_path'], 'r', encoding='utf-8') as f:
    GENAI_CONTEXT = f.read().strip()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_TOKEN')

logging.basicConfig(level=logging.INFO)

# Инициализация клиентов
bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

participants = None

@dp.message(Command("start"))
async def cmd_start(message: Message):
    logging.info(f"Пользователь {message.from_user.id} начал сессию.")
    await message.answer("Привет! Задай вопрос для обсуждения.")

@dp.message()
async def handle_message(message: Message):
    global participants
    if participants is None:
        participants = load_participants()
    user_text = message.text
    logging.info(f"Получен вопрос от пользователя {message.from_user.id}: {user_text}")
    await message.answer("Вопрос принят. Обсуждение начинается...")

    async def send_to_chat(msg):
        max_len = 4096
        for i in range(0, len(msg), max_len):
            await message.answer(msg[i:i+max_len], parse_mode="HTML")

    summary = await run_discussion(participants, user_text, send_callback=send_to_chat)
    summary_text = "\n<b>Итоговый вывод:</b>\n" + str(summary)
    # Telegram max message length is 4096 chars
    max_len = 4096
    for i in range(0, len(summary_text), max_len):
        await message.answer(summary_text[i:i+max_len], parse_mode="HTML")

if __name__ == "__main__":
    async def main():
        logging.info("Запуск Telegram-бота...")
        await dp.start_polling(bot)
    asyncio.run(main()) 