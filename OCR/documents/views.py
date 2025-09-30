from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Document
from templates.models import Template


def document_list(request):
    """List all processed documents"""
    documents = Document.objects.all().order_by('-created_at')
    return render(request, 'documents/document_list.html', {'documents': documents})


def document_upload(request):
    """Upload a document for general OCR processing"""
    if request.method == 'POST':
        # TODO: Implement document upload logic
        messages.success(request, 'Document upload functionality will be implemented here')
        return redirect('documents:document_list')
    return render(request, 'documents/document_upload.html')


def document_upload_with_template(request, template_id):
    """Upload a document using a specific template"""
    template = get_object_or_404(Template, id=template_id)
    if request.method == 'POST':
        # TODO: Implement template-based document upload logic
        messages.success(request, f'Document upload with template "{template.name}" will be implemented here')
        return redirect('documents:document_list')
    return render(request, 'documents/document_upload_template.html', {'template': template})


def document_detail(request, document_id):
    """View document details and extracted data"""
    document = get_object_or_404(Document, id=document_id)
    return render(request, 'documents/document_detail.html', {'document': document})


def document_edit(request, document_id):
    """Edit extracted document data"""
    document = get_object_or_404(Document, id=document_id)
    if request.method == 'POST':
        # TODO: Implement document data editing logic
        messages.success(request, 'Document edit functionality will be implemented here')
        return redirect('documents:document_detail', document_id=document_id)
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
        # TODO: Implement document reprocessing logic
        messages.info(request, 'Document reprocessing functionality will be implemented here')
        return redirect('documents:document_detail', document_id=document_id)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
