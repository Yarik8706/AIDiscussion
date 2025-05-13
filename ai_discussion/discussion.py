from .discusser import Discusser    
import asyncio
import json
import os
import logging
import re

def strip_markdown(text):
    # Удалить markdown-форматирование: **, *, _, `, >, #, ~~, и т.п.
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # **bold**
    text = re.sub(r'\*([^*]+)\*', r'\1', text)        # *italic*
    text = re.sub(r'__([^_]+)__', r'\1', text)          # __bold__
    text = re.sub(r'_([^_]+)_', r'\1', text)            # _italic_
    text = re.sub(r'`([^`]+)`', r'\1', text)            # `code`
    text = re.sub(r'~~([^~]+)~~', r'\1', text)          # ~~strikethrough~~
    text = re.sub(r'^>\s?', '', text, flags=re.MULTILINE) # > quote
    text = re.sub(r'^#+\s?', '', text, flags=re.MULTILINE) # # heading
    text = re.sub(r'\[(.*?)\]\((.*?)\)', r'\1', text) # [text](url)
    return text

async def run_discussion(participants, question: str, max_rounds: int = 50, send_callback=None):
    logging.info(f"Начало обсуждения: {question}")
    discussion_history = [f"Вопрос пользователя: {question}. Вы должны ответить на заданную тему за 150 сообщений. Контролируйте ваше обсуждение, чтобы прийти к общему ответу на тему за данной количеством сообщений."]
    consensus = False
    round_num = 0
    while not consensus and round_num < max_rounds:
        round_num += 1
        logging.info(f"Раунд {round_num}")
        for participant in participants:
            response = await participant.ask(discussion_history)
            response = strip_markdown(response)
            message = f"<b>{participant.name}</b>: {response}"
            discussion_history.append(message)
            if send_callback:
                await send_callback(message)
        # Проверка консенсуса
        consensus_answers = []
        for participant in participants:
            consensus_prompt = "Считаете ли вы диалог законченным и не требующим продолжения, а тему разговора разрешенной? Ответьте только ДА или НЕТ."
            logging.info(f"Проверка консенсуса: {consensus_prompt}")
            response = await participant.ask_without_humanization(consensus_prompt, discussion_history)
            response = strip_markdown(response)
            consensus_answers.append(response.strip().upper())
        # Завершить, если все ответили ДА
        yes_count = sum(ans.startswith('ДА') for ans in consensus_answers)
        if yes_count == len(participants):
            consensus = True
    logging.info("\n".join(discussion_history))        
    # Итоговый вывод
    summary = None
    try:
        summary_participant = Discusser(os.getenv('GENAI_API_KEY_1'), "Ты ии который максимально рационально рассуждаешь", "ИИ")
        summary_prompt = "Вот весь диалог между ИИ. Сделай краткий, структурированный и читабельный вывод для пользователя, к которому пришли участники обсуждения."
        summary = await summary_participant.ask_without_humanization(summary_prompt, discussion_history)
        if isinstance(summary, (tuple, list)):
            summary = "\n".join(str(x) for x in summary if isinstance(x, str))
        summary = str(summary).replace("('[", "").replace("]')", "").replace("('[", "").replace("]')", "").strip()
        summary = strip_markdown(summary)
    except Exception as e:
        summary = f"Ошибка при получении вывода: {e}"
    logging.info("Обсуждение завершено")
    return summary, discussion_history 