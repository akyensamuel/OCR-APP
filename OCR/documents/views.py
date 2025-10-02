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
            
            # Get current user or create default user
            if request.user.is_authenticated:
                uploaded_by = request.user
            else:
                from django.contrib.auth.models import User
                uploaded_by, created = User.objects.get_or_create(
                    username='anonymous',
                    defaults={
                        'email': 'anonymous@example.com',
                        'first_name': 'Anonymous',
                        'last_name': 'User'
                    }
                )
            
            # Create Document record
            document = Document.objects.create(
                name=uploaded_file.name,
                file=file_path,
                uploaded_by=uploaded_by,
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
            from ocr_processing.ocr_core import OCREngine
            from ocr_processing.table_detector import TableDetector
            from ocr_processing.excel_manager import ExcelTemplateManager
            from django.core.files.storage import default_storage
            from django.core.files import File
            from django.conf import settings
            import os
            
            # Save uploaded file
            file_path = default_storage.save(
                f'uploads/documents/{uploaded_file.name}',
                uploaded_file
            )
            full_path = os.path.join(settings.MEDIA_ROOT, file_path)
            
            # Get current user or create default user
            if request.user.is_authenticated:
                uploaded_by = request.user
            else:
                from django.contrib.auth.models import User
                uploaded_by, created = User.objects.get_or_create(
                    username='anonymous',
                    defaults={
                        'email': 'anonymous@example.com',
                        'first_name': 'Anonymous',
                        'last_name': 'User'
                    }
                )
            
            # Initialize OCR
            ocr_engine = OCREngine()
            
            # Check if template has table structure (new detection method)
            has_table_structure = (
                template.structure and 
                ('headers' in template.structure or 'cells' in template.structure)
            )
            
            extracted_data = {}
            excel_file_path = None
            
            if has_table_structure:
                # Use table detection for processing
                table_detector = TableDetector(ocr_engine)
                table_structure = table_detector.detect_table_structure(full_path, method="morphology")
                
                if table_structure:
                    extracted_data = table_detector.structure_to_dict(table_structure)
                    
                    # Try to fill Excel template if it exists
                    excel_manager = ExcelTemplateManager()
                    template_excel_path = excel_manager.get_template_excel_path(template)
                    
                    if template_excel_path:
                        # Generate output path for populated Excel
                        base_name = os.path.splitext(uploaded_file.name)[0]
                        output_excel_name = f"{base_name}_extracted.xlsx"
                        output_excel_path = os.path.join(
                            settings.MEDIA_ROOT, 
                            'documents', 
                            'excel', 
                            output_excel_name
                        )
                        
                        # Ensure directory exists
                        os.makedirs(os.path.dirname(output_excel_path), exist_ok=True)
                        
                        # Append data to Excel template
                        excel_manager.append_document_to_excel(template_excel_path, extracted_data)
                        
                        # Also create a copy for this specific document
                        import shutil
                        shutil.copy(template_excel_path, output_excel_path)
                        
                        excel_file_path = os.path.join('documents', 'excel', output_excel_name)
                else:
                    messages.warning(request, 'No table structure detected in document. Using fallback extraction.')
            
            else:
                # Fallback to old template processor
                from ocr_processing.ocr_core import TemplateProcessor
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
            
            # Create Document record
            document = Document.objects.create(
                name=uploaded_file.name,
                file=file_path,
                template=template,
                uploaded_by=uploaded_by,
                extracted_data=extracted_data,
                processing_status='completed'
            )
            
            # Attach Excel file if created
            if excel_file_path:
                document.excel_file = excel_file_path
                document.save()
            
            field_count = len(extracted_data.get('fields', [])) or len(extracted_data.get('cells', []))
            messages.success(request, f'Document processed with template "{template.name}". Extracted {field_count} items.')
            return redirect('documents:document_detail', document_id=document.pk)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
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


def document_reextract_field(request, document_id):
    """Re-extract a specific field from the document using OCR"""
    import json
    
    if request.method == 'POST':
        try:
            from ocr_processing.ocr_core import OCREngine, TemplateProcessor
            from django.conf import settings
            import os
            
            document = get_object_or_404(Document, id=document_id)
            
            # Get field name from request
            data = json.loads(request.body)
            field_name = data.get('field_name')
            
            if not field_name:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Field name is required'
                }, status=400)
            
            # Check if document has a template
            if not document.template:
                return JsonResponse({
                    'status': 'error',
                    'message': 'This document has no associated template'
                }, status=400)
            
            # Get document file path
            full_path = os.path.join(settings.MEDIA_ROOT, document.file.name)
            
            if not os.path.exists(full_path):
                return JsonResponse({
                    'status': 'error',
                    'message': 'Original document file not found'
                }, status=404)
            
            # Re-extract the field
            ocr_engine = OCREngine()
            template_processor = TemplateProcessor(ocr_engine)
            
            # Extract all fields again using the template
            extracted_fields = template_processor.process_document_with_template(
                full_path,
                document.template.structure
            )
            
            # Find the specific field
            field_value = None
            field_confidence = None
            
            for field in extracted_fields:
                if field.name == field_name:
                    field_value = field.value
                    field_confidence = field.confidence
                    break
            
            if field_value is None:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Field "{field_name}" not found in extraction result'
                }, status=404)
            
            # Update the document's extracted data for this field
            if document.extracted_data and 'fields' in document.extracted_data:
                for i, field in enumerate(document.extracted_data['fields']):
                    if field.get('name') == field_name:
                        document.extracted_data['fields'][i]['value'] = field_value
                        document.extracted_data['fields'][i]['confidence'] = field_confidence
                        break
                
                document.save()
            
            return JsonResponse({
                'status': 'success',
                'field_name': field_name,
                'field_value': field_value,
                'confidence': field_confidence,
                'message': f'Field "{field_name}" re-extracted successfully'
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Error re-extracting field: {str(e)}'
            }, status=500)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    }, status=405)


