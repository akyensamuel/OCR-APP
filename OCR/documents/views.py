from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Document
from templates.models import Template


def document_list(request):
    """List all processed documents"""
    documents = Document.objects.all().order_by('-created_at')
    return render(request, 'documents/document_list.html', {'documents': documents})


def document_upload(request):
    """Upload a document for general OCR processing"""
    if request.method == 'POST':
        try:
            uploaded_file = request.FILES.get('document_file')
            if not uploaded_file:
                messages.error(request, 'No file selected')
                return redirect('documents:document_upload')
            
            # Process with OCR
            from ocr_processing.ocr_core import OCREngine
            from django.core.files.storage import default_storage
            from django.conf import settings
            import os
            
            # Save uploaded file
            file_path = default_storage.save(
                f'uploads/documents/{uploaded_file.name}',
                uploaded_file
            )
            full_path = os.path.join(settings.MEDIA_ROOT, file_path)
            
            # Initialize OCR and extract text
            ocr_engine = OCREngine()
            ocr_result = ocr_engine.extract_text(full_path)
            
            # Create Document record
            document = Document.objects.create(
                name=uploaded_file.name,
                file=file_path,
                extracted_data={
                    'text': ocr_result.text,
                    'confidence': ocr_result.confidence,
                    'engine': ocr_result.engine
                },
                processing_status='completed'
            )
            
            messages.success(request, f'Document processed successfully! Confidence: {ocr_result.confidence:.1f}%')
            return redirect('documents:document_detail', document_id=document.pk)
            
        except Exception as e:
            messages.error(request, f'Error processing document: {str(e)}')
            return redirect('documents:document_upload')
    
    return render(request, 'documents/document_upload.html')


def document_upload_with_template(request, template_id):
    """Upload a document using a specific template"""
    template = get_object_or_404(Template, id=template_id)
    if request.method == 'POST':
        try:
            uploaded_file = request.FILES.get('document_file')
            if not uploaded_file:
                messages.error(request, 'No file selected')
                return redirect('documents:document_upload_with_template', template_id=template_id)
            
            # Process with template
            from ocr_processing.ocr_core import OCREngine, TemplateProcessor
            from django.core.files.storage import default_storage
            from django.conf import settings
            import os
            
            # Save uploaded file
            file_path = default_storage.save(
                f'uploads/documents/{uploaded_file.name}',
                uploaded_file
            )
            full_path = os.path.join(settings.MEDIA_ROOT, file_path)
            
            # Initialize OCR and process with template
            ocr_engine = OCREngine()
            template_processor = TemplateProcessor(ocr_engine)
            
            extracted_fields = template_processor.process_document_with_template(
                full_path, template.structure or {}
            )
            
            # Create Document record
            document = Document.objects.create(
                name=uploaded_file.name,
                file=file_path,
                template=template,
                extracted_data={
                    'fields': [
                        {
                            'name': field.name,
                            'value': field.value,
                            'confidence': field.confidence
                        } for field in extracted_fields
                    ]
                },
                processing_status='completed'
            )
            
            messages.success(request, f'Document processed with template "{template.name}". Extracted {len(extracted_fields)} fields.')
            return redirect('documents:document_detail', document_id=document.pk)
            
        except Exception as e:
            messages.error(request, f'Error processing document: {str(e)}')
            return redirect('documents:document_upload_with_template', template_id=template_id)
    
    return render(request, 'documents/document_upload_template.html', {'template': template})


def document_detail(request, document_id):
    """View document details and extracted data"""
    document = get_object_or_404(Document, id=document_id)
    return render(request, 'documents/document_detail.html', {'document': document})


