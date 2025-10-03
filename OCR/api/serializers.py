"""
API Serializers for Documents and Templates
"""
from rest_framework import serializers
from documents.models import Document
from templates.models import Template
from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']


class TemplateSerializer(serializers.ModelSerializer):
    """Serializer for Template model"""
    document_count = serializers.SerializerMethodField()
    field_names = serializers.SerializerMethodField()
    created_by = UserSerializer(read_only=True)
    
    class Meta:
        model = Template
        fields = [
            'id', 'name', 'description', 'structure', 'field_count',
            'is_active', 'processing_status', 'created_at', 'updated_at',
            'created_by', 'document_count', 'field_names', 'sample_image'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'field_count']
    
    def get_document_count(self, obj):
        """Get count of documents using this template"""
        return obj.document_set.count()
    
    def get_field_names(self, obj):
        """Get list of field names from template structure"""
        return obj.get_field_names()


class TemplateListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for template lists"""
    document_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Template
        fields = [
            'id', 'name', 'description', 'field_count',
            'is_active', 'created_at', 'document_count'
        ]
        read_only_fields = ['id', 'created_at', 'field_count']
    
    def get_document_count(self, obj):
        return obj.document_set.count()


class DocumentSerializer(serializers.ModelSerializer):
    """Serializer for Document model"""
    template = TemplateListSerializer(read_only=True)
    template_id = serializers.PrimaryKeyRelatedField(
        queryset=Template.objects.all(),
        source='template',
        write_only=True,
        required=False,
        allow_null=True
    )
    uploaded_by = UserSerializer(read_only=True)
    extracted_fields = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()
    excel_file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Document
        fields = [
            'id', 'name', 'file', 'file_url', 'text_version',  # Fixed: text_version not text_content
            'extracted_data', 'extracted_fields', 'confidence_score',
            'processing_status', 'template', 'template_id',
            'uploaded_by', 'created_at', 'updated_at',
            'excel_file', 'excel_file_url'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'extracted_data',
            'confidence_score', 'processing_status'
        ]
    
    def get_extracted_fields(self, obj):
        """Parse extracted_data JSON into structured fields"""
        try:
            import json
            if obj.extracted_data:
                data = json.loads(obj.extracted_data) if isinstance(obj.extracted_data, str) else obj.extracted_data
                if isinstance(data, dict) and 'fields' in data:
                    return data['fields']
                return data
        except:
            pass
        return None
    
    def get_file_url(self, obj):
        """Get full URL for uploaded file"""
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None
    
    def get_excel_file_url(self, obj):
        """Get full URL for Excel export file"""
        if obj.excel_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.excel_file.url)
            return obj.excel_file.url
        return None


class DocumentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for document lists"""
    template_name = serializers.CharField(source='template.name', read_only=True)
    uploaded_by_name = serializers.CharField(source='uploaded_by.username', read_only=True)
    
    class Meta:
        model = Document
        fields = [
            'id', 'name', 'confidence_score', 'processing_status',
            'template_name', 'uploaded_by_name', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class DocumentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating documents with file upload"""
    template_id = serializers.PrimaryKeyRelatedField(
        queryset=Template.objects.all(),
        source='template',
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = Document
        fields = ['name', 'file', 'template_id', 'text_version']  # Fixed: text_version not text_content
    
    def create(self, validated_data):
        """Create document and trigger OCR processing"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['uploaded_by'] = request.user
        
        document = Document.objects.create(**validated_data)
        
        # Trigger OCR processing if file is provided
        if document.file:
            try:
                from ocr_processing.ocr_core import OCREngine
                from django.conf import settings
                import os
                
                file_path = os.path.join(settings.MEDIA_ROOT, document.file.name)
                ocr_engine = OCREngine()
                ocr_result = ocr_engine.extract_text(file_path)
                
                document.text_version = ocr_result.get('text', '')  # Fixed: text_version not text_content
                document.confidence_score = ocr_result.get('confidence', 0)
                document.processing_status = 'completed'
                document.save()
            except Exception as e:
                document.processing_status = 'failed'
                document.save()
                raise serializers.ValidationError(f"OCR processing failed: {str(e)}")
        
        return document


class OCRProcessSerializer(serializers.Serializer):
    """Serializer for OCR processing requests"""
    file = serializers.FileField(required=True)
    template_id = serializers.IntegerField(required=False, allow_null=True)
    extract_structure = serializers.BooleanField(default=False)
    
    def validate_file(self, value):
        """Validate uploaded file"""
        # Check file size (max 10MB)
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("File size must be less than 10MB")
        
        # Check file extension
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.pdf', '.tiff', '.bmp']
        import os
        ext = os.path.splitext(value.name)[1].lower()
        if ext not in allowed_extensions:
            raise serializers.ValidationError(f"File type {ext} not allowed. Allowed types: {', '.join(allowed_extensions)}")
        
        return value


class StatisticsSerializer(serializers.Serializer):
    """Serializer for dashboard statistics"""
    total_documents = serializers.IntegerField()
    total_templates = serializers.IntegerField()
    recent_documents = DocumentListSerializer(many=True)
    documents_by_template = serializers.ListField()
    average_confidence = serializers.FloatField()
    processing_status_breakdown = serializers.DictField()
