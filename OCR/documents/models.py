from django.db import models
from django.contrib.auth.models import User
from templates.models import Template


class Document(models.Model):
    """
    Model for storing processed documents that use a template structure
    or standalone documents for general text extraction.
    """
    name = models.CharField(max_length=255, help_text="Document name or identifier")
    
    # Store file directly in database as binary data
    file_data = models.BinaryField(null=True, blank=True, help_text="Original document file data (stored in DB)")
    file_name = models.CharField(max_length=255, null=True, blank=True, help_text="Original filename")
    file_type = models.CharField(max_length=50, null=True, blank=True, help_text="File MIME type")
    file_size = models.IntegerField(null=True, blank=True, help_text="File size in bytes")
    
    # Keep for backward compatibility (will be deprecated)
    file = models.FileField(upload_to='documents/', blank=True, null=True, help_text="Original uploaded document - deprecated")
    
    # Optional link to template (None for general text extraction)
    template = models.ForeignKey(
        Template, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        help_text="Template used for structured extraction (optional)"
    )
    
    # Extracted data (structured for template-based, raw text for general)
    extracted_data = models.JSONField(
        default=dict, 
        help_text="Extracted structured data based on template fields"
    )
    
    # Excel file with populated data (for table-based templates) - stored in DB
    excel_data = models.BinaryField(null=True, blank=True, help_text="Populated Excel file data (stored in DB)")
    excel_name = models.CharField(max_length=255, null=True, blank=True, help_text="Excel filename")
    
    # Keep for backward compatibility (will be deprecated)
    excel_file = models.FileField(
        upload_to='documents/excel/',
        blank=True,
        null=True,
        help_text="Populated Excel file with extracted data - deprecated"
    )
    
    # Raw text version (for general text extraction mode)
    text_version = models.TextField(
        blank=True, 
        null=True, 
        help_text="Raw extracted text for general OCR mode"
    )
    
    # Processing metadata
    confidence_score = models.FloatField(
        null=True, 
        blank=True, 
        help_text="OCR confidence score (0.0 - 1.0)"
    )
    
    # User and timestamps
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Processing status
    PROCESSING_STATUS_CHOICES = [
        ('pending', 'Pending Processing'),
        ('processing', 'Processing'),
        ('completed', 'Processing Complete'),
        ('failed', 'Processing Failed'),
        ('reviewed', 'Human Reviewed'),
    ]
    processing_status = models.CharField(
        max_length=20, 
        choices=PROCESSING_STATUS_CHOICES, 
        default='pending'
    )
    
    # Processing type
    PROCESSING_TYPE_CHOICES = [
        ('template', 'Template-based Extraction'),
        ('general', 'General Text Extraction'),
    ]
    processing_type = models.CharField(
        max_length=20,
        choices=PROCESSING_TYPE_CHOICES,
        default='general'
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Document"
        verbose_name_plural = "Documents"
    
    def __str__(self):
        if self.template:
            return f"{self.name} (Template: {self.template.name})"
        return f"{self.name} (General OCR)"
    
    @property
    def is_template_based(self):
        """Check if this document uses template-based processing"""
        return self.template is not None
    
    def get_extracted_field_value(self, field_name):
        """Get the value of a specific extracted field"""
        if self.extracted_data and field_name in self.extracted_data:
            return self.extracted_data[field_name]
        return None


class DocumentProcessingLog(models.Model):
    """
    Model for logging OCR processing steps and errors for debugging.
    """
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='processing_logs')
    step = models.CharField(max_length=100, help_text="Processing step name")
    status = models.CharField(
        max_length=20,
        choices=[('started', 'Started'), ('completed', 'Completed'), ('failed', 'Failed')],
        default='started'
    )
    message = models.TextField(blank=True, help_text="Log message or error details")
    processing_time = models.FloatField(null=True, blank=True, help_text="Time taken for this step (seconds)")
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.document.name} - {self.step} ({self.status})"
