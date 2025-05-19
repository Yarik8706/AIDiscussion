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
from utils.firebase_auth import firebase_auth_required
from utils.firebase_config import get_firestore_db, update_discussion_in_firestore, save_discussion_to_firestore, save_message_to_firestore

# Set up logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Cache for participants
_participants = None

async def get_participants():
    global _participants
    if _participants is None:
        _participants = await load_participants()
    return _participants

def home(request):
    """Главная страница с формой для вопроса"""
    discussions = []
    if request.firebase_user_id:
        discussions = Discussion.objects.filter(firebase_user_id=request.firebase_user_id).order_by('-created_at')[:5]
    return render(request, 'ai_discussion/home.html', {
        'discussions': discussions,
        'is_authenticated': request.firebase_user_id is not None
    })

def discussion_detail(request, discussion_id):
    """Страница отдельного обсуждения"""
    discussion = get_object_or_404(Discussion, id=discussion_id)
    
    # Проверка доступа: если обсуждение привязано к пользователю, только он может его просматривать
    if discussion.firebase_user_id and discussion.firebase_user_id != request.firebase_user_id:
        return render(request, 'ai_discussion/error.html', {'error': 'У вас нет доступа к этому обсуждению'})
        
    messages = discussion.messages.all().order_by('created_at')
    return render(request, 'ai_discussion/discussion_detail.html', {
        'discussion': discussion, 
        'messages': messages,
        'is_authenticated': request.firebase_user_id is not None
    })

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
        discussion = Discussion.objects.create(
            question=question,
            firebase_user_id=request.firebase_user_id
        )
        
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
@firebase_auth_required
def delete_discussion(request, discussion_id):
    """Удалить обсуждение"""
    try:
        discussion = get_object_or_404(Discussion, id=discussion_id)
        
        # Проверка доступа: только владелец может удалить обсуждение
        if discussion.firebase_user_id and discussion.firebase_user_id != request.firebase_user_id:
            return JsonResponse({'status': 'error', 'message': 'У вас нет доступа к этому обсуждению'}, status=403)
            
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
        participants = await get_participants()
        summary, messages = await run_discussion(
            participants=participants,
            question=question,
            send_callback=save_message,
            discussion_id=discussion_id,
            check_if_stopped=check_if_discussion_stopped
        )
        
        # Сохраняем результат
        discussion_obj = await get_discussion_by_id(discussion_id)
        await update_discussion(discussion_obj, summary, True)
        
        # Если обсуждение привязано к пользователю, сохраняем его в Firestore
        if discussion.firebase_user_id:
            try:
                # Получаем экземпляр Firestore
                db = get_firestore_db()
                
                # Создаем словарь с данными обсуждения
                discussion_data = {
                    'id': discussion.id,
                    'question': discussion.question,
                    'summary': discussion.summary,
                    'created_at': discussion.created_at.isoformat(),
                    'completed': discussion.completed,
                    'is_stopped': discussion.is_stopped,
                    'user_id': discussion.firebase_user_id,
                }
                
                # Сохраняем в Firestore
                db.collection('users').document(discussion.firebase_user_id).collection('discussions').document(str(discussion.id)).set(discussion_data)
                
                # Сохраняем сообщения в Firestore
                for idx, msg in enumerate(discussion.messages.all().order_by('created_at')):
                    message_data = {
                        'content': msg.content,
                        'created_at': msg.created_at.isoformat(),
                        'discussion_id': discussion.id,
                        'order': idx
                    }
                    db.collection('users').document(discussion.firebase_user_id).collection('discussions') \
                        .document(str(discussion.id)).collection('messages').add(message_data)
                
                logger.info(f"Discussion {discussion_id} saved to Firestore for user {discussion.firebase_user_id}")
            except Exception as e:
                logger.error(f"Error saving to Firestore: {e}")
        
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
def get_discussion_and_messages(discussion_id, user_id=None):
    discussion = get_object_or_404(Discussion, id=discussion_id)
    
    # Проверка доступа
    if discussion.firebase_user_id and discussion.firebase_user_id != user_id:
        return {
            'status': 'error',
            'error': 'Unauthorized'
        }
        
    messages = list(discussion.messages.all().order_by('created_at'))
    return {
        'status': 'completed' if discussion.completed else 'in_progress',
        'completed': discussion.completed,
        'is_stopped': discussion.is_stopped,
        'summary': discussion.summary if discussion.completed else None,
        'discussion': discussion.to_dict(),
        'messages': [msg.to_dict() for msg in messages],
        'message_count': len(messages)
    }

async def get_discussion_status(request, discussion_id):
    """Получить статус обсуждения и сообщения"""
    data = await get_discussion_and_messages(discussion_id, request.firebase_user_id)
    if 'error' in data:
        return JsonResponse(data, status=403)
    return JsonResponse(data)

