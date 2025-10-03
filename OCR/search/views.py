"""
Search views for documents and templates
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from documents.models import Document
from templates.models import Template
from django.core.paginator import Paginator


@login_required
def search(request):
    """
    Universal search view for documents and templates
    """
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'all')  # all, documents, templates
    
    context = {
        'query': query,
        'search_type': search_type,
    }
    
    if not query:
        return render(request, 'search/search.html', context)
    
    # Search documents
    if search_type in ['all', 'documents']:
        documents = search_documents(query)
        context['documents'] = documents
        context['document_count'] = documents.count()
    
    # Search templates
    if search_type in ['all', 'templates']:
        templates = search_templates(query)
        context['templates'] = templates
        context['template_count'] = templates.count()
    
    # Total results
    context['total_results'] = (
        context.get('document_count', 0) + 
        context.get('template_count', 0)
    )
    
    return render(request, 'search/search.html', context)


def search_documents(query):
    """
    Search documents by name, text content, and extracted data
    """
    # Build search query with OR conditions
    search_query = Q(name__icontains=query)
    search_query |= Q(text_version__icontains=query)  # Fixed: text_version not text_content
    search_query |= Q(extracted_data__icontains=query)
    
    # Search by template name
    search_query |= Q(template__name__icontains=query)
    
    documents = Document.objects.filter(search_query).distinct()
    documents = documents.select_related('template', 'uploaded_by')
    documents = documents.order_by('-created_at')
    
    return documents


def search_templates(query):
    """
    Search templates by name, description, and structure
    """
    # Build search query with OR conditions
    search_query = Q(name__icontains=query)
    search_query |= Q(description__icontains=query)
    search_query |= Q(structure__icontains=query)
    
    templates = Template.objects.filter(search_query).distinct()
    
    # Annotate with document count
    templates = templates.annotate(
        document_count=Count('document')
    )
    
    templates = templates.order_by('-created_at')
    
    return templates


@login_required
def advanced_search(request):
    """
    Advanced search with filters for documents and templates
    """
    query = request.GET.get('q', '').strip()
    
    # Document filters
    template_id = request.GET.get('template')
    confidence_min = request.GET.get('confidence_min')
    confidence_max = request.GET.get('confidence_max')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    # Template filters
    is_active = request.GET.get('is_active')
    processing_status = request.GET.get('processing_status')
    
    context = {
        'query': query,
        'templates': Template.objects.all().order_by('name'),
    }
    
    # Base document queryset
    documents = Document.objects.all()
    
    # Apply text search
    if query:
        search_query = Q(name__icontains=query)
        search_query |= Q(text_version__icontains=query)  # Fixed: text_version not text_content
        search_query |= Q(extracted_data__icontains=query)
        documents = documents.filter(search_query)
    
    # Apply filters
    if template_id:
        documents = documents.filter(template_id=template_id)
        context['selected_template'] = template_id
    
    if confidence_min:
        try:
            documents = documents.filter(confidence_score__gte=float(confidence_min))
            context['confidence_min'] = confidence_min
        except ValueError:
            pass
    
    if confidence_max:
        try:
            documents = documents.filter(confidence_score__lte=float(confidence_max))
            context['confidence_max'] = confidence_max
        except ValueError:
            pass
    
    if date_from:
        documents = documents.filter(created_at__gte=date_from)
        context['date_from'] = date_from
    
    if date_to:
        documents = documents.filter(created_at__lte=date_to)
        context['date_to'] = date_to
    
    # Order and select related
    documents = documents.select_related('template', 'uploaded_by')
    documents = documents.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(documents, 20)  # 20 documents per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context['documents'] = page_obj
    context['document_count'] = documents.count()
    
    return render(request, 'search/advanced_search.html', context)


@login_required
def search_api(request):
    """
    JSON API endpoint for search autocomplete/suggestions
    """
    from django.http import JsonResponse
    
    query = request.GET.get('q', '').strip()
    limit = int(request.GET.get('limit', 10))
    
    if not query or len(query) < 2:
        return JsonResponse({'results': []})
    
    # Search documents
    documents = search_documents(query)[:limit]
    
    # Search templates
    templates = search_templates(query)[:limit]
    
    results = {
        'documents': [
            {
                'id': doc.id,
                'name': doc.name,
                'url': f'/documents/{doc.id}/',
                'type': 'document',
                'template': doc.template.name if doc.template else None,
                'date': doc.created_at.strftime('%Y-%m-%d'),
            }
            for doc in documents
        ],
        'templates': [
            {
                'id': tmpl.id,
                'name': tmpl.name,
                'url': f'/templates/{tmpl.id}/',
                'type': 'template',
                'field_count': tmpl.field_count,
            }
            for tmpl in templates
        ]
    }
    
    return JsonResponse(results)
