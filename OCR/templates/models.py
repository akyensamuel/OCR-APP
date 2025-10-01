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
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
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
        if not self.structure:
            return 0
        
        # New table detection format (has 'headers' or 'field_names')
        if 'headers' in self.structure:
            headers = self.structure['headers']
            if isinstance(headers, (list, dict)):
                return len(headers)
        
        if 'field_names' in self.structure:
            return len(self.structure['field_names'])
        
        # Old format (has 'fields' key)
        if 'fields' in self.structure:
            fields = self.structure['fields']
            if isinstance(fields, (list, dict)):
                return len(fields)
        
        return 0
    
    def get_field_names(self):
        """Return list of field names from the template structure"""
        if not self.structure:
            return []
        
        # New table detection format (has 'headers' key)
        if 'headers' in self.structure:
            headers = self.structure['headers']
            if isinstance(headers, dict):
                # Headers are stored as {col_index: header_name}
                return list(headers.values())
            elif isinstance(headers, list):
                return headers
        
        # New table detection format (has 'field_names' key)
        if 'field_names' in self.structure:
            return self.structure['field_names']
        
        # Old format (has 'fields' key)
        if 'fields' in self.structure:
            fields = self.structure['fields']
            if isinstance(fields, list):
                # If fields is a list of field objects
                return [field.get('name', f'Field {i+1}') for i, field in enumerate(fields)]
            elif isinstance(fields, dict):
                # If fields is a dictionary
                return list(fields.keys())
        
        return []
