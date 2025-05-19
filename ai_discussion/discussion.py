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

async def run_discussion(participants, question: str, max_rounds: int = 50, send_callback=None, discussion_id=None, check_if_stopped=None):
    logging.info(f"Начало обсуждения: {question}")
    discussion_history = [f"Вопрос пользователя: {question}. Вы должны ответить на заданную тему за 150 сообщений. Контролируйте ваше обсуждение, чтобы прийти к общему ответу на тему за данной количеством сообщений."]
    consensus = False
    round_num = 0
    is_stopped = False
    
    while not consensus and round_num < max_rounds and not is_stopped:
        round_num += 1
        logging.info(f"Раунд {round_num}")
        
        # Проверяем, не была ли остановлена дискуссия
        if check_if_stopped and discussion_id:
            is_stopped = await check_if_stopped(discussion_id)
            if is_stopped:
                logging.info(f"Обсуждение {discussion_id} было остановлено пользователем")
                break
                
        for participant in participants:
            response = await participant.ask(discussion_history)
            response = strip_markdown(response)
            message = f"<b>{participant.name}</b>: {response}"
            discussion_history.append(message)
            if send_callback:
                await send_callback(message)
                
            # Проверяем после каждого сообщения, не была ли остановлена дискуссия
            if check_if_stopped and discussion_id:
                is_stopped = await check_if_stopped(discussion_id)
                if is_stopped:
                    logging.info(f"Обсуждение {discussion_id} было остановлено пользователем после сообщения от {participant.name}")
                    break
                    
        if is_stopped:
            break
                
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
      
    # Итоговый вывод
    summary = None
    try:
        status_message = "нормальное завершение"
        if is_stopped:
            status_message = "досрочное завершение по запросу пользователя"
            discussion_history.append(f"<b>Система</b>: Обсуждение было остановлено пользователем досрочно.")
            
        summary_participant = Discusser(os.getenv('GENAI_API_KEY_1'), "Ты ии который максимально рационально рассуждаешь", "ИИ")
        await summary_participant.initialize()  # Initialize the AI backend
        summary_prompt = f"""Вот весь диалог между ИИ. Сделай краткий, структурированный и читабельный вывод для пользователя, к которому пришли участники обсуждения.
        Учти, что обсуждение имело {status_message}."""
        summary = await summary_participant.ask_without_humanization(summary_prompt, discussion_history)
        if isinstance(summary, (tuple, list)):
            summary = "\n".join(str(x) for x in summary if isinstance(x, str))
        summary = str(summary).replace("('[", "").replace("]')", "").replace("('[", "").replace("]')", "").strip()
        summary = strip_markdown(summary)
        await summary_participant.close()  # Close the AI backend
    except Exception as e:
        summary = f"Ошибка при получении вывода: {e}"
    logging.info(f"Обсуждение завершено. Статус: {'остановлено досрочно' if is_stopped else 'завершено нормально'}")
    return summary, discussion_history 