def document_download_excel(request, document_id):
    """Download the populated Excel file for a document"""
    document = get_object_or_404(Document, id=document_id)
    
    if not document.excel_file:
        messages.error(request, 'No Excel file available for this document')
        return redirect('documents:document_detail', document_id=document_id)
    
    try:
        from django.conf import settings
        import os
        
        excel_path = os.path.join(settings.MEDIA_ROOT, document.excel_file.name)
        
        if not os.path.exists(excel_path):
            messages.error(request, 'Excel file not found')
            return redirect('documents:document_detail', document_id=document_id)
        
        # Read file and return as response
        with open(excel_path, 'rb') as excel_file:
            response = HttpResponse(
                excel_file.read(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            filename = f"{document.name}_data.xlsx"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
            
    except Exception as e:
        messages.error(request, f'Error downloading Excel file: {str(e)}')
        return redirect('documents:document_detail', document_id=document_id)


def template_export_all_documents(request, template_id):
    """Export all documents for a template into a single Excel file"""
    template = get_object_or_404(Template, id=template_id)
    
    if request.method == 'POST':
        try:
            from ocr_processing.excel_manager import ExcelTemplateManager
            from django.conf import settings
            import os
            from datetime import datetime
            
            # Get custom filename from user
            custom_filename = request.POST.get('export_filename', '')
            if not custom_filename:
                custom_filename = f"{template.name}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            
            if not custom_filename.endswith('.xlsx'):
                custom_filename += '.xlsx'
            
            # Get all documents for this template
            documents = Document.objects.filter(template=template, processing_status='completed')
            
            if not documents.exists():
                messages.error(request, 'No processed documents found for this template')
                return redirect('templates:template_detail', template_id=template_id)
            
            # Create output path
            output_dir = os.path.join(settings.MEDIA_ROOT, 'exports')
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, custom_filename)
            
            # Create consolidated Excel
            excel_manager = ExcelTemplateManager()
            excel_path = excel_manager.create_multi_document_export(
                template, 
                documents, 
                output_path,
                custom_filename
            )
            
            # Return file as download
            with open(excel_path, 'rb') as excel_file:
                response = HttpResponse(
                    excel_file.read(),
                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                response['Content-Disposition'] = f'attachment; filename="{custom_filename}"'
                return response
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            messages.error(request, f'Error exporting documents: {str(e)}')
            return redirect('templates:template_detail', template_id=template_id)
    
    # GET request - show export form
    documents = Document.objects.filter(template=template, processing_status='completed')
    context = {
        'template': template,
        'document_count': documents.count()
    }
    return render(request, 'documents/template_export_form.html', context)


def document_export_excel(request, document_id):
    """Export a single document's data to Excel with custom filename"""
    document = get_object_or_404(Document, id=document_id)
    
    if request.method == 'POST':
        try:
            from ocr_processing.excel_manager import ExcelTemplateManager
            from django.conf import settings
            from datetime import datetime
            import os
            
            # Get custom filename from user
            custom_filename = request.POST.get('export_filename', '')
            if not custom_filename:
                custom_filename = f"{document.name}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            
            if not custom_filename.endswith('.xlsx'):
                custom_filename += '.xlsx'
            
            # Create output path
            output_dir = os.path.join(settings.MEDIA_ROOT, 'exports')
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, custom_filename)
            
            # Create Excel file
            excel_manager = ExcelTemplateManager()
            
            if document.template:
                # Create Excel from template
                excel_path = excel_manager.create_multi_document_export(
                    document.template,
                    [document],
                    output_path,
                    custom_filename
                )
            else:
                # Create simple Excel from extracted data
                from openpyxl import Workbook
                wb = Workbook()
                ws = wb.active
                ws.title = "Extracted Data"
                
                # Write data
                if document.extracted_data and 'text' in document.extracted_data:
                    ws.cell(row=1, column=1, value="Extracted Text")
                    ws.cell(row=2, column=1, value=document.extracted_data['text'])
                
                wb.save(output_path)
                excel_path = output_path
            
            # Return file as download
            with open(excel_path, 'rb') as excel_file:
                response = HttpResponse(
                    excel_file.read(),
                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                response['Content-Disposition'] = f'attachment; filename="{custom_filename}"'
                return response
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            messages.error(request, f'Error exporting to Excel: {str(e)}')
            return redirect('documents:document_detail', document_id=document_id)
    
    # GET request - show export form
    return render(request, 'documents/document_export_form.html', {'document': document})


def document_export_docx(request, document_id):
    """Export a single document's data to Word (DOCX) with custom filename"""
    document = get_object_or_404(Document, id=document_id)
    
    if request.method == 'POST':
        try:
            from ocr_processing.docx_exporter import DocxExporter
            from django.conf import settings
            from datetime import datetime
            import os
            
            # Get custom filename from user
            custom_filename = request.POST.get('export_filename', '')
            if not custom_filename:
                custom_filename = f"{document.name}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
            
            if not custom_filename.endswith('.docx'):
                custom_filename += '.docx'
            
            # Create output path
            output_dir = os.path.join(settings.MEDIA_ROOT, 'exports')
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, custom_filename)
            
            # Create DOCX file
            docx_exporter = DocxExporter()
            
            if document.template:
                # Create structured DOCX from template data
                docx_path = docx_exporter.export_template_data_to_docx(
                    document.extracted_data,
                    document.template,
                    output_path,
                    title=document.name
                )
            else:
                # Create plain text DOCX
                text = document.extracted_data.get('text', '') if document.extracted_data else ''
                metadata = {
                    'Document': document.name,
                    'Processed': document.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'Confidence': f"{document.confidence_score:.1f}%" if document.confidence_score else "N/A"
                }
                docx_path = docx_exporter.export_plain_text_to_docx(
                    text,
                    output_path,
                    title=document.name,
                    metadata=metadata
                )
            
            # Return file as download
            with open(docx_path, 'rb') as docx_file:
                response = HttpResponse(
                    docx_file.read(),
                    content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                )
                response['Content-Disposition'] = f'attachment; filename="{custom_filename}"'
                return response
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            messages.error(request, f'Error exporting to Word: {str(e)}')
            return redirect('documents:document_detail', document_id=document_id)
    
    # GET request - show export form
    return render(request, 'documents/document_export_docx_form.html', {'document': document})


def template_export_all_documents_docx(request, template_id):
    """Export all documents for a template into a single Word (DOCX) file"""
    template = get_object_or_404(Template, id=template_id)
    
    if request.method == 'POST':
        try:
            from ocr_processing.docx_exporter import DocxExporter
            from django.conf import settings
            import os
            from datetime import datetime
            
            # Get custom filename from user
            custom_filename = request.POST.get('export_filename', '')
            if not custom_filename:
                custom_filename = f"{template.name}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
            
            if not custom_filename.endswith('.docx'):
                custom_filename += '.docx'
            
            # Get all documents for this template
            documents = Document.objects.filter(template=template, processing_status='completed')
            
            if not documents.exists():
                messages.error(request, 'No processed documents found for this template')
                return redirect('templates:template_detail', template_id=template_id)
            
            # Create output path
            output_dir = os.path.join(settings.MEDIA_ROOT, 'exports')
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, custom_filename)
            
            # Create consolidated DOCX
            docx_exporter = DocxExporter()
            docx_path = docx_exporter.export_multi_documents_to_docx(
                documents, 
                template, 
                output_path,
                custom_filename.replace('.docx', '')
            )
            
            # Return file as download
            with open(docx_path, 'rb') as docx_file:
                response = HttpResponse(
                    docx_file.read(),
                    content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                )
                response['Content-Disposition'] = f'attachment; filename="{custom_filename}"'
                return response
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            messages.error(request, f'Error exporting documents: {str(e)}')
            return redirect('templates:template_detail', template_id=template_id)
    
    # GET request - show export form
    documents = Document.objects.filter(template=template, processing_status='completed')
    context = {
        'template': template,
        'document_count': documents.count()
    }
    return render(request, 'documents/template_export_docx_form.html', context)


