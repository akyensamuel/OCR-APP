"""
OCR Processing app URL configuration
"""
from django.urls import path
from . import views

app_name = 'ocr_processing'

urlpatterns = [
    path('', views.processing_home, name='processing_home'),
    path('api/process/', views.process_document_api, name='process_document_api'),
    path('api/status/<int:task_id>/', views.processing_status_api, name='processing_status_api'),
    path('config/', views.ocr_configuration, name='ocr_configuration'),
    path('config/save/', views.save_ocr_configuration, name='save_ocr_configuration'),
]
