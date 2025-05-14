# AI Discussion System

Система для организации обсуждений между несколькими ИИ-участниками с различными характерами и ролями.

## Архитектура системы

### Модули и компоненты

Система построена на основе следующих компонентов:

1. **Модуль Discusser** - Абстракция для участников обсуждения
   - `BaseDiscusser` - абстрактный базовый класс для всех дискуссеров
   - `Discusser` - основная реализация дискуссера на базе AI моделей
   - `SimpleDiscusser` - простая правило-ориентированная реализация для тестирования
   - `CognitiveDiscusser` - продвинутая реализация с симуляцией когнитивных процессов

2. **Модуль AIBackend** - Абстракция для AI-бэкендов
   - `AIBackend` - абстрактный базовый класс для всех AI-бэкендов
   - `GeminiBackend` - реализация для работы с Google Gemini API
   - `OpenAIBackend` - реализация для работы с OpenAI API

3. **Фабрика Дискуссеров**
   - `DiscusserFactory` - класс для создания дискуссеров различных типов

4. **Загрузка настроек**
   - `settings_loader.py` - загрузка настроек и создание дискуссеров

### Диаграмма классов

```
BaseDiscusser (abstract)
    |
    ├── Discusser (AI-based)
    |       |
    |       ├── Uses AIBackend
    |       |
    |       └── CognitiveDiscusser (Group chat simulation)
    |
    └── SimpleDiscusser (Rule-based)


AIBackend (abstract)
    |
    ├── GeminiBackend
    |
    └── OpenAIBackend


DiscusserFactory
    |
    └── Creates instances of BaseDiscusser subclasses
```

## Как использовать

### Пример создания дискуссеров

```python
# Создание ИИ-дискуссера с бэкендом Gemini
discusser = Discusser(
    api_key="ваш_api_ключ",
    context="Инструкции и контекст для ИИ",
    name="Имя дискуссера",
    model="gemini-2.0-flash-001",
    backend_type="gemini"
)
await discusser.initialize()

# Создание простого правило-ориентированного дискуссера
simple_discusser = SimpleDiscusser(
    name="Имя",
    personality="дружелюбный",
    responses=["Список", "предопределенных", "ответов"]
)
await simple_discusser.initialize()

# Создание когнитивного дискуссера с симуляцией мышления
cognitive_discusser = CognitiveDiscusser(
    api_key="ваш_api_ключ",
    context="Инструкции и контекст для ИИ",
    name="Имя дискуссера",
    model="gemini-2.0-flash-001",
    backend_type="gemini"
)
await cognitive_discusser.initialize()

# Или с использованием фабрики
discusser = await DiscusserFactory.create_discusser(
    discusser_type="cognitive",  # ai, simple, cognitive
    name="Имя",
    config={
        "api_key": "ваш_api_ключ",
        "context": "Инструкции и контекст",
        "model": "gemini-2.0-flash-001",
        "backend_type": "gemini"
    }
)
```

### Настройка через JSON

Система поддерживает настройку через JSON-файл:

```json
{
  "settings": [
    {
      "env_token_name": "GENAI_API_KEY_1",
      "name": "Анна",
      "character_path": "./characters/character_1.txt",
      "backend_type": "gemini",
      "model": "gemini-2.0-flash-001",
      "discusser_type": "ai"
    },
    {
      "env_token_name": "GENAI_API_KEY_2",
      "name": "Артур",
      "character_path": "./characters/character_2.txt",
      "backend_type": "gemini",
      "model": "gemini-2.0-flash-001",
      "discusser_type": "cognitive"
    },
    {
      "name": "Максим",
      "personality": "логичный",
      "discusser_type": "simple",
      "responses": [
        "Давайте рассмотрим этот вопрос логически.",
        "С точки зрения логики, самое разумное решение - это..."
      ]
    }
  ]
}
```

## Типы дискуссеров

### Обычный дискуссер (Discusser)
Использует AI модель (Gemini или OpenAI) для генерации ответов. Предоставляет базовую функциональность для участия в дискуссиях.

### Простой дискуссер (SimpleDiscusser)
Использует правила и предопределенные ответы вместо AI. Полезен для тестирования или ситуаций, когда доступ к API ограничен.

### Когнитивный дискуссер (CognitiveDiscusser)
Расширяет обычного дискуссера, добавляя симуляцию когнитивных процессов с помощью групповых чатов AutoGen:

- **Модуль восприятия** - Анализирует входные данные
- **Модуль памяти** - Привносит контекст и прошлый опыт
- **Модуль рассуждения** - Логически анализирует информацию
- **Эмоциональный модуль** - Добавляет эмоциональную реакцию
- **Модуль принятия решений** - Формулирует ключевые мысли
- **Языковой модуль** - Превращает мысли в естественный текст

Этот подход создает более реалистичные и человеческие ответы, имитируя процесс размышления.

## Расширение системы

### Добавление нового типа дискуссера

Для добавления нового типа дискуссера:

1. Создайте класс, наследующийся от `BaseDiscusser` или `Discusser`
2. Реализуйте все абстрактные методы
3. Добавьте поддержку нового типа в `DiscusserFactory`

### Добавление нового AI бэкенда

Для добавления поддержки новой AI-платформы:

1. Создайте класс, наследующийся от `AIBackend`
2. Реализуйте методы `initialize()`, `generate_response()` и `close()`
3. Обновите метод `_create_backend()` в классе `Discusser`

## Запуск примеров

```bash
# Базовый пример с разными типами дискуссеров
python examples/discusser_example.py

# Пример использования когнитивного дискуссера
python examples/cognitive_example.py
```

## Требования

- Python 3.8+
- Библиотеки: aiogram, asyncio, django, autogen-agentchat
- API ключи для соответствующих сервисов (Google Gemini, OpenAI и т.д.)