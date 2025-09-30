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
    path('delete/<int:document_id>/', views.delete_text_document, name='delete_text_document'),
    path('list/', views.text_document_list, name='text_document_list'),
]
