from nicegui import ui, app
from typing import List
import asyncio
from settings_loader import load_participants
from discussion import run_discussion
import contextlib

# Tailwind классы для центрации и красоты
CENTER = 'flex flex-col items-center justify-center min-h-screen max-h-screen bg-gradient-to-br from-blue-100 to-indigo-200 w-full'
CARD = 'bg-white rounded-xl shadow-lg p-8 w-[600px] max-w-xl text-center m-auto'
BUTTON = 'mt-4 px-6 py-2 rounded bg-indigo-500 text-white hover:bg-indigo-600 transition-colors duration-200'
ANIMATION = 'transition-all duration-700 ease-in-out'

participants = None
question = ''
discussion_messages: List[str] = []
discussion_result = ''
page_container = None
discussion_task = None
message_column = None

# --- UI Components ---
def main_page():
    global page_container
    if page_container is not None:
        page_container.clear()
    page_container = ui.column().classes(CENTER)
    with page_container:
        with ui.column().classes(CARD):
            ui.label('Задайте вопрос для обсуждения нейросетям').classes('text-2xl font-bold mb-6')
            input_box = ui.input('Ваш вопрос...').props('outlined dense').classes('w-full mb-4')
            submit_btn = ui.button('Обсудить').classes(BUTTON)
            submit_btn.on('click', lambda: on_submit(input_box))
            input_box.on('keydown.enter', lambda: on_submit(input_box))
            # Для анимации скрытия
            input_box.props('v-model="question"')
            submit_btn.props('v-if="question.length > 0"')
            # Сохраняем для анимации
            ui.run_javascript('window.question = ""')

async def on_submit(input_box):
    print("on_submit called")
    global question, discussion_messages, discussion_result, participants, page_container, discussion_task, message_column
    question = input_box.value.strip()
    if not question:
        return
    await ui.run_javascript('document.querySelector(\"input\").classList.add(\"opacity-0\");')
    await asyncio.sleep(0.7)
    if page_container is not None:
        page_container.clear()
    if participants is None:
        participants = load_participants()
    # Создаём контейнер для сообщений
    message_column = ui.column().classes(CENTER)
    if discussion_task is not None:
        discussion_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await discussion_task
    discussion_task = asyncio.create_task(show_discussion(question, message_column))

def message_card(html_text):
    print(f"Creating card with text: {html_text}")
    with ui.card().classes('my-4 shadow-md'):
        ui.html(html_text).classes('text-gray-700 mt-2')

def result_window(result):
    with ui.card().classes('mt-8 p-6 shadow-lg bg-indigo-50'):
        ui.label('Итог обсуждения').classes('text-xl font-bold mb-2')
        ui.label(result).classes('text-gray-800 mb-4')
        with ui.row().classes('justify-center'):
            ui.button('Посмотреть рассуждения нейросетей', on_click=show_all_messages).classes(BUTTON)
            ui.button('Задать новый вопрос', on_click=reset_page).classes(BUTTON)

async def show_discussion(q, message_column):
    print("show_discussion called")
    global discussion_messages, discussion_result
    try:
        discussion_messages = []
        discussion_result = ''
        async def send_to_ui(msg):
            print(f"Adding message: {msg}")
            discussion_messages.append(msg)
            with message_column:
                message_card(msg)
            message_column.update()  # Обновляем контейнер
            await asyncio.sleep(0.01)  # Задержка для рендеринга
        summary = await run_discussion(participants, q, send_callback=send_to_ui)
        discussion_result = summary
        result_window(discussion_result)
    except asyncio.CancelledError:
        print("Обсуждение отменено из-за закрытия вкладки")
        raise
    except Exception as e:
        print(f"Ошибка: {e}")
        raise

def show_all_messages():
    global page_container
    if page_container is not None:
        page_container.clear()
    with ui.column().classes(CENTER):
        ui.label('Рассуждения нейросетей').classes('text-2xl font-bold mb-6')
        for msg in discussion_messages:
            message_card(msg)
        ui.button('Назад к итогу', on_click=lambda: (page_container.clear(), result_window(discussion_result))).classes(BUTTON)

def reset_page():
    global page_container
    if page_container is not None:
        page_container.clear()
    main_page()

async def on_disconnect():
    print("on_disconnect called")
    global discussion_task
    if discussion_task is not None:
        discussion_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await discussion_task
        discussion_task = None

@ui.page('/')
def index():
    main_page()

# --- Tailwind CSS ---
ui.add_head_html('<script src="https://cdn.tailwindcss.com"></script>')
ui.add_head_html('<style>.nicegui-content {margin:0 !important; padding:0 !important;}</style>')
ui.run(title='AI Discussion UI', favicon='🌐')