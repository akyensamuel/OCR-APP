from django.urls import path
from . import views

app_name = 'documents'

urlpatterns = [
    # Document processing URLs
    path('', views.document_list, name='document_list'),
    path('upload/', views.document_upload, name='document_upload'),
    path('<int:document_id>/', views.document_detail, name='document_detail'),
    path('<int:document_id>/edit/', views.document_edit, name='document_edit'),
    path('<int:document_id>/delete/', views.document_delete, name='document_delete'),
    path('<int:document_id>/reprocess/', views.document_reprocess, name='document_reprocess'),
    path('<int:document_id>/export/', views.document_export, name='document_export'),
    path('<int:document_id>/export-excel/', views.document_export_excel, name='document_export_excel'),
    path('<int:document_id>/export-docx/', views.document_export_docx, name='document_export_docx'),
    path('<int:document_id>/export-csv/', views.document_export_csv, name='document_export_csv'),
    path('<int:document_id>/download-excel/', views.document_download_excel, name='document_download_excel'),
    path('<int:document_id>/reextract-field/', views.document_reextract_field, name='document_reextract_field'),
    path('template/<int:template_id>/upload/', views.document_upload_with_template, name='document_upload_with_template'),
    path('template/<int:template_id>/export-all/', views.template_export_all_documents, name='template_export_all'),
    path('template/<int:template_id>/export-all-docx/', views.template_export_all_documents_docx, name='template_export_all_docx'),
    path('template/<int:template_id>/export-all-csv/', views.template_export_all_documents_csv, name='template_export_all_csv'),
]
