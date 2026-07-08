from django.contrib import admin
from .models import CorruptionReport, ReportStatus, Department, ReportComment

@admin.register(ReportStatus)
class ReportStatusAdmin(admin.ModelAdmin):
    list_display = ('status', 'description')
    search_fields = ('status',)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone')
    search_fields = ('name', 'email')
    list_filter = ('created_at',)


@admin.register(CorruptionReport)
class CorruptionReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'severity', 'status', 'reporter_name', 'reporter_email', 'created_at')
    list_filter = ('category', 'severity', 'status', 'is_anonymous', 'created_at')
    search_fields = ('title', 'description', 'reporter_name', 'reporter_email')
    readonly_fields = ('created_at', 'updated_at', 'resolved_at', 'reporter_name', 'reporter_email')
    
    fieldsets = (
        ('Report Details', {
            'fields': ('title', 'description', 'category', 'severity', 'location')
        }),
        ('Department', {
            'fields': ('related_department',)
        }),
        ('Reporter Information', {
            'fields': ('reporter', 'reporter_name', 'reporter_email', 'is_anonymous')
        }),
        ('Status & Tracking', {
            'fields': ('status', 'evidence_file', 'resolved_at')
        }),
        ('Admin Notes', {
            'fields': ('admin_notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ReportComment)
class ReportCommentAdmin(admin.ModelAdmin):
    list_display = ('report', 'author', 'is_official', 'created_at')
    list_filter = ('is_official', 'created_at')
    search_fields = ('report__title', 'text', 'author__username')
    readonly_fields = ('created_at', 'updated_at')
