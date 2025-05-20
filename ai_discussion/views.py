from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
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
import requests
import base64
import hashlib
import secrets
import urllib.parse
from utils.firebase_auth import firebase_auth_required, get_firebase_user_data, verify_firebase_token
from utils.firebase_config import get_firestore_db, update_discussion_in_firestore, save_discussion_to_firestore, save_message_to_firestore, get_firebase_config

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
    processing = False
    error_message = None
    auth_debug_data = None
    
    # Check for query parameters that might indicate returning from a process
    if request.GET.get('processing') == 'true':
        processing = True
    if request.GET.get('error'):
        error_message = request.GET.get('error')
    
    # Get user discussions if authenticated
    if request.firebase_user_id:
        discussions = Discussion.objects.filter(firebase_user_id=request.firebase_user_id).order_by('-created_at')[:5]
    
    # Get auth debug data if requested
    if request.GET.get('debug_auth') == 'true':
        auth_data = {
            'is_authenticated': request.firebase_user_id is not None,
            'user_id': request.firebase_user_id,
            'auth_source': getattr(request, 'auth_source', None),
        }
        
        # If user is authenticated, add user data
        if request.firebase_user_id and hasattr(request, 'firebase_user') and request.firebase_user:
            auth_data['user_data'] = request.firebase_user
        
        auth_debug_data = json.dumps(auth_data, indent=2)
    
    return render(request, 'ai_discussion/home.html', {
        'discussions': discussions,
        'is_authenticated': request.firebase_user_id is not None,
        'processing': processing,
        'error_message': error_message,
        'auth_debug_data': auth_debug_data
    })

# Enhanced Authentication views
def user_login(request):
    """Страница входа в систему с серверной обработкой"""
    # If user is already logged in, redirect to home
    if request.firebase_user_id:
        return redirect('ai_discussion:home')
    
    error_message = None
    success_message = None
    
    if request.method == 'POST':
        try:
            # Get request data (both JSON and form data)
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST
                
            email = data.get('email')
            password = data.get('password')
            login_method = data.get('method', 'email')
            
            if login_method == 'email' and email and password:
                # Firebase Auth REST API for email/password login
                firebase_config = get_firebase_config()
                api_key = firebase_config.get('apiKey')
                
                # Call Firebase Auth REST API
                url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"
                payload = {
                    "email": email,
                    "password": password,
                    "returnSecureToken": True
                }
                
                response = requests.post(url, json=payload)
                data = response.json()
                
                if response.status_code == 200 and data.get('idToken'):
                    # Successfully signed in
                    id_token = data.get('idToken')
                    decoded_token = verify_firebase_token(id_token)
                    
                    if decoded_token:
                        # Set the Firebase token as a cookie
                        response = redirect('ai_discussion:home')
                        response.set_cookie('firebaseToken', id_token, max_age=60*60*24*7, samesite='Lax', httponly=True)
                        messages.success(request, "Вход выполнен успешно")
                        return response
                    else:
                        error_message = "Ошибка при верификации токена"
                else:
                    # Error handling
                    error_code = data.get('error', {}).get('message', 'unknown_error')
                    error_message = get_firebase_error_message(error_code)
            else:
                error_message = "Не указаны email или пароль"
        
        except Exception as e:
            logger.error(f"Login error: {e}")
            error_message = "Произошла ошибка при входе"
    
    return render(request, 'ai_discussion/login.html', {
        'error_message': error_message,
        'success_message': success_message
    })

def user_signup(request):
    """Страница регистрации с серверной обработкой"""
    # If user is already logged in, redirect to home
    if request.firebase_user_id:
        return redirect('ai_discussion:home')
    
    error_message = None
    success_message = None
    
    if request.method == 'POST':
        try:
            # Get request data (both JSON and form data)
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST
                
            email = data.get('email')
            password = data.get('password')
            display_name = data.get('displayName')
            
            if email and password and display_name:
                # Validate password
                if len(password) < 6:
                    error_message = "Пароль должен содержать не менее 6 символов"
                    return render(request, 'ai_discussion/signup.html', {
                        'error_message': error_message
                    })
                
                # Firebase Auth REST API for signup
                firebase_config = get_firebase_config()
                api_key = firebase_config.get('apiKey')
                
                # Create user account
                url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={api_key}"
                payload = {
                    "email": email,
                    "password": password,
                    "displayName": display_name,
                    "returnSecureToken": True
                }
                
                response = requests.post(url, json=payload)
                data = response.json()
                
                if response.status_code == 200 and data.get('idToken'):
                    # Successfully signed up
                    id_token = data.get('idToken')
                    local_id = data.get('localId')
                    
                    # Update profile with display name
                    profile_url = f"https://identitytoolkit.googleapis.com/v1/accounts:update?key={api_key}"
                    profile_payload = {
                        "idToken": id_token,
                        "displayName": display_name,
                        "returnSecureToken": True
                    }
                    requests.post(profile_url, json=profile_payload)
                    
                    # Set the Firebase token as a cookie
                    response = redirect('ai_discussion:home')
                    response.set_cookie('firebaseToken', id_token, max_age=60*60*24*7, samesite='Lax', httponly=True)
                    messages.success(request, "Регистрация выполнена успешно")
                    return response
                else:
                    # Error handling
                    error_code = data.get('error', {}).get('message', 'unknown_error')
                    error_message = get_firebase_error_message(error_code)
            else:
                error_message = "Все поля должны быть заполнены"
        
        except Exception as e:
            logger.error(f"Signup error: {e}")
            error_message = "Произошла ошибка при регистрации"
    
    return render(request, 'ai_discussion/signup.html', {
        'error_message': error_message,
        'success_message': success_message
    })

