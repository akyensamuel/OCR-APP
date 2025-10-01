from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import Template
import json


def home(request):
    """Home page with overview of OCR workflows"""
    context = {
        'total_templates': Template.objects.filter(is_active=True).count(),
        'recent_templates': Template.objects.filter(is_active=True).order_by('-created_at')[:3],
    }
    return render(request, 'base/home.html', context)


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
                messages.error(request, 'Template name and file are required.')
                return redirect('templates:template_upload')
            
            # Create template object
            template = Template.objects.create(
                name=name,
                description=description,
                file=file_obj,
                created_by=request.user if request.user.is_authenticated else None,
                processing_status='pending'
            )
            
            # Process the template using OCR core
            try:
                from ocr_processing.ocr_core import OCREngine, TemplateProcessor
                import os
                from django.conf import settings
                
                # Get full file path
                file_path = os.path.join(settings.MEDIA_ROOT, template.file.name)
                
                # Initialize OCR engine and template processor
                ocr_engine = OCREngine()
                template_processor = TemplateProcessor(ocr_engine)
                
                # Check if OCR engines are available
                if not ocr_engine.tesseract_available and ocr_engine.easyocr_reader is None:
                    # No OCR engines available, create a mock structure based on filename
                    structure_data = {
                        'fields': [
                            {'name': 'Field 1', 'type': 'text', 'required': True},
                            {'name': 'Field 2', 'type': 'text', 'required': True},
                            {'name': 'Field 3', 'type': 'text', 'required': False}
                        ],
                        'total_fields': 3,
                        'extraction_confidence': 50.0,
                        'ocr_engine': 'mock_fallback',
                        'note': 'OCR engines not available. Install Tesseract or fix EasyOCR for actual field detection.'
                    }
                else:
                    # Extract template structure using available OCR
                    structure_data = template_processor.extract_structure_from_template(file_path)
                
                # Update template with extracted structure
                template.structure = structure_data
                template.processing_status = 'completed'
                template.save()
                
                result = {'success': True, 'structure': structure_data}
                
            except Exception as e:
                template.processing_status = 'failed'
                template.save()
                result = {'success': False, 'error': str(e)}
            
            if result['success']:
                messages.success(request, f'Template "{name}" uploaded and processed successfully. Found {len(result["structure"].get("fields", []))} fields.')
                return redirect('templates:template_detail', template_id=template.pk)
            else:
                messages.error(request, f'Failed to process template: {result.get("error", "Unknown error")}')
                return redirect('templates:template_upload')
                
        except Exception as e:
            messages.error(request, f'Error uploading template: {str(e)}')
            return redirect('templates:template_upload')
    
    return render(request, 'templates/template_upload.html')


def template_detail(request, template_id):
    """View template details and structure"""
    template = get_object_or_404(Template, id=template_id)
    return render(request, 'templates/template_detail.html', {'template': template})


def template_edit(request, template_id):
    """Edit template information and structure"""
    template = get_object_or_404(Template, id=template_id)
    
    if request.method == 'POST':
        try:
            # Update basic template info
            template.name = request.POST.get('name', template.name)
            template.description = request.POST.get('description', template.description)
            
            # Handle structure editing
            if 'structure_data' in request.POST:
                structure_json = request.POST.get('structure_data')
                try:
                    structure_data = json.loads(structure_json)
                    
                    # Validate structure data
                    if 'fields' in structure_data:
                        # Update template structure
                        template.structure = structure_data
                        template.save()
                        
                        messages.success(request, f'Template "{template.name}" updated successfully with {len(structure_data["fields"])} fields.')
                        return redirect('templates:template_detail', template_id=template_id)
                    else:
                        messages.error(request, 'Invalid structure data: missing fields')
                        
                except json.JSONDecodeError:
                    messages.error(request, 'Invalid JSON structure data')
            else:
                # Just update basic info
                template.save()
                messages.success(request, f'Template "{template.name}" information updated successfully.')
                return redirect('templates:template_detail', template_id=template_id)
                
        except Exception as e:
            messages.error(request, f'Error updating template: {str(e)}')
    
    return render(request, 'templates/template_edit.html', {'template': template})


