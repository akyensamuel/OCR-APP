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
    path('<int:document_id>/reextract-field/', views.document_reextract_field, name='document_reextract_field'),
    path('template/<int:template_id>/upload/', views.document_upload_with_template, name='document_upload_with_template'),
]