def reset_password(request):
    """Страница сброса пароля с серверной обработкой"""
    error_message = None
    success_message = None
    
    if request.method == 'POST':
        try:
            # Get request data (both JSON and form data)
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST
                
            email = data.get('email')
            
            if email:
                # Firebase Auth REST API for password reset
                firebase_config = get_firebase_config()
                api_key = firebase_config.get('apiKey')
                
                url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={api_key}"
                payload = {
                    "requestType": "PASSWORD_RESET",
                    "email": email
                }
                
                response = requests.post(url, json=payload)
                
                if response.status_code == 200:
                    success_message = "Инструкции по сбросу пароля отправлены на ваш email"
                else:
                    data = response.json()
                    error_code = data.get('error', {}).get('message', 'unknown_error')
                    error_message = get_firebase_error_message(error_code)
            else:
                error_message = "Укажите email"
                
        except Exception as e:
            logger.error(f"Password reset error: {e}")
            error_message = "Произошла ошибка при отправке сброса пароля"
    
    return render(request, 'ai_discussion/reset-password.html', {
        'error_message': error_message,
        'success_message': success_message
    })

def user_logout(request):
    """Выход из системы с серверной стороны"""
    # Clear the token cookie
    response = redirect('ai_discussion:login')
    response.delete_cookie('firebaseToken')
    messages.success(request, "Вы успешно вышли из системы")
    return response

# Helper function for Firebase error messages
def get_firebase_error_message(error_code):
    """Get user-friendly error message from Firebase error code"""
    error_messages = {
        'EMAIL_NOT_FOUND': 'Пользователь с таким email не найден',
        'INVALID_PASSWORD': 'Неверный пароль',
        'USER_DISABLED': 'Учетная запись отключена',
        'EMAIL_EXISTS': 'Пользователь с таким email уже существует',
        'OPERATION_NOT_ALLOWED': 'Данный метод регистрации отключен',
        'TOO_MANY_ATTEMPTS_TRY_LATER': 'Слишком много попыток входа. Попробуйте позже',
        'INVALID_EMAIL': 'Недействительный email',
        'WEAK_PASSWORD': 'Слишком слабый пароль',
        'MISSING_EMAIL': 'Укажите email',
    }
    
    return error_messages.get(error_code, f'Ошибка: {error_code}')

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

@csrf_exempt  # Exempt for API calls, normal form submissions will have CSRF token
def start_discussion(request):
    """Начать новое обсуждение - обрабатывает как стандартные POST запросы от форм, так и AJAX"""
    if request.method != 'POST':
        # Redirect GET requests to home
        return redirect('ai_discussion:home')
    
    try:
        # Get question from POST data, handling both form submissions and JSON
        question = None
        
        if request.content_type == 'application/json':
            # For AJAX requests
            data = json.loads(request.body)
            question = data.get('question', '').strip()
        else:
            # For form submissions
            question = request.POST.get('question', '').strip()
        
        if not question:
            # Handle empty question
            if request.content_type == 'application/json':
                return JsonResponse({
                    'status': 'error',
                    'message': 'Вопрос не может быть пустым'
                }, status=400)
            else:
                # Redirect back to home with error
                return redirect(f'/?error={"Вопрос не может быть пустым"}')
        
        # Create a new discussion in the database
        discussion = Discussion.objects.create(
            question=question,
            firebase_user_id=request.firebase_user_id
        )
        
        # Start the async discussion in a separate thread
        threading.Thread(
            target=lambda: asyncio.run(process_discussion(discussion.id, question))
        ).start()
        
        # Handle response based on request type
        if request.content_type == 'application/json':
            # For AJAX requests, return JSON
            return JsonResponse({
                'status': 'success',
                'discussion_id': discussion.id,
                'redirect_url': reverse('ai_discussion:discussion_detail', args=[discussion.id])
            })
        else:
            # For form submissions, redirect to the discussion page
            return redirect('ai_discussion:discussion_detail', discussion_id=discussion.id)
            
    except Exception as e:
        logger.error(f"Error starting discussion: {e}")
        
        # Handle error based on request type
        if request.content_type == 'application/json':
            return JsonResponse({
                'status': 'error',
                'message': f'Ошибка: {str(e)}'
            }, status=400)
        else:
            # Redirect back to home with error
            return redirect(f'/?error={"Ошибка: " + str(e)}')

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

