"""
URL configuration for search app
"""
from django.urls import path
from . import views

app_name = 'search'

urlpatterns = [
    path('', views.search, name='search'),
    path('advanced/', views.advanced_search, name='advanced_search'),
    path('api/', views.search_api, name='search_api'),
]
