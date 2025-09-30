from django.db import models
from django.utils import timezone


class TextDocument(models.Model):
    """Model for storing text documents for editing"""
    
    PROCESSING_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    title = models.CharField(max_length=200)
    original_file = models.FileField(upload_to='uploads/editor/', blank=True)
    extracted_text = models.TextField(blank=True)
    confidence_score = models.FloatField(default=0.0)
    processing_status = models.CharField(
        max_length=20,
        choices=PROCESSING_STATUS_CHOICES,
        default='pending'
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Text Document'
        verbose_name_plural = 'Text Documents'
    
    def __str__(self):
        return self.title
    
    @property
    def word_count(self):
        """Get word count of extracted text"""
        return len(self.extracted_text.split()) if self.extracted_text else 0
    
    @property
    def char_count(self):
        """Get character count of extracted text"""
        return len(self.extracted_text) if self.extracted_text else 0
