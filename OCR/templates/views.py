from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import Template
import json
import logging

logger = logging.getLogger(__name__)


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
            
            # 💾 Save file to database instead of file system
            from basemode.file_storage import save_file_to_db, get_temp_file_path, cleanup_temp_file, read_file_from_path
            
            file_info = save_file_to_db(file_obj)
            
            # Create template object with file stored in database
            template = Template.objects.create(
                name=name,
                description=description,
                file_data=file_info['file_data'],
                file_name=file_info['file_name'],
                file_type=file_info['file_type'],
                file_size=file_info['file_size'],
                created_by=request.user if request.user.is_authenticated else None,
                processing_status='pending'
            )
            
            # Process the template using advanced table detection
            try:
                from ocr_processing.ocr_core import OCREngine
                from ocr_processing.table_detector import TableDetector
                import os
                
                # Create temporary file for processing
                file_path = get_temp_file_path(template.file_data, template.file_name)
                
                # Initialize OCR engine
                ocr_engine = OCREngine()
                
                # Check if OCR engines are available
                if not ocr_engine.tesseract_available and ocr_engine.easyocr_reader is None:
                    # No OCR engines available, create a mock structure
                    structure_data = {
                        'fields': [
                            {'name': 'Field 1', 'type': 'text', 'required': True},
                            {'name': 'Field 2', 'type': 'text', 'required': True},
                            {'name': 'Field 3', 'type': 'text', 'required': True}
                        ],
                        'total_fields': 3,
                        'extraction_confidence': 50.0,
                        'ocr_engine': 'mock_fallback',
                        'detection_method': 'fallback',
                        'note': 'OCR engines not available. Install Tesseract for actual table detection.'
                    }
                else:
                    # 🚀 Use ENHANCED multi-strategy table detector for complex images
                    try:
                        from ocr_processing.enhanced_table_detector import EnhancedTableDetector
                        
                        enhanced_detector = EnhancedTableDetector(ocr_engine)
                        table_structure, best_strategy = enhanced_detector.detect_with_multiple_strategies(file_path)
                        
                        if table_structure and hasattr(table_structure, 'cells') and len(table_structure.cells) > 0:
                            # Successfully detected with enhanced detector
                            from ocr_processing.table_detector import TableDetector
                            table_detector = TableDetector(ocr_engine)
                            structure_data = table_detector.structure_to_dict(table_structure)
                            structure_data['detection_method'] = f'enhanced_{best_strategy.method}'
                            structure_data['detection_strategy'] = best_strategy.name
                            structure_data['detection_confidence'] = best_strategy.confidence
                            structure_data['note'] = (
                                f'[SMART] Detection: Used {best_strategy.name} strategy '
                                f'(confidence: {best_strategy.confidence:.1f}%). '
                                f'Detected {table_structure.rows}x{table_structure.cols} table '
                                f'with {len(table_structure.cells)} cells.'
                            )
                            
                            # Save all strategies tried
                            structure_data['strategies_tried'] = [
                                {
                                    'name': s.name,
                                    'confidence': s.confidence,
                                    'cells_found': s.cells_found
                                }
                                for s in enhanced_detector.strategies
                            ]
                            
                            # Export as Excel template to temp file, then save to DB
                            import tempfile
                            excel_temp = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
                            excel_path = excel_temp.name
                            excel_temp.close()
                            table_detector.export_to_excel_template(table_structure, excel_path)
                            
                            # Read Excel file and save to database
                            excel_info = read_file_from_path(excel_path)
                            template.excel_template_data = excel_info['file_data']
                            template.excel_template_name = f"{template.name}_template.xlsx"
                            cleanup_temp_file(excel_path)
                            
                            # Save visualization to temp file, then save to DB
                            viz_temp = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
                            viz_path = viz_temp.name
                            viz_temp.close()
                            from ocr_processing.table_detector import visualize_table_detection
                            visualize_table_detection(file_path, table_structure, viz_path)
                            
                            # Read visualization and save to database
                            viz_info = read_file_from_path(viz_path)
                            template.visualization_data = viz_info['file_data']
                            template.visualization_name = f"{template.name}_detected.jpg"
                            cleanup_temp_file(viz_path)
                        else:
                            raise ValueError("Enhanced detection found no cells")
                            
                    except Exception as enhanced_error:
                        # Fallback to standard detection if enhanced fails
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.warning(f"Enhanced detection failed: {enhanced_error}. Trying standard detection...")
                        
                        table_detector = TableDetector(ocr_engine)
                        table_structure = table_detector.detect_table_structure(
                            file_path, 
                            method="morphology"
                        )
                        
                        if table_structure and len(table_structure.headers) > 0:
                            structure_data = table_detector.structure_to_dict(table_structure)
                            structure_data['detection_method'] = 'standard_table_detection'
                            structure_data['note'] = f'Standard detection: {table_structure.rows}x{table_structure.cols} table'
                        else:
                            # Final fallback to simple field extraction
                            from ocr_processing.ocr_core import TemplateProcessor
                            template_processor = TemplateProcessor(ocr_engine)
                            structure_data = template_processor.extract_structure_from_template(file_path)
                            structure_data['detection_method'] = 'simple_extraction'
                            structure_data['note'] = 'No clear table structure detected. Using simple field extraction.'
                
                # Update template with extracted structure
                template.structure = structure_data
                template.processing_status = 'completed'
                template.save()
                
                # Cleanup temporary file
                cleanup_temp_file(file_path)
                
                result = {'success': True, 'structure': structure_data}
                
            except Exception as e:
                template.processing_status = 'failed'
                template.save()
                # Cleanup temporary file on error
                try:
                    cleanup_temp_file(file_path)
                except:
                    pass
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
            from ocr_processing.table_detector import TableDetector
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
            
            # Initialize OCR and process document
            ocr_engine = OCREngine()
            
            # Check if template has table structure (new detection method)
            has_table_structure = (
                template.structure and 
                ('headers' in template.structure or 'cells' in template.structure)
            )
            
            extracted_data = {}
            
            if has_table_structure:
                # 🚀 Use ENHANCED multi-strategy detection for complex documents
                try:
                    from ocr_processing.enhanced_table_detector import EnhancedTableDetector
                    
                    enhanced_detector = EnhancedTableDetector(ocr_engine)
                    table_structure, best_strategy = enhanced_detector.detect_with_multiple_strategies(full_path)
                    
                    if table_structure and hasattr(table_structure, 'cells') and len(table_structure.cells) > 0:
                        # Successfully detected with enhanced detector
                        table_detector = TableDetector(ocr_engine)
                        extracted_data = table_detector.structure_to_dict(table_structure)
                        cell_count = len(extracted_data.get('cells', []))
                        success_message = (
                            f'[SMART] Detection: Extracted {cell_count} cells from table. '
                            f'Used {best_strategy.name} strategy (confidence: {best_strategy.confidence:.1f}%).'
                        )
                    else:
                        raise ValueError("Enhanced detection found no cells")
                        
                except Exception as enhanced_error:
                    # Fallback to standard detection
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Enhanced detection failed: {enhanced_error}. Trying standard detection...")
                    
                    table_detector = TableDetector(ocr_engine)
                    table_structure = table_detector.detect_table_structure(full_path, method="morphology")
                    
                    if table_structure:
                        extracted_data = table_detector.structure_to_dict(table_structure)
                        cell_count = len(extracted_data.get('cells', []))
                        success_message = f'Document processed successfully. Extracted {cell_count} cells from table.'
                    else:
                        # Final fallback to template processor
                        template_processor = TemplateProcessor(ocr_engine)
                        extracted_fields = template_processor.process_document_with_template(
                            full_path, template.structure or {}
                        )
                        extracted_data = {
                            'fields': [
                                {
                                    'name': field.name,
                                    'value': field.value,
                                    'confidence': field.confidence
                                } for field in extracted_fields
                            ]
                        }
                        success_message = f'Document processed successfully. Extracted {len(extracted_fields)} fields (fallback method).'
            else:
                # Old template format - use template processor
                template_processor = TemplateProcessor(ocr_engine)
                extracted_fields = template_processor.process_document_with_template(
                    full_path, template.structure or {}
                )
                extracted_data = {
                    'fields': [
                        {
                            'name': field.name,
                            'value': field.value,
                            'confidence': field.confidence
                        } for field in extracted_fields
                    ]
                }
                success_message = f'Document processed successfully. Extracted {len(extracted_fields)} fields.'
            
            # Create Document record
            document = Document.objects.create(
                name=uploaded_file.name,
                file=file_path,
                template=template,
                uploaded_by=uploaded_by,
                extracted_data=extracted_data,
                processing_status='completed'
            )
            
            return JsonResponse({
                'success': True,
                'message': success_message,
                'redirect_url': f'/documents/{document.pk}/'
            })
            
        except Exception as e:
            import traceback
            traceback.print_exc()
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


