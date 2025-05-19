from django.db import models
from django.utils.timezone import localtime

# Create your models here.

class Discussion(models.Model):
    question = models.TextField(verbose_name="Вопрос пользователя")
    summary = models.TextField(verbose_name="Итог обсуждения", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    completed = models.BooleanField(default=False, verbose_name="Завершено")
    firebase_user_id = models.CharField(max_length=128, verbose_name="Firebase UID", blank=True, null=True)
    is_stopped = models.BooleanField(default=False, verbose_name="Остановлено досрочно")
    
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
            'is_stopped': self.is_stopped
        }

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