def document_export_csv(request, document_id):
    """Export a single document's data to CSV"""
    document = get_object_or_404(Document, id=document_id)
    
    try:
        import csv
        from io import StringIO
        
        # Create CSV in memory
        output = StringIO()
        writer = csv.writer(output)
        
        if document.template:
            # Get field names from template
            field_names = document.template.get_field_names() if hasattr(document.template, 'get_field_names') else []
            
            if field_names:
                # Write header row
                writer.writerow(field_names)
                
                # Write data row
                extracted_data = document.extracted_data
                values = []
                
                if 'fields' in extracted_data:
                    # Template-based format
                    for field in extracted_data['fields']:
                        values.append(field.get('value', ''))
                
                elif 'cells' in extracted_data:
                    # Table detection format - extract first data row
                    cells = extracted_data['cells']
                    row_data = {}
                    for cell in cells:
                        row = cell.get('row', 0)
                        col = cell.get('col', 0)
                        if row == 1:  # First data row
                            row_data[col] = cell.get('text', '')
                    
                    for col_idx in sorted(row_data.keys()):
                        values.append(row_data[col_idx])
                
                writer.writerow(values)
        
        else:
            # General text document - export as single cell
            writer.writerow(['Extracted Text'])
            text = document.extracted_data.get('text', '') if document.extracted_data else ''
            writer.writerow([text])
        
        # Create response
        filename = f"{document.name.replace('.', '_')}_export.csv"
        response = HttpResponse(output.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        messages.error(request, f'Error exporting to CSV: {str(e)}')
        return redirect('documents:document_detail', document_id=document_id)


def template_export_all_documents_csv(request, template_id):
    """Export all documents for a template into a single CSV file"""
    template = get_object_or_404(Template, id=template_id)
    
    try:
        import csv
        from io import StringIO
        from datetime import datetime
        
        # Get all documents for this template
        documents = Document.objects.filter(template=template, processing_status='completed')
        
        if not documents.exists():
            messages.error(request, 'No processed documents found for this template')
            return redirect('templates:template_detail', template_id=template_id)
        
        # Create CSV in memory
        output = StringIO()
        writer = csv.writer(output)
        
        # Get field names from template
        field_names = template.get_field_names() if hasattr(template, 'get_field_names') else []
        
        if field_names:
            # Write header row (with Document column)
            headers = ['Document'] + field_names
            writer.writerow(headers)
            
            # Write data for each document
            for doc_idx, document in enumerate(documents, start=1):
                row = [f"Doc_{doc_idx}"]
                extracted_data = document.extracted_data
                
                if 'fields' in extracted_data:
                    # Template-based format
                    for field in extracted_data['fields']:
                        row.append(field.get('value', ''))
                
                elif 'cells' in extracted_data:
                    # Table detection format
                    cells = extracted_data['cells']
                    row_data = {}
                    for cell in cells:
                        cell_row = cell.get('row', 0)
                        col = cell.get('col', 0)
                        if cell_row == 1:  # First data row
                            row_data[col] = cell.get('text', '')
                    
                    for col_idx in sorted(row_data.keys()):
                        row.append(row_data[col_idx])
                
                writer.writerow(row)
        
        # Create response
        filename = f"{template.name.replace(' ', '_')}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        response = HttpResponse(output.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        messages.error(request, f'Error exporting to CSV: {str(e)}')
        return redirect('templates:template_detail', template_id=template_id)
