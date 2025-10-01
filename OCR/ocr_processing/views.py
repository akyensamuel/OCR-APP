from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
import json
from .models import OCRConfiguration, ProcessingTask


def processing_home(request):
    """Home page for OCR processing"""
    recent_tasks = ProcessingTask.objects.order_by('-created_at')[:5]
    total_tasks = ProcessingTask.objects.count()
    completed_tasks = ProcessingTask.objects.filter(processing_status='completed').count()
    
    context = {
        'recent_tasks': recent_tasks,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'success_rate': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
    }
    return render(request, 'ocr_processing/processing_home.html', context)


@csrf_exempt
def process_document_api(request):
    """API endpoint for processing documents"""
    if request.method == 'POST':
        try:
            # This would typically handle file upload and processing
            # For now, return a simple response
            return JsonResponse({
                'success': True,
                'message': 'Document processing started',
                'task_id': 1
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


def processing_status_api(request, task_id):
    """API endpoint for checking processing status"""
    try:
        task = get_object_or_404(ProcessingTask, id=task_id)
        return JsonResponse({
            'success': True,
            'status': task.processing_status,
            'progress': 100 if task.processing_status == 'completed' else 50,
            'message': f'Task is {task.processing_status}'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


def ocr_configuration(request):
    """OCR configuration page"""
    try:
        config = OCRConfiguration.objects.first()
        if not config:
            config = OCRConfiguration.objects.create()
    except:
        config = None
    
    context = {'config': config}
    return render(request, 'ocr_processing/configuration.html', context)


def save_ocr_configuration(request):
    """Save OCR configuration"""
    if request.method == 'POST':
        try:
            config = OCRConfiguration.objects.first()
            if not config:
                config = OCRConfiguration.objects.create()
            
            config.engine_preference = request.POST.get('engine_preference', 'tesseract')
            config.enable_preprocessing = request.POST.get('enable_preprocessing') == 'on'
            config.confidence_threshold = float(request.POST.get('confidence_threshold', 50))
            config.save()
            
            messages.success(request, 'OCR configuration saved successfully')
        except Exception as e:
            messages.error(request, f'Error saving configuration: {str(e)}')
    
    return redirect('ocr_processing:ocr_configuration')
