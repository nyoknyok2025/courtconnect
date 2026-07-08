from django.db import models
from django.contrib.auth.models import User

class ReportStatus(models.Model):
    """Tracks the status of reports"""
    STATUS_CHOICES = [
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('investigating', 'Investigating'),
        ('resolved', 'Resolved'),
        ('rejected', 'Rejected'),
        ('closed', 'Closed'),
    ]
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, unique=True)
    description = models.TextField()
    
    def __str__(self):
        return self.get_status_display()


class Department(models.Model):
    """Government departments/authorities"""
    name = models.CharField(max_length=200, unique=True)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name


class CorruptionReport(models.Model):
    """Main report model for corruption/governance issues"""
    CATEGORY_CHOICES = [
        ('corruption', 'Corruption'),
        ('unsafe_service', 'Unsafe Public Service'),
        ('governance', 'Governance Issue'),
        ('bribery', 'Bribery'),
        ('misconduct', 'Official Misconduct'),
        ('other', 'Other'),
    ]
    
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    # Basic Info
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='medium')
    
    # Location Info
    location = models.CharField(max_length=255)
    related_department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Reporter Info
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    reporter_name = models.CharField(max_length=200, help_text="Your name (required)")
    reporter_email = models.EmailField(help_text="Your email (required)")
    is_anonymous = models.BooleanField(default=True)
    
    # Status & Tracking
    status = models.ForeignKey(ReportStatus, on_delete=models.SET_NULL, null=True, default=1)
    evidence_file = models.FileField(upload_to='evidence/', blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    # Admin Notes
    admin_notes = models.TextField(blank=True, help_text="Internal notes for administrators")
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        # `status` is a FK to `ReportStatus`, not a choice field on this model.
        # Use the related object's display label when available.
        if self.status:
            try:
                status_label = self.status.get_status_display()
            except Exception:
                status_label = str(self.status)
        else:
            status_label = 'No Status'
        return f"{self.title} - {status_label}"


class ReportComment(models.Model):
    """Comments/updates on reports"""
    report = models.ForeignKey(CorruptionReport, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    is_official = models.BooleanField(default=False, help_text="Official response from authority")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Comment on {self.report.title}"


