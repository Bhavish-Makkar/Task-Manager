from django.contrib import admin

from .models import Comment


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("task", "author", "timestamp")
    search_fields = ("body", "task__title", "author__username")
    readonly_fields = ("task", "author", "body", "timestamp")
