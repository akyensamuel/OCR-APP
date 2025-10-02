"""
API URL Configuration
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from . import views

# Create router and register viewsets
router = DefaultRouter()
router.register(r'templates', views.TemplateViewSet, basename='template')
router.register(r'documents', views.DocumentViewSet, basename='document')
router.register(r'ocr', views.OCRViewSet, basename='ocr')
router.register(r'statistics', views.StatisticsViewSet, basename='statistics')

app_name = 'api'

urlpatterns = [
    # Router URLs
    path('', include(router.urls)),
    
    # Authentication
    path('auth/token/', obtain_auth_token, name='api_token_auth'),
]
