from django.urls import path
from . import views

app_name = 'templates'

urlpatterns = [
    # Template management URLs
    path('', views.template_list, name='template_list'),
    path('upload/', views.template_upload, name='template_upload'),
    path('<int:template_id>/', views.template_detail, name='template_detail'),
    path('<int:template_id>/edit/', views.template_edit, name='template_edit'),
    path('<int:template_id>/delete/', views.template_delete, name='template_delete'),
    path('<int:template_id>/process/', views.process_template, name='process_template'),
]
