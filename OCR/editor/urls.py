"""
Editor app URL configuration
"""
from django.urls import path
from . import views

app_name = 'editor'

urlpatterns = [
    path('', views.editor_home, name='editor_home'),
    path('upload/', views.upload_text_document, name='upload_text_document'),
    path('edit/<int:document_id>/', views.edit_text_document, name='edit_text_document'),
    path('save/<int:document_id>/', views.save_text_document, name='save_text_document'),
    path('export/<int:document_id>/', views.export_text_document, name='export_text_document'),
    path('export-docx/<int:document_id>/', views.export_text_document_docx, name='export_text_document_docx'),
    path('export-pdf/<int:document_id>/', views.export_text_document_pdf, name='export_text_document_pdf'),
    path('delete/<int:document_id>/', views.delete_text_document, name='delete_text_document'),
    path('reprocess/<int:document_id>/', views.reprocess_text_document, name='reprocess_text_document'),
    path('list/', views.text_document_list, name='text_document_list'),
    path('api/document/<int:document_id>/', views.document_api_detail, name='document_api_detail'),
]
