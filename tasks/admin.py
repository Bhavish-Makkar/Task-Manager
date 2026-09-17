from django.contrib import admin

from .models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "project", "status", "priority", "due_date", "assigned_to")
    list_filter = ("status", "priority")
    search_fields = ("title", "project__name", "assigned_to__username")
