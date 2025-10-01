from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.files.storage import default_storage
from django.conf import settings
import json
import os
from .models import TextDocument
from ocr_processing.ocr_core import OCREngine


def editor_home(request):
    """Home page for text editor"""
    recent_documents = TextDocument.objects.order_by('-created_at')[:5]
    context = {
        'recent_documents': recent_documents,
        'total_documents': TextDocument.objects.count(),
    }
    return render(request, 'editor/editor_home.html', context)


def upload_text_document(request):
    """Upload and process document for text editing"""
    if request.method == 'POST':
        try:
            uploaded_file = request.FILES.get('document_file')
            if not uploaded_file:
                messages.error(request, 'No file selected')
                return redirect('editor:editor_home')
            
            # Save uploaded file
            file_path = default_storage.save(
                f'uploads/editor/{uploaded_file.name}',
                uploaded_file
            )
            full_path = os.path.join(settings.MEDIA_ROOT, file_path)
            
            # Process with OCR
            ocr_engine = OCREngine()
            ocr_result = ocr_engine.extract_text(full_path)
            
            # Create TextDocument
            document = TextDocument.objects.create(
                title=uploaded_file.name,
                original_file=file_path,
                extracted_text=ocr_result.text,
                confidence_score=ocr_result.confidence,
                processing_status='completed'
            )
            
            messages.success(request, f'Document processed successfully! Confidence: {ocr_result.confidence:.1f}%')
            return redirect('editor:edit_text_document', document_id=document.id)
            
        except Exception as e:
            messages.error(request, f'Error processing document: {str(e)}')
            return redirect('editor:editor_home')
    
    return render(request, 'editor/upload_document.html')


def edit_text_document(request, document_id):
    """Edit extracted text"""
    document = get_object_or_404(TextDocument, id=document_id)
    context = {
        'document': document,
    }
    return render(request, 'editor/edit_document.html', context)


@csrf_exempt
def save_text_document(request, document_id):
    """Save edited text via AJAX"""
    if request.method == 'POST':
        try:
            document = get_object_or_404(TextDocument, id=document_id)
            data = json.loads(request.body)
            
            document.extracted_text = data.get('text', '')
            document.save()
            
            return JsonResponse({'success': True, 'message': 'Text saved successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


def export_text_document(request, document_id):
    """Export document as text file"""
    document = get_object_or_404(TextDocument, id=document_id)
    
    response = HttpResponse(document.extracted_text, content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename="{document.title}.txt"'
    
    return response


def delete_text_document(request, document_id):
    """Delete text document"""
    document = get_object_or_404(TextDocument, id=document_id)
    
    if request.method == 'POST':
        # Delete associated files
        if document.original_file:
            try:
                default_storage.delete(document.original_file.name)
            except:
                pass
        
        document.delete()
        messages.success(request, 'Document deleted successfully')
        return redirect('editor:text_document_list')
    
    context = {'document': document}
    return render(request, 'editor/delete_confirm.html', context)


def text_document_list(request):
    """List all text documents"""
    documents = TextDocument.objects.order_by('-created_at')
    context = {
        'documents': documents,
    }
    return render(request, 'editor/document_list.html', context)


def document_api_detail(request, document_id):
    """API endpoint for document details (for preview modal)"""
    try:
        document = get_object_or_404(TextDocument, id=document_id)
        
        # Get file URL if available
        file_url = ''
        if document.original_file:
            try:
                file_url = document.original_file.url
            except:
                file_url = str(document.original_file) if document.original_file else ''
        
        return JsonResponse({
            'success': True,
            'document': {
                'id': document.id,
                'title': document.title,
                'extracted_text': document.extracted_text,
                'confidence_score': document.confidence_score,
                'word_count': document.word_count,
                'char_count': document.char_count,
                'created_at': document.created_at.strftime('%Y-%m-%d %H:%M'),
                'processing_status': document.get_processing_status_display(),
                'original_file': file_url,
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


def reprocess_text_document(request, document_id):
    """Reprocess a text document with OCR"""
    document = get_object_or_404(TextDocument, id=document_id)
    
    if request.method == 'POST':
        try:
            # Check if original file exists
            if not document.original_file:
                messages.error(request, 'No original file available for reprocessing')
                return redirect('editor:document_list')
            
            # Get full file path
            full_path = os.path.join(settings.MEDIA_ROOT, document.original_file.name)
            
            if not os.path.exists(full_path):
                messages.error(request, 'Original file not found')
                return redirect('editor:document_list')
            
            # Reprocess with OCR
            document.processing_status = 'processing'
            document.save()
            
            ocr_engine = OCREngine()
            ocr_result = ocr_engine.extract_text(full_path)
            
            # Update document
            document.extracted_text = ocr_result.text
            document.confidence_score = ocr_result.confidence
            document.processing_status = 'completed'
            document.save()
            
            messages.success(
                request, 
                f'Document reprocessed successfully! Confidence: {ocr_result.confidence:.1f}%'
            )
            return redirect('editor:edit_text_document', document_id=document.id)
            
        except Exception as e:
            document.processing_status = 'failed'
            document.save()
            messages.error(request, f'Error reprocessing document: {str(e)}')
            return redirect('editor:document_list')
    
    # GET request - show confirmation page
    context = {
        'document': document,
    }
    return render(request, 'editor/reprocess_confirm.html', context)

