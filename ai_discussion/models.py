from django.db import models

# Create your models here.

class Discussion(models.Model):
    question = models.TextField(verbose_name="Вопрос пользователя")
    summary = models.TextField(verbose_name="Итог обсуждения", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    completed = models.BooleanField(default=False, verbose_name="Завершено")
    
    class Meta:
        verbose_name = "Обсуждение"
        verbose_name_plural = "Обсуждения"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Обсуждение от {self.created_at.strftime('%d.%m.%Y %H:%M')}: {self.question[:50]}"

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
