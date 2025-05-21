from django.db import models
from django.utils.timezone import localtime
import json

# Create your models here.

class Discussion(models.Model):
    question = models.TextField(verbose_name="Вопрос пользователя")
    summary = models.TextField(verbose_name="Итог обсуждения", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    completed = models.BooleanField(default=False, verbose_name="Завершено")
    firebase_user_id = models.CharField(max_length=128, verbose_name="Firebase UID", blank=True, null=True)
    is_stopped = models.BooleanField(default=False, verbose_name="Остановлено досрочно")
    selected_participants = models.TextField(verbose_name="Выбранные участники", blank=True, null=True, 
                                            help_text="JSON строка с ID участников из настроек и пользовательских")
    
    class Meta:
        verbose_name = "Обсуждение"
        verbose_name_plural = "Обсуждения"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Обсуждение от {self.created_at.strftime('%d.%m.%Y %H:%M')}: {self.question[:50]}"
    
    def to_dict(self):
        """Преобразовать обсуждение в словарь для JSON"""
        return {
            'id': self.id,
            'question': self.question,
            'summary': self.summary,
            'created_at': localtime(self.created_at).isoformat(),
            'completed': self.completed,
            'is_stopped': self.is_stopped,
            'selected_participants': self.get_selected_participants()
        }
    
    def get_selected_participants(self):
        """Получить список выбранных участников"""
        if not self.selected_participants:
            return []
        try:
            return json.loads(self.selected_participants)
        except:
            return []
    
    def set_selected_participants(self, participants_list):
        """Установить список выбранных участников"""
        if isinstance(participants_list, list):
            self.selected_participants = json.dumps(participants_list)
        else:
            self.selected_participants = None

class Message(models.Model):
    discussion = models.ForeignKey(Discussion, on_delete=models.CASCADE, related_name='messages', verbose_name="Обсуждение")
    content = models.TextField(verbose_name="Содержание сообщения")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    
    class Meta:
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"
        ordering = ['created_at']
    
    def __str__(self):
        return f"Сообщение от {self.created_at.strftime('%d.%m.%Y %H:%M')}"
    
    def to_dict(self):
        """Преобразовать сообщение в словарь для JSON"""
        return {
            'id': self.id,
            'content': self.content,
            'created_at': localtime(self.created_at).isoformat(),
            'discussion_id': self.discussion_id
        }

class CustomCharacter(models.Model):
    """Пользовательские характеры для нейросетей"""
    DISCUSSER_TYPES = [
        ('ai', 'AI - Обычная нейросеть'),
        ('cognitive', 'Cognitive - Аналитическая нейросеть'),
    ]
    
    name = models.CharField(max_length=100, verbose_name="Имя")
    character = models.TextField(verbose_name="Описание характера")
    discusser_type = models.CharField(max_length=20, choices=DISCUSSER_TYPES, default='ai', verbose_name="Тип нейросети")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    firebase_user_id = models.CharField(max_length=128, verbose_name="Firebase UID", blank=True, null=True)
    
    class Meta:
        verbose_name = "Пользовательский характер"
        verbose_name_plural = "Пользовательские характеры"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_discusser_type_display()})"
    
    def to_dict(self):
        """Преобразовать участника в словарь для JSON"""
        return {
            'id': self.id,
            'name': self.name,
            'character': self.character,
            'discusser_type': self.discusser_type,
            'created_at': localtime(self.created_at).isoformat(),
            'is_custom': True
        }
