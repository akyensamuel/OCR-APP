from django.db import models
from django.contrib.auth.models import User
import json


class Template(models.Model):
    """
    Model for storing uploaded template forms and their extracted structure.
    This represents the 'master form' that defines field positions and layout.
    """
    name = models.CharField(max_length=255, help_text="Name of the template")
    description = models.TextField(blank=True, null=True, help_text="Description of what this template is for")
    file = models.FileField(upload_to='templates/', help_text="Original template file (PDF/image)")
    
    # JSON field to store the extracted structure (field names, coordinates, etc.)
    structure = models.JSONField(
        default=dict, 
        help_text="JSON structure containing field names, positions, and coordinates"
    )
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    # Processing status
    PROCESSING_STATUS_CHOICES = [
        ('pending', 'Pending Processing'),
        ('processing', 'Processing'),
        ('completed', 'Processing Complete'),
        ('failed', 'Processing Failed'),
    ]
    processing_status = models.CharField(
        max_length=20, 
        choices=PROCESSING_STATUS_CHOICES, 
        default='pending'
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Template"
        verbose_name_plural = "Templates"
    
    def __str__(self):
        return f"{self.name} ({self.processing_status})"
    
    @property
    def field_count(self):
        """Return the number of fields detected in this template"""
        if self.structure and 'fields' in self.structure:
            return len(self.structure['fields'])
        return 0
    
    def get_field_names(self):
        """Return list of field names from the template structure"""
        if self.structure and 'fields' in self.structure:
            return list(self.structure['fields'].keys())
        return []
