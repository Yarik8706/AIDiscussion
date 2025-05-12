from django.contrib import admin
from .models import Discussion, Message

class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ['content', 'created_at']

@admin.register(Discussion)
class DiscussionAdmin(admin.ModelAdmin):
    list_display = ['question', 'created_at', 'completed']
    search_fields = ['question', 'summary']
    list_filter = ['completed', 'created_at']
    readonly_fields = ['created_at']
    inlines = [MessageInline]

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['discussion', 'content_preview', 'created_at']
    search_fields = ['content']
    list_filter = ['created_at']
    readonly_fields = ['created_at']
    
    def content_preview(self, obj):
        if len(obj.content) > 50:
            return obj.content[:47] + "..."
        return obj.content
    content_preview.short_description = 'Содержание'