@csrf_exempt
def save_template_structure(request, template_id):
    """Save template structure via AJAX"""
    if request.method == 'POST':
        try:
            template = get_object_or_404(Template, id=template_id)
            data = json.loads(request.body)
            
            # Validate and save structure
            fields = data.get('fields', [])
            structure_data = {
                'fields': [
                    {
                        'name': field.get('name', ''),
                        'type': field.get('type', 'text'),
                        'required': field.get('required', True)
                    }
                    for field in fields if field.get('name', '').strip()
                ],
                'total_fields': len([f for f in fields if f.get('name', '').strip()]),
                'last_updated': str(timezone.now()),
                'manually_edited': True
            }
            
            template.structure = structure_data
            template.save()
            
            return JsonResponse({
                'success': True, 
                'message': f'Structure saved with {len(structure_data["fields"])} fields.'
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@csrf_exempt
def reprocess_template(request, template_id):
    """Reprocess template via AJAX"""
    if request.method == 'POST':
        template = get_object_or_404(Template, id=template_id)
        try:
            # Reprocess the template using OCR core
            from ocr_processing.ocr_core import OCREngine, TemplateProcessor
            import os
            from django.conf import settings
            
            # Get full file path
            file_path = os.path.join(settings.MEDIA_ROOT, template.file.name)
            
            # Initialize OCR engine and template processor
            ocr_engine = OCREngine()
            template_processor = TemplateProcessor(ocr_engine)
            
            # Extract template structure
            structure_data = template_processor.extract_structure_from_template(file_path)
            
            # Update template with extracted structure
            template.structure = structure_data
            template.processing_status = 'completed'
            template.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Template reprocessed successfully. Found {len(structure_data.get("fields", []))} fields.',
                'field_count': len(structure_data.get("fields", []))
            })
            
        except Exception as e:
            template.processing_status = 'failed'
            template.save()
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


def template_delete(request, template_id):
    """Delete a template"""
    template = get_object_or_404(Template, id=template_id)
    
    if request.method == 'POST':
        template_name = template.name
        
        # Delete associated files
        if template.file:
            try:
                template.file.delete(save=False)
            except Exception as e:
                print(f"Error deleting template file: {e}")
        
        # Delete the template
        template.delete()
        
        # Handle AJAX requests
        if request.headers.get('Accept') == 'application/json':
            return JsonResponse({
                'success': True,
                'message': f'Template "{template_name}" has been deleted successfully.'
            })
        
        messages.success(request, f'Template "{template_name}" has been deleted successfully.')
        return redirect('templates:template_list')
    
    return render(request, 'templates/template_delete.html', {'template': template})


def template_deactivate(request, template_id):
    """Deactivate/reactivate a template"""
    template = get_object_or_404(Template, id=template_id)
    
    if request.method == 'POST':
        # Toggle active status
        template.is_active = not template.is_active
        template.save()
        
        status = "deactivated" if not template.is_active else "reactivated"
        messages.success(request, f'Template "{template.name}" has been {status}.')
        return redirect('templates:template_detail', template_id=template.pk)
    
    return redirect('templates:template_detail', template_id=template.pk)


def template_archive(request, template_id):
    """Archive a template (soft delete)"""
    template = get_object_or_404(Template, id=template_id)
    
    if request.method == 'POST':
        # Set as inactive and add archived flag
        template.is_active = False
        template.save()
        
        messages.success(request, f'Template "{template.name}" has been archived successfully.')
        return redirect('templates:template_list')
    
    return redirect('templates:template_detail', template_id=template.pk)


