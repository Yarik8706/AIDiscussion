from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.db import transaction
from django.utils import timezone
from django.contrib import messages
from asgiref.sync import sync_to_async
from .models import Discussion, Message
from .settings_loader import load_participants
from .discussion import run_discussion
import asyncio
import json
import logging
import threading

# Set up logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Cache for participants
_participants = None

def get_participants():
    global _participants
    if _participants is None:
        _participants = load_participants()
    return _participants

def home(request):
    """Главная страница с формой для вопроса"""
    discussions = Discussion.objects.all().order_by('-created_at')[:5]
    return render(request, 'ai_discussion/home.html', {'discussions': discussions})

def discussion_detail(request, discussion_id):
    """Страница отдельного обсуждения"""
    discussion = get_object_or_404(Discussion, id=discussion_id)
    messages = discussion.messages.all().order_by('created_at')
    return render(request, 'ai_discussion/discussion_detail.html', 
                  {'discussion': discussion, 'messages': messages})

@csrf_exempt
@require_POST
def start_discussion(request):
    """Начать новое обсуждение"""
    try:
        data = json.loads(request.body)
        question = data.get('question', '').strip()
        if not question:
            return HttpResponseBadRequest('Вопрос не может быть пустым')
        
        # Создаем новое обсуждение в БД
        discussion = Discussion.objects.create(question=question)
        
        # Запускаем асинхронное обсуждение в отдельном потоке
        threading.Thread(
            target=lambda: asyncio.run(process_discussion(discussion.id, question))
        ).start()
        
        return JsonResponse({
            'status': 'success', 
            'discussion_id': discussion.id, 
            'redirect_url': reverse('ai_discussion:discussion_detail', args=[discussion.id])
        })
    except Exception as e:
        logger.error(f"Error starting discussion: {e}")
        return HttpResponseBadRequest(f'Ошибка: {str(e)}')

@csrf_exempt
@require_POST
def delete_discussion(request, discussion_id):
    """Удалить обсуждение"""
    try:
        discussion = get_object_or_404(Discussion, id=discussion_id)
        discussion.delete()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success'})
        else:
            messages.success(request, "Обсуждение успешно удалено.")
            return redirect('ai_discussion:discussions_list')
    except Exception as e:
        logger.error(f"Error deleting discussion: {e}")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
        else:
            messages.error(request, f"Ошибка при удалении обсуждения: {str(e)}")
            return redirect('ai_discussion:discussion_detail', discussion_id=discussion_id)

# Создаем синхронные обертки для операций с базой данных
@sync_to_async
def get_discussion_by_id(discussion_id):
    return Discussion.objects.get(id=discussion_id)

@sync_to_async
def create_message(discussion, content):
    return Message.objects.create(discussion=discussion, content=content)

@sync_to_async
def update_discussion(discussion, summary, completed=True):
    discussion.summary = summary
    discussion.completed = completed
    discussion.save()
    return discussion

async def process_discussion(discussion_id, question):
    """Обработать обсуждение асинхронно"""
    try:
        # Получаем объект обсуждения асинхронно
        discussion = await get_discussion_by_id(discussion_id)
        
        # Функция для сохранения сообщений в БД
        async def save_message(message):
            await create_message(discussion, message)
        
        # Запускаем обсуждение с callbacks для сохранения сообщений
        participants = get_participants()
        summary, messages = await run_discussion(
            participants=participants,
            question=question,
            send_callback=save_message
        )
        
        # Сохраняем результат
        await update_discussion(discussion, summary, True)
        
        logger.info(f"Discussion {discussion_id} completed successfully")
    except Exception as e:
        logger.error(f"Error in discussion {discussion_id}: {e}")
        try:
            # Получаем объект обсуждения снова, на случай если он не был получен ранее
            discussion = await get_discussion_by_id(discussion_id)
            # Отмечаем как завершенное с ошибкой
            await update_discussion(discussion, f"Ошибка при обработке: {str(e)}", True)
        except Exception as inner_e:
            logger.error(f"Error updating discussion status: {inner_e}")

@sync_to_async
def get_discussion_and_messages(discussion_id):
    discussion = get_object_or_404(Discussion, id=discussion_id)
    messages = list(discussion.messages.all().order_by('created_at').values('content', 'created_at'))
    return {
        'status': 'completed' if discussion.completed else 'in_progress',
        'completed': discussion.completed,
        'summary': discussion.summary if discussion.completed else None,
        'messages': messages,
        'message_count': len(messages)
    }

async def get_discussion_status(request, discussion_id):
    """Получить статус обсуждения и сообщения"""
    data = await get_discussion_and_messages(discussion_id)
    return JsonResponse(data)

def discussions_list(request):
    """Список всех обсуждений"""
    discussions = Discussion.objects.all().order_by('-created_at')
    return render(request, 'ai_discussion/discussions_list.html', {'discussions': discussions})
