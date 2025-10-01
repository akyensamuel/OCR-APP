from django.urls import path
from . import views

app_name = 'templates'

urlpatterns = [
    # Home page
    path('', views.home, name='home'),
    # Template management URLs
    path('templates/', views.template_list, name='template_list'),
    path('upload/', views.template_upload, name='template_upload'),
    path('<int:template_id>/', views.template_detail, name='template_detail'),
    path('<int:template_id>/edit/', views.template_edit, name='template_edit'),
    path('<int:template_id>/delete/', views.template_delete, name='template_delete'),
    path('<int:template_id>/process/', views.process_template, name='process_template'),
    path('<int:template_id>/save-structure/', views.save_template_structure, name='save_template_structure'),
    path('<int:template_id>/reprocess/', views.reprocess_template, name='reprocess_template'),
    path('<int:template_id>/fields/', views.template_fields_api, name='template_fields_api'),
]