def discussions_list(request):
    """Список всех обсуждений"""
    if request.firebase_user_id:
        # Для авторизованных пользователей показываем только их обсуждения
        discussions = Discussion.objects.filter(firebase_user_id=request.firebase_user_id).order_by('-created_at')
    else:
        # Для неавторизованных пользователей показываем публичные обсуждения
        discussions = Discussion.objects.filter(firebase_user_id__isnull=True).order_by('-created_at')
    
    return render(request, 'ai_discussion/discussions_list.html', {
        'discussions': discussions,
        'is_authenticated': request.firebase_user_id is not None
    })

@firebase_auth_required
def user_discussions(request):
    """API для получения обсуждений текущего пользователя"""
    discussions = Discussion.objects.filter(firebase_user_id=request.firebase_user_id).order_by('-created_at')
    data = [discussion.to_dict() for discussion in discussions]
    return JsonResponse({'discussions': data})

def user_login(request):
    """Страница входа"""
    return render(request, 'ai_discussion/login.html')

@csrf_exempt
@require_POST
def stop_discussion(request, discussion_id):
    """Остановить обсуждение досрочно"""
    try:
        discussion = get_object_or_404(Discussion, id=discussion_id)
        
        # Проверка доступа: только владелец может остановить обсуждение
        if discussion.firebase_user_id and discussion.firebase_user_id != request.firebase_user_id:
            return JsonResponse({'status': 'error', 'message': 'У вас нет доступа к этому обсуждению'}, status=403)
        
        # Если обсуждение уже завершено, возвращаем сообщение об этом
        if discussion.completed:
            return JsonResponse({'status': 'success', 'message': 'Обсуждение уже завершено'})
            
        # Отмечаем обсуждение как остановленное
        discussion.is_stopped = True
        discussion.save()
        
        # Обновляем в Firestore, если нужно
        if discussion.firebase_user_id:
            update_discussion_in_firestore(
                discussion.firebase_user_id, 
                str(discussion.id), 
                {'is_stopped': True}
            )
            
        return JsonResponse({'status': 'success', 'message': 'Обсуждение остановлено'})
    except Exception as e:
        logger.error(f"Error stopping discussion: {e}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@sync_to_async
def check_if_discussion_stopped(discussion_id):
    """Проверить, было ли обсуждение остановлено"""
    try:
        discussion = Discussion.objects.get(id=discussion_id)
        return discussion.is_stopped
    except Exception as e:
        logger.error(f"Error checking if discussion is stopped: {e}")
        return False

@csrf_exempt
@require_POST
@firebase_auth_required
def migrate_local_discussions(request):
    """Переместить локальные обсуждения из localStorage в Firestore"""
    try:
        data = json.loads(request.body)
        local_discussions = data.get('discussions', [])
        
        if not local_discussions:
            return JsonResponse({'status': 'success', 'message': 'Нет локальных обсуждений для миграции'})
            
        user_id = request.firebase_user_id
        migrated_count = 0
        
        for local_discussion in local_discussions:
            try:
                # Создаем обсуждение в базе данных
                question = local_discussion.get('question', 'Без вопроса')
                summary = local_discussion.get('summary')
                
                discussion = Discussion.objects.create(
                    question=question,
                    summary=summary,
                    firebase_user_id=user_id,
                    completed=True
                )
                
                # Сохраняем сообщения, если они есть
                messages = local_discussion.get('messages', [])
                for message in messages:
                    Message.objects.create(
                        discussion=discussion,
                        content=message.get('content', '')
                    )
                
                # Сохраняем в Firestore
                discussion_data = {
                    'id': discussion.id,
                    'question': discussion.question,
                    'summary': discussion.summary,
                    'created_at': discussion.created_at.isoformat(),
                    'completed': discussion.completed,
                    'user_id': user_id,
                }
                
                # Сохраняем обсуждение
                save_discussion_to_firestore(user_id, discussion_data)
                
                # Сохраняем сообщения
                for idx, msg in enumerate(messages):
                    message_data = {
                        'content': msg.get('content', ''),
                        'created_at': timezone.now().isoformat(),
                        'discussion_id': discussion.id,
                        'order': idx
                    }
                    save_message_to_firestore(user_id, str(discussion.id), message_data)
                
                migrated_count += 1
            except Exception as discussion_error:
                logger.error(f"Error migrating discussion: {discussion_error}")
                
        return JsonResponse({
            'status': 'success', 
            'message': f'Перенесено {migrated_count} из {len(local_discussions)} обсуждений'
        })
    except Exception as e:
        logger.error(f"Error migrating local discussions: {e}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@csrf_exempt
def auth_debug(request):
    """Отладочная информация об аутентификации"""
    data = {
        'is_authenticated': request.firebase_user_id is not None,
        'user_id': request.firebase_user_id,
        'auth_source': getattr(request, 'auth_source', None),
        'headers': {k: v for k, v in request.headers.items() if k.lower() in ['authorization', 'cookie']},
        'cookies': {k: v for k, v in request.COOKIES.items() if k.lower() in ['firebasetoken']},
    }
    
    return JsonResponse(data)