@csrf_exempt  # Exempt for API calls, normal form submissions will use GET
def auth_debug(request):
    """Отладочная информация об аутентификации"""
    data = {
        'is_authenticated': request.firebase_user_id is not None,
        'user_id': request.firebase_user_id,
        'auth_source': getattr(request, 'auth_source', None),
        'headers': {k: v for k, v in request.headers.items() if k.lower() in ['authorization', 'cookie']},
        'cookies': {k: v for k, v in request.COOKIES.items() if k.lower() in ['firebasetoken']},
    }
    
    # If user is authenticated, get additional user data
    if request.firebase_user_id and hasattr(request, 'firebase_user') and request.firebase_user:
        data['user_data'] = request.firebase_user
    
    # Return JSON for API calls, or redirect to home with debug info for form submissions
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
        return JsonResponse(data)
    else:
        # Redirect to home with debug parameter
        return redirect('/?debug_auth=true')

# Google OAuth2 authentication views
def generate_oauth_state():
    """Generate a secure state token for OAuth2 flow"""
    return secrets.token_urlsafe(32)

def google_auth(request):
    """Start Google OAuth2 authentication flow"""
    try:
        # Get Firebase configuration
        firebase_config = get_firebase_config()
        api_key = firebase_config.get('apiKey')
        project_id = firebase_config.get('projectId')
        
        # Generate and store state parameter to prevent CSRF
        state = generate_oauth_state()
        request.session['oauth_state'] = state
        
        # Generate URL for Google OAuth2
        oauth_params = {
            'client_id': firebase_config.get('messagingSenderId') + '.apps.googleusercontent.com',
            'redirect_uri': request.build_absolute_uri('/auth/google/callback/'),
            'response_type': 'code',
            'scope': 'email profile',
            'state': state,
            'prompt': 'select_account',
        }
        
        auth_url = f"https://accounts.google.com/o/oauth2/auth?{urllib.parse.urlencode(oauth_params)}"
        return redirect(auth_url)
    
    except Exception as e:
        logger.error(f"Error starting Google auth: {e}")
        messages.error(request, "Ошибка при начале OAuth аутентификации")
        return redirect('ai_discussion:login')

def google_auth_callback(request):
    """Handle Google OAuth2 callback"""
    try:
        # Verify state parameter to prevent CSRF
        state = request.GET.get('state')
        session_state = request.session.pop('oauth_state', None)
        
        if not state or state != session_state:
            messages.error(request, "Недействительное состояние OAuth")
            return redirect('ai_discussion:login')
        
        # Check for errors
        error = request.GET.get('error')
        if error:
            messages.error(request, f"Ошибка OAuth: {error}")
            return redirect('ai_discussion:login')
        
        # Get authorization code
        code = request.GET.get('code')
        if not code:
            messages.error(request, "Код авторизации не получен")
            return redirect('ai_discussion:login')
        
        # Get Firebase configuration
        firebase_config = get_firebase_config()
        api_key = firebase_config.get('apiKey')
        
        # Exchange code for token
        token_url = "https://oauth2.googleapis.com/token"
        client_id = firebase_config.get('messagingSenderId') + '.apps.googleusercontent.com'
        client_secret = os.environ.get('GOOGLE_CLIENT_SECRET', '')
        
        token_data = {
            'code': code,
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': request.build_absolute_uri('/auth/google/callback/'),
            'grant_type': 'authorization_code'
        }
        
        token_response = requests.post(token_url, data=token_data)
        token_json = token_response.json()
        
        if 'error' in token_json:
            messages.error(request, f"Ошибка получения токена: {token_json['error']}")
            return redirect('ai_discussion:login')
        
        # Get id_token from response
        id_token = token_json.get('id_token')
        
        # Exchange Google ID token for Firebase custom token
        firebase_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithIdp?key={api_key}"
        firebase_data = {
            'postBody': f"id_token={id_token}&providerId=google.com",
            'requestUri': request.build_absolute_uri('/'),
            'returnSecureToken': True,
            'returnIdpCredential': True
        }
        
        firebase_response = requests.post(firebase_url, json=firebase_data)
        firebase_json = firebase_response.json()
        
        if 'error' in firebase_json:
            messages.error(request, f"Ошибка входа через Firebase: {firebase_json['error']['message']}")
            return redirect('ai_discussion:login')
        
        # Get Firebase ID token
        firebase_token = firebase_json.get('idToken')
        
        # Set the token as a cookie
        response = redirect('ai_discussion:home')
        response.set_cookie('firebaseToken', firebase_token, max_age=60*60*24*7, samesite='Lax', httponly=True)
        
        # Check if this is a new user
        is_new_user = firebase_json.get('isNewUser', False)
        
        if is_new_user:
            messages.success(request, "Регистрация через Google выполнена успешно")
        else:
            messages.success(request, "Вход через Google выполнен успешно")
        
        return response
    
    except Exception as e:
        logger.error(f"Error in Google auth callback: {e}")
        messages.error(request, "Произошла ошибка при аутентификации через Google")
        return redirect('ai_discussion:login')
