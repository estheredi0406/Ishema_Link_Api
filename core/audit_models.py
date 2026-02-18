"""
Audit Log Models
Tracks all access to sensitive data for compliance
"""
from django.db import models
from django.conf import settings
from django.utils import timezone


class AuditLog(models.Model):
    """
    Glass Log - Audit trail for data access
    Records WHO accessed WHAT data WHEN
    Required for Rwanda Data Protection Law compliance
    """
    
    ACTION_CHOICES = [
        ('VIEW', 'Viewed'),
        ('CREATE', 'Created'),
        ('UPDATE', 'Updated'),
        ('DELETE', 'Deleted'),
        ('EXPORT', 'Exported'),
    ]
    
    # Who
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs'
    )
    user_phone = models.CharField(max_length=17, db_index=True)
    user_type = models.CharField(max_length=10)
    
    # What
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    resource_type = models.CharField(max_length=50, db_index=True)  # e.g., 'shipment', 'user'
    resource_id = models.IntegerField(null=True, blank=True)
    sensitive_fields = models.JSONField(default=list, help_text="List of sensitive fields accessed")
    
    # When
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    
    # Where
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Additional Context
    reason = models.TextField(blank=True, help_text="Why was this data accessed?")
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user_phone', '-timestamp']),
            models.Index(fields=['resource_type', 'resource_id']),
            models.Index(fields=['-timestamp']),
        ]
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
    
    def __str__(self):
        return f"{self.user_phone} {self.action} {self.resource_type} at {self.timestamp}"


class ConsentRecord(models.Model):
    """
    Tracks user consent to Terms of Service
    Required for GDPR/Data Protection compliance
    """
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='consent_records'
    )
    
    # What they consented to
    consent_type = models.CharField(max_length=50, db_index=True)  # 'terms', 'privacy', 'marketing'
    version = models.CharField(max_length=20)  # '1.0', '2.0', etc.
    
    # When
    consented_at = models.DateTimeField(default=timezone.now)
    
    # How
    consent_method = models.CharField(max_length=50)  # 'registration', 'update', 'api'
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    # Revocation
    revoked = models.BooleanField(default=False)
    revoked_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-consented_at']
        indexes = [
            models.Index(fields=['user', 'consent_type', '-consented_at']),
        ]
    
    def __str__(self):
        return f"{self.user.phone} - {self.consent_type} v{self.version}"


class DataExportRequest(models.Model):
    """
    GDPR Right to Data Portability
    Tracks user requests to export their data
    """
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='export_requests'
    )
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    requested_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Export file
    export_data = models.JSONField(null=True, blank=True)
    file_path = models.CharField(max_length=255, blank=True)
    
    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-requested_at']
    
    def __str__(self):
        return f"Export for {self.user.phone} - {self.status}"


class AnonymizationRequest(models.Model):
    """
    GDPR Right to be Forgotten
    Tracks user requests to delete/anonymize their data
    """
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('REJECTED', 'Rejected'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='anonymization_requests'
    )
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    requested_at = models.DateTimeField(default=timezone.now)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    # Reason
    reason = models.TextField(blank=True)
    
    # Admin review
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_anonymizations'
    )
    admin_notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-requested_at']
    
    def __str__(self):
        return f"Anonymization for {self.user.phone} - {self.status}"