def template_editor(request, template_id):
    """Interactive Excel-like template editor"""
    template = get_object_or_404(Template, id=template_id)
    return render(request, 'templates/template_editor.html', {'template': template})


@csrf_exempt
def template_editor_get_data(request, template_id):
    """Get template structure data for editor"""
    if request.method == 'GET':
        try:
            template = get_object_or_404(Template, id=template_id)
            structure = template.structure or {}
            
            # Prepare data for editor
            cells = structure.get('cells', [])
            headers = structure.get('headers', {})
            rows = structure.get('rows', 0)
            cols = structure.get('cols', 0)
            
            return JsonResponse({
                'success': True,
                'data': {
                    'cells': cells,
                    'headers': headers,
                    'rows': rows,
                    'cols': cols,
                    'detection_method': structure.get('detection_method', 'unknown'),
                    'detection_confidence': structure.get('detection_confidence', 0)
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)


@csrf_exempt
def template_editor_save_data(request, template_id):
    """Save edited template structure"""
    if request.method == 'POST':
        try:
            template = get_object_or_404(Template, id=template_id)
            data = json.loads(request.body)
            
            # Update template structure
            structure = template.structure or {}
            structure['cells'] = data.get('cells', [])
            structure['headers'] = data.get('headers', {})
            structure['rows'] = data.get('rows', 0)
            structure['cols'] = data.get('cols', 0)
            structure['manually_edited'] = True
            structure['last_edited'] = str(timezone.now())
            
            template.structure = structure
            template.save()
            
            # Re-export Excel template with updated structure
            try:
                from ocr_processing.table_detector import TableDetector, TableStructure, CellInfo
                
                cell_objects = []
                for cell_data in structure['cells']:
                    cell_objects.append(CellInfo(
                        row=cell_data.get('row', 0),
                        col=cell_data.get('col', 0),
                        x=cell_data.get('x', 0),
                        y=cell_data.get('y', 0),
                        width=cell_data.get('width', 0),
                        height=cell_data.get('height', 0),
                        text=cell_data.get('text', ''),
                        confidence=cell_data.get('confidence', 0),
                        is_header=cell_data.get('is_header', False)
                    ))
                
                table_structure = TableStructure(
                    rows=structure['rows'],
                    cols=structure['cols'],
                    cells=cell_objects,
                    headers=structure['headers'],
                    grid_confidence=structure.get('grid_confidence', 85.0)
                )
                
                # Export to Excel using TableDetector
                table_detector = TableDetector()
                excel_path = template.file.path.rsplit('.', 1)[0] + '_template.xlsx'
                table_detector.export_to_excel_template(table_structure, excel_path)
                
            except Exception as excel_error:
                logger.warning(f"Could not re-export Excel template: {excel_error}")
            
            return JsonResponse({
                'success': True,
                'message': 'Template structure saved successfully',
                'cell_count': len(structure['cells'])
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)


@csrf_exempt
def template_editor_add_row(request, template_id):
    """Add a new row to the template"""
    if request.method == 'POST':
        try:
            template = get_object_or_404(Template, id=template_id)
            data = json.loads(request.body)
            position = data.get('position', 'end')  # 'start', 'end', or row index
            
            structure = template.structure or {}
            cells = structure.get('cells', [])
            rows = structure.get('rows', 0)
            cols = structure.get('cols', 0)
            
            # Determine insertion row
            if position == 'end':
                new_row_idx = rows
            elif position == 'start':
                new_row_idx = 0
                # Shift all existing rows down
                for cell in cells:
                    cell['row'] += 1
            else:
                new_row_idx = int(position)
                # Shift rows at and after position
                for cell in cells:
                    if cell['row'] >= new_row_idx:
                        cell['row'] += 1
            
            # Add new empty cells for the row
            for col_idx in range(cols):
                cells.append({
                    'row': new_row_idx,
                    'col': col_idx,
                    'text': '',
                    'confidence': 0,
                    'x': 0,
                    'y': 0,
                    'width': 100,
                    'height': 30,
                    'is_header': False,
                    'bbox': [0, 0, 100, 30]
                })
            
            structure['cells'] = cells
            structure['rows'] = rows + 1
            template.structure = structure
            template.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Row added at position {new_row_idx}',
                'new_row': new_row_idx,
                'total_rows': rows + 1
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)


@csrf_exempt
def template_editor_delete_row(request, template_id):
    """Delete a row from the template"""
    if request.method == 'POST':
        try:
            template = get_object_or_404(Template, id=template_id)
            data = json.loads(request.body)
            row_idx = int(data.get('row'))
            
            structure = template.structure or {}
            cells = structure.get('cells', [])
            rows = structure.get('rows', 0)
            
            # Remove cells in the specified row
            cells = [cell for cell in cells if cell['row'] != row_idx]
            
            # Shift cells after the deleted row up
            for cell in cells:
                if cell['row'] > row_idx:
                    cell['row'] -= 1
            
            structure['cells'] = cells
            structure['rows'] = max(0, rows - 1)
            template.structure = structure
            template.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Row {row_idx} deleted',
                'total_rows': structure['rows']
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)


@csrf_exempt
def template_editor_add_column(request, template_id):
    """Add a new column to the template"""
    if request.method == 'POST':
        try:
            template = get_object_or_404(Template, id=template_id)
            data = json.loads(request.body)
            position = data.get('position', 'end')  # 'start', 'end', or column index
            
            structure = template.structure or {}
            cells = structure.get('cells', [])
            rows = structure.get('rows', 0)
            cols = structure.get('cols', 0)
            
            # Determine insertion column
            if position == 'end':
                new_col_idx = cols
            elif position == 'start':
                new_col_idx = 0
                # Shift all existing columns right
                for cell in cells:
                    cell['col'] += 1
            else:
                new_col_idx = int(position)
                # Shift columns at and after position
                for cell in cells:
                    if cell['col'] >= new_col_idx:
                        cell['col'] += 1
            
            # Add new empty cells for the column
            for row_idx in range(rows):
                cells.append({
                    'row': row_idx,
                    'col': new_col_idx,
                    'text': '',
                    'confidence': 0,
                    'x': 0,
                    'y': 0,
                    'width': 100,
                    'height': 30,
                    'is_header': (row_idx == 0),
                    'bbox': [0, 0, 100, 30]
                })
            
            structure['cells'] = cells
            structure['cols'] = cols + 1
            template.structure = structure
            template.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Column added at position {new_col_idx}',
                'new_col': new_col_idx,
                'total_cols': cols + 1
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)


