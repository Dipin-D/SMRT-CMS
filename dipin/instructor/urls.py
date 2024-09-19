from django.urls import path
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views

app_name = 'instructor'

urlpatterns = [
    path('', views.class_shell_list, name='class_shell_list'),
    path('create/', views.create_class_shell, name='create_class_shell'),
    path('course/<int:class_shell_id>/', views.go_to_course, name='go_to_course'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