def template_duplicate(request, template_id):
    """Create a duplicate/backup copy of a template"""
    original_template = get_object_or_404(Template, id=template_id)
    
    if request.method == 'POST':
        # Create a duplicate by copying the template
        from django.core.files.base import ContentFile
        
        duplicate = Template.objects.create(
            name=f"{original_template.name} (Copy)",
            description=original_template.description,
            structure=original_template.structure,
            created_by=request.user if request.user.is_authenticated else None,
            processing_status=original_template.processing_status,
            is_active=original_template.is_active
        )
        
        # Copy the file if it exists
        if original_template.file:
            try:
                file_content = original_template.file.read()
                duplicate.file.save(
                    original_template.file.name,
                    ContentFile(file_content),
                    save=True
                )
            except Exception as e:
                print(f"Error copying template file: {e}")
        
        messages.success(request, f'Backup copy "{duplicate.name}" created successfully.')
        return redirect('templates:template_detail', template_id=duplicate.pk)
    
    return redirect('templates:template_detail', template_id=template_id)


def template_export(request, template_id):
    """Export template structure as JSON"""
    template = get_object_or_404(Template, id=template_id)
    
    # Prepare export data
    export_data = {
        'name': template.name,
        'description': template.description,
        'structure': template.structure,
        'field_count': template.field_count,
        'created_at': str(template.created_at),
        'updated_at': str(template.updated_at),
    }
    
    # Create JSON response
    import json
    response = JsonResponse(export_data)
    response['Content-Disposition'] = f'attachment; filename="{template.name}_structure.json"'
    
    return response


def process_template(request, template_id):
    """Process documents using this template"""
    template = get_object_or_404(Template, id=template_id)
    
    if request.method == 'POST':
        # Handle document processing with this template
        try:
            uploaded_file = request.FILES.get('document_file')
            if not uploaded_file:
                return JsonResponse({
                    'success': False,
                    'message': 'No document file provided'
                })
            
            # Process document using template structure
            from ocr_processing.ocr_core import OCREngine, TemplateProcessor
            from documents.models import Document
            import os
            from django.conf import settings
            from django.core.files.storage import default_storage
            
            # Save uploaded file
            file_path = default_storage.save(
                f'uploads/documents/{uploaded_file.name}',
                uploaded_file
            )
            full_path = os.path.join(settings.MEDIA_ROOT, file_path)
            
            # Initialize OCR and process document
            ocr_engine = OCREngine()
            template_processor = TemplateProcessor(ocr_engine)
            
            # Extract data using template structure
            extracted_fields = template_processor.process_document_with_template(
                full_path, template.structure or {}
            )
            
            # Create Document record
            # Get current user or create a default user if not authenticated
            if request.user.is_authenticated:
                uploaded_by = request.user
            else:
                # Get or create a default "anonymous" user for unauthenticated uploads
                from django.contrib.auth.models import User
                uploaded_by, created = User.objects.get_or_create(
                    username='anonymous',
                    defaults={
                        'email': 'anonymous@example.com',
                        'first_name': 'Anonymous',
                        'last_name': 'User'
                    }
                )
            
            document = Document.objects.create(
                name=uploaded_file.name,
                file=file_path,
                template=template,
                uploaded_by=uploaded_by,
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
            
            return JsonResponse({
                'success': True,
                'message': f'Document processed successfully. Extracted {len(extracted_fields)} fields.',
                'redirect_url': f'/documents/{document.pk}/'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error processing document: {str(e)}'
            })
    
    # GET request - show the processing form
    context = {
        'template': template,
    }
    return render(request, 'templates/process_template.html', context)


def template_fields_api(request, template_id):
    """API endpoint to get template field structure for preview"""
    try:
        template = get_object_or_404(Template, id=template_id)
        
        # Parse field structure from template
        fields = []
        if template.structure and 'fields' in template.structure:
            fields = template.structure['fields']
            if not isinstance(fields, list):
                fields = []
        
        return JsonResponse({
            'success': True,
            'fields': fields,
            'template_name': template.name,
            'field_count': len(fields)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error loading template fields: {str(e)}',
            'fields': []
        })