@csrf_exempt
def template_editor_delete_column(request, template_id):
    """Delete a column from the template"""
    if request.method == 'POST':
        try:
            template = get_object_or_404(Template, id=template_id)
            data = json.loads(request.body)
            col_idx = int(data.get('col'))
            
            structure = template.structure or {}
            cells = structure.get('cells', [])
            cols = structure.get('cols', 0)
            
            # Remove cells in the specified column
            cells = [cell for cell in cells if cell['col'] != col_idx]
            
            # Shift cells after the deleted column left
            for cell in cells:
                if cell['col'] > col_idx:
                    cell['col'] -= 1
            
            structure['cells'] = cells
            structure['cols'] = max(0, cols - 1)
            template.structure = structure
            template.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Column {col_idx} deleted',
                'total_cols': structure['cols']
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)


@csrf_exempt
def template_editor_update_cell(request, template_id):
    """Update a single cell's data"""
    if request.method == 'POST':
        try:
            template = get_object_or_404(Template, id=template_id)
            data = json.loads(request.body)
            
            row = int(data.get('row'))
            col = int(data.get('col'))
            text = data.get('text', '')
            is_header = data.get('is_header', False)
            
            structure = template.structure or {}
            cells = structure.get('cells', [])
            
            # Find and update the cell
            cell_found = False
            for cell in cells:
                if cell['row'] == row and cell['col'] == col:
                    cell['text'] = text
                    cell['is_header'] = is_header
                    cell_found = True
                    break
            
            if not cell_found:
                # Create new cell if it doesn't exist
                cells.append({
                    'row': row,
                    'col': col,
                    'text': text,
                    'confidence': 0,
                    'x': 0,
                    'y': 0,
                    'width': 100,
                    'height': 30,
                    'is_header': is_header,
                    'bbox': [0, 0, 100, 30]
                })
            
            structure['cells'] = cells
            template.structure = structure
            template.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Cell updated successfully'
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)


