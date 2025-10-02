"""
API ViewSets for Documents and Templates
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Avg, Q
from django.shortcuts import get_object_or_404

from documents.models import Document
from templates.models import Template
from .serializers import (
    DocumentSerializer, DocumentListSerializer, DocumentCreateSerializer,
    TemplateSerializer, TemplateListSerializer,
    OCRProcessSerializer, StatisticsSerializer
)


class TemplateViewSet(viewsets.ModelViewSet):
    """
    API endpoint for templates
    
    list: Get all templates
    retrieve: Get a specific template
    create: Create a new template
    update: Update a template
    destroy: Delete a template
    """
    queryset = Template.objects.all().order_by('-created_at')
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'processing_status']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'name', 'field_count']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return TemplateListSerializer
        return TemplateSerializer
    
    def perform_create(self, serializer):
        """Set created_by to current user"""
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['get'])
    def documents(self, request, pk=None):
        """Get all documents for a specific template"""
        template = self.get_object()
        documents = Document.objects.filter(template=template).order_by('-created_at')
        
        # Apply pagination
        page = self.paginate_queryset(documents)
        if page is not None:
            serializer = DocumentListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = DocumentListSerializer(documents, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a template"""
        template = self.get_object()
        template.is_active = True
        template.save()
        serializer = self.get_serializer(template)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate a template"""
        template = self.get_object()
        template.is_active = False
        template.save()
        serializer = self.get_serializer(template)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def export_excel(self, request, pk=None):
        """Export all template documents to Excel"""
        from django.http import FileResponse
        from ocr_processing.excel_manager import ExcelTemplateManager
        import tempfile
        import os
        
        template = self.get_object()
        documents = Document.objects.filter(template=template)
        
        if not documents.exists():
            return Response(
                {'error': 'No documents found for this template'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Create Excel file
        excel_manager = ExcelTemplateManager()
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
        
        try:
            excel_manager.create_multi_document_export(
                documents=list(documents),
                template=template,
                output_path=temp_file.name
            )
            
            response = FileResponse(
                open(temp_file.name, 'rb'),
                as_attachment=True,
                filename=f'{template.name}_export.xlsx'
            )
            return response
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DocumentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for documents
    
    list: Get all documents
    retrieve: Get a specific document
    create: Create a new document (with file upload)
    update: Update a document
    destroy: Delete a document
    """
    queryset = Document.objects.all().order_by('-created_at')
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['processing_status', 'template']
    search_fields = ['name']  # Simplified to avoid NULL text_content issues
    ordering_fields = ['created_at', 'name', 'confidence_score']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return DocumentListSerializer
        elif self.action == 'create':
            return DocumentCreateSerializer
        return DocumentSerializer
    
    def get_queryset(self):
        """Filter queryset with additional parameters"""
        queryset = super().get_queryset()
        
        # Filter by confidence score range
        confidence_min = self.request.query_params.get('confidence_min')
        confidence_max = self.request.query_params.get('confidence_max')
        
        if confidence_min:
            try:
                queryset = queryset.filter(confidence_score__gte=float(confidence_min))
            except ValueError:
                pass
        
        if confidence_max:
            try:
                queryset = queryset.filter(confidence_score__lte=float(confidence_max))
            except ValueError:
                pass
        
        return queryset.select_related('template', 'uploaded_by')
    
    @action(detail=True, methods=['get'])
    def export_excel(self, request, pk=None):
        """Export document to Excel"""
        from django.http import FileResponse
        
        document = self.get_object()
        
        if not document.excel_file:
            return Response(
                {'error': 'No Excel file available for this document'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return FileResponse(
            open(document.excel_file.path, 'rb'),
            as_attachment=True,
            filename=f'{document.name}.xlsx'
        )
    
    @action(detail=True, methods=['get'])
    def export_pdf(self, request, pk=None):
        """Export document to PDF"""
        from django.http import FileResponse
        from ocr_processing.pdf_filler import PDFFiller
        import tempfile
        
        document = self.get_object()
        pdf_filler = PDFFiller()
        
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        
        try:
            if document.template:
                pdf_filler.create_pdf_from_template_data(
                    document=document,
                    template=document.template,
                    output_path=temp_file.name
                )
            else:
                pdf_filler.create_pdf_from_text(
                    text=document.text_content or "No text content",
                    output_path=temp_file.name,
                    title=document.name
                )
            
            response = FileResponse(
                open(temp_file.name, 'rb'),
                as_attachment=True,
                filename=f'{document.name}.pdf'
            )
            return response
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def reprocess(self, request, pk=None):
        """Reprocess document with OCR"""
        document = self.get_object()
        
        if not document.file:
            return Response(
                {'error': 'No file attached to this document'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from ocr_processing.ocr_core import OCREngine
            from django.conf import settings
            import os
            
            file_path = os.path.join(settings.MEDIA_ROOT, document.file.name)
            ocr_engine = OCREngine()
            ocr_result = ocr_engine.extract_text(file_path)
            
            document.text_content = ocr_result.get('text', '')
            document.confidence_score = ocr_result.get('confidence', 0)
            document.processing_status = 'completed'
            document.save()
            
            serializer = self.get_serializer(document)
            return Response(serializer.data)
        except Exception as e:
            document.processing_status = 'failed'
            document.save()
            return Response(
                {'error': f'OCR processing failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class OCRViewSet(viewsets.ViewSet):
    """
    API endpoint for OCR processing
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def process(self, request):
        """Process an image/document with OCR"""
        serializer = OCRProcessSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            from ocr_processing.ocr_core import OCREngine
            from django.core.files.storage import default_storage
            from django.conf import settings
            import os
            
            uploaded_file = serializer.validated_data['file']
            template_id = serializer.validated_data.get('template_id')
            extract_structure = serializer.validated_data.get('extract_structure', False)
            
            # Save uploaded file temporarily
            file_path = default_storage.save(
                f'temp/{uploaded_file.name}',
                uploaded_file
            )
            full_path = os.path.join(settings.MEDIA_ROOT, file_path)
            
            # Process with OCR
            ocr_engine = OCREngine()
            ocr_result = ocr_engine.extract_text(full_path)
            
            result = {
                'text': ocr_result.get('text', ''),
                'confidence': ocr_result.get('confidence', 0),
                'status': 'success'
            }
            
            # If template provided, try to extract structured data
            if template_id:
                template = get_object_or_404(Template, id=template_id)
                # Add template-based extraction logic here
                result['template'] = template.name
            
            # Clean up temp file
            if os.path.exists(full_path):
                os.remove(full_path)
            
            return Response(result)
        except Exception as e:
            return Response(
                {'error': str(e), 'status': 'failed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class StatisticsViewSet(viewsets.ViewSet):
    """
    API endpoint for statistics and analytics
    """
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """Get dashboard statistics"""
        # Total counts
        total_documents = Document.objects.count()
        total_templates = Template.objects.count()
        
        # Recent documents
        recent_documents = Document.objects.all().order_by('-created_at')[:5]
        
        # Documents by template
        documents_by_template = list(
            Template.objects.annotate(
                doc_count=Count('document')
            ).values('name', 'doc_count').order_by('-doc_count')[:10]
        )
        
        # Average confidence score
        avg_confidence = Document.objects.filter(
            confidence_score__isnull=False
        ).aggregate(avg=Avg('confidence_score'))['avg'] or 0
        
        # Processing status breakdown
        status_breakdown = dict(
            Document.objects.values('processing_status').annotate(
                count=Count('id')
            ).values_list('processing_status', 'count')
        )
        
        data = {
            'total_documents': total_documents,
            'total_templates': total_templates,
            'recent_documents': DocumentListSerializer(recent_documents, many=True).data,
            'documents_by_template': documents_by_template,
            'average_confidence': round(avg_confidence, 2),
            'processing_status_breakdown': status_breakdown
        }
        
        serializer = StatisticsSerializer(data)
        return Response(serializer.data)
