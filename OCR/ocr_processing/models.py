from django.db import models
from django.utils import timezone


class OCRConfiguration(models.Model):
    """Configuration settings for OCR processing"""
    
    ENGINE_CHOICES = [
        ('tesseract', 'Tesseract'),
        ('easyocr', 'EasyOCR'),
    ]
    
    engine_preference = models.CharField(
        max_length=20,
        choices=ENGINE_CHOICES,
        default='tesseract'
    )
    enable_preprocessing = models.BooleanField(default=True)
    confidence_threshold = models.FloatField(default=50.0)
    max_file_size_mb = models.IntegerField(default=50)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'OCR Configuration'
        verbose_name_plural = 'OCR Configurations'
    
    def __str__(self):
        return f"OCR Config - {self.engine_preference}"


class ProcessingTask(models.Model):
    """Track OCR processing tasks"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    task_name = models.CharField(max_length=200, default='OCR Task')
    file_path = models.CharField(max_length=500, blank=True)
    processing_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    progress_percentage = models.IntegerField(default=0)
    result_text = models.TextField(blank=True)
    confidence_score = models.FloatField(default=0.0)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Processing Task'
        verbose_name_plural = 'Processing Tasks'
    
    def __str__(self):
        return f"{self.task_name} - {self.processing_status}"
