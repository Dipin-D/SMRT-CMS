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
    path('quizlist/<int:class_shell_id>/', views.quizlist, name='quizlist'),  # Add class_shell_id here
    path('create_quiz/<int:class_shell_id>/', views.create_quiz, name='create_quiz'),
    path('question/<int:class_shell_id>/<int:quiz_id>/', views.go_to_quiz, name='go_to_quiz'),
    path('class-shell/<int:class_shell_id>/assignments/', views.assignment, name='assignment'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