def document_edit(request, document_id):
    """Edit extracted document data"""
    document = get_object_or_404(Document, id=document_id)
    
    if request.method == 'POST':
        try:
            # Handle different types of extracted data
            if document.template and document.extracted_data and 'fields' in document.extracted_data:
                # Template-based document: edit individual fields
                updated_fields = []
                
                for i, field in enumerate(document.extracted_data['fields']):
                    field_name = field.get('name', f'field_{i}')
                    new_value = request.POST.get(f'field_{i}_value', field.get('value', ''))
                    
                    updated_fields.append({
                        'name': field_name,
                        'value': new_value,
                        'confidence': field.get('confidence', 0),
                        'manually_edited': True
                    })
                
                document.extracted_data['fields'] = updated_fields
                document.extracted_data['last_edited'] = str(timezone.now())
                
                messages.success(request, f'Document fields updated successfully. Modified {len(updated_fields)} fields.')
                
            else:
                # General text document: edit raw text
                new_text = request.POST.get('extracted_text', '')
                if document.extracted_data:
                    document.extracted_data['text'] = new_text
                    document.extracted_data['manually_edited'] = True
                    document.extracted_data['last_edited'] = str(timezone.now())
                else:
                    document.extracted_data = {
                        'text': new_text,
                        'manually_edited': True,
                        'last_edited': str(timezone.now())
                    }
                
                messages.success(request, 'Document text updated successfully.')
            
            document.save()
            return redirect('documents:document_detail', document_id=document_id)
            
        except Exception as e:
            messages.error(request, f'Error updating document: {str(e)}')
    
    return render(request, 'documents/document_edit.html', {'document': document})


def document_delete(request, document_id):
    """Delete a document"""
    document = get_object_or_404(Document, id=document_id)
    if request.method == 'POST':
        document.delete()
        messages.success(request, f'Document "{document.name}" has been deleted.')
        return redirect('documents:document_list')
    return render(request, 'documents/document_delete.html', {'document': document})


def document_reprocess(request, document_id):
    """Reprocess a document with OCR"""
    document = get_object_or_404(Document, id=document_id)
    if request.method == 'POST':
        try:
            from ocr_processing.ocr_core import OCREngine, TemplateProcessor
            from django.conf import settings
            import os
            
            # Get full file path
            full_path = os.path.join(settings.MEDIA_ROOT, document.file.name)
            
            # Initialize OCR engine
            ocr_engine = OCREngine()
            
            if document.template:
                # Reprocess with template
                template_processor = TemplateProcessor(ocr_engine)
                extracted_fields = template_processor.process_document_with_template(
                    full_path, document.template.structure or {}
                )
                
                document.extracted_data = {
                    'fields': [
                        {
                            'name': field.name,
                            'value': field.value,
                            'confidence': field.confidence
                        } for field in extracted_fields
                    ]
                }
                messages.success(request, f'Document reprocessed with template. Extracted {len(extracted_fields)} fields.')
            else:
                # General OCR reprocessing
                ocr_result = ocr_engine.extract_text(full_path)
                document.extracted_data = {
                    'text': ocr_result.text,
                    'confidence': ocr_result.confidence,
                    'engine': ocr_result.engine
                }
                messages.success(request, f'Document reprocessed. Confidence: {ocr_result.confidence:.1f}%')
            
            document.processing_status = 'completed'
            document.save()
            
            return redirect('documents:document_detail', document_id=document_id)
            
        except Exception as e:
            messages.error(request, f'Error reprocessing document: {str(e)}')
            return redirect('documents:document_detail', document_id=document_id)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})


def document_export(request, document_id):
    """Export document as text file"""
    document = get_object_or_404(Document, id=document_id)
    
    # Prepare export content
    if document.template and document.extracted_data and 'fields' in document.extracted_data:
        # Template-based export with structured data
        content_lines = [f"Document: {document.name}"]
        content_lines.append(f"Template: {document.template.name}")
        content_lines.append(f"Processed: {document.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        content_lines.append("=" * 50)
        content_lines.append("")
        
        for field in document.extracted_data['fields']:
            field_name = field.get('name', 'Unknown Field')
            field_value = field.get('value', '')
            confidence = field.get('confidence', 0)
            content_lines.append(f"{field_name}: {field_value}")
            if confidence:
                content_lines.append(f"  [Confidence: {confidence:.1f}%]")
            content_lines.append("")
        
        export_content = '\n'.join(content_lines)
        filename = f"{document.name}_structured.txt"
        
    else:
        # General text export
        export_content = document.extracted_data.get('text', '') if document.extracted_data else ''
        filename = f"{document.name}_text.txt"
    
    # Create response
    response = HttpResponse(export_content, content_type='text/plain; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response
