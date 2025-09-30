from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from .models import Template
import json


def template_list(request):
    """List all available templates"""
    templates = Template.objects.filter(is_active=True)
    return render(request, 'templates/template_list.html', {'templates': templates})


def template_upload(request):
    """Upload and process a new template"""
    if request.method == 'POST':
        try:
            # Get form data
            name = request.POST.get('name')
            description = request.POST.get('description', '')
            file_obj = request.FILES.get('file')
            
            if not name or not file_obj:
                return JsonResponse({
                    'success': False,
                    'message': 'Template name and file are required.'
                })
            
            # Create template object
            template = Template.objects.create(
                name=name,
                description=description,
                file=file_obj,
                created_by=request.user,
                processing_status='pending'
            )
            
            # Process the template using OCR service
            from ocr_processing.utils import get_ocr_service
            ocr_service = get_ocr_service()
            
            # Process template in background (for now, process synchronously)
            result = ocr_service.process_template_file(
                file_field=template.file,
                user=request.user,
                template_name=name
            )
            
            if result['success']:
                # Update template with extracted structure
                template.structure = result['structure']
                template.processing_status = 'completed'
                template.save()
                
                return JsonResponse({
                    'success': True,
                    'message': f'Template "{name}" uploaded and processed successfully. Found {len(result["structure"].get("fields", {}))} fields.',
                    'template_id': template.pk
                })
            else:
                template.processing_status = 'failed'
                template.save()
                return JsonResponse({
                    'success': False,
                    'message': result.get('message', 'Failed to process template.')
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error uploading template: {str(e)}'
            })
    
    return render(request, 'templates/template_upload.html')


def template_detail(request, template_id):
    """View template details and structure"""
    template = get_object_or_404(Template, id=template_id)
    return render(request, 'templates/template_detail.html', {'template': template})


def template_edit(request, template_id):
    """Edit template information"""
    template = get_object_or_404(Template, id=template_id)
    if request.method == 'POST':
        # TODO: Implement template editing logic
        messages.success(request, 'Template edit functionality will be implemented here')
        return redirect('templates:template_detail', template_id=template_id)
    return render(request, 'templates/template_edit.html', {'template': template})


def template_delete(request, template_id):
    """Delete a template"""
    template = get_object_or_404(Template, id=template_id)
    if request.method == 'POST':
        template.delete()
        messages.success(request, f'Template "{template.name}" has been deleted.')
        return redirect('templates:template_list')
    return render(request, 'templates/template_delete.html', {'template': template})


def process_template(request, template_id):
    """Process/reprocess template structure extraction"""
    template = get_object_or_404(Template, id=template_id)
    if request.method == 'POST':
        # TODO: Implement template processing logic
        messages.info(request, 'Template processing functionality will be implemented here')
        return redirect('templates:template_detail', template_id=template_id)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