def serve_template_file(request, template_id):
    """Serve template file from database"""
    from django.http import HttpResponse
    from basemode.file_storage import serve_file_from_db
    
    template = get_object_or_404(Template, id=template_id)
    
    if not template.file_data:
        # Fallback to file system if no DB data
        if template.file:
            from django.http import FileResponse
            return FileResponse(template.file.open(), content_type=template.file_type or 'application/octet-stream')
        return HttpResponse('File not found', status=404)
    
    return serve_file_from_db(
        template.file_data,
        template.file_name or 'template_file',
        template.file_type or 'application/octet-stream',
        as_attachment=False
    )


def serve_template_excel(request, template_id):
    """Serve Excel template from database"""
    from django.http import HttpResponse
    from basemode.file_storage import serve_file_from_db
    
    template = get_object_or_404(Template, id=template_id)
    
    if not template.excel_template_data:
        return HttpResponse('Excel template not found', status=404)
    
    return serve_file_from_db(
        template.excel_template_data,
        template.excel_template_name or f'{template.name}_template.xlsx',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True
    )


def serve_template_visualization(request, template_id):
    """Serve visualization image from database"""
    from django.http import HttpResponse
    from basemode.file_storage import serve_file_from_db
    
    template = get_object_or_404(Template, id=template_id)
    
    if not template.visualization_data:
        return HttpResponse('Visualization not found', status=404)
    
    return serve_file_from_db(
        template.visualization_data,
        template.visualization_name or f'{template.name}_detected.jpg',
        'image/jpeg',
        as_attachment=False
    )
