from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .views import (
    GoToCourseView,
    class_shell_list,
    create_class_shell,
    QuizDetailView,
    ExerciseDetailView,
    
)

app_name = 'instructor'

urlpatterns = [
    path('', class_shell_list, name='class_shell_list'),
    path('create/', create_class_shell, name='create_class_shell'),
    path('course/<int:class_shell_id>/', GoToCourseView.as_view(), name='go_to_course'),
    path('quizlist/<int:class_shell_id>/', GoToCourseView.as_view(), name='quizlist'),
    path('create_quiz/<int:class_shell_id>/', GoToCourseView.as_view(), name='create_quiz'),
    path('quiz/<int:class_shell_id>/<int:quiz_id>/', QuizDetailView.as_view(), name='go_to_quiz'),
    path('exercises/<int:class_shell_id>/', GoToCourseView.as_view(), name='exercises'),
    path('exercise/<int:class_shell_id>/<int:exercise_id>/', ExerciseDetailView.as_view(), name='go_to_exercise'),
    path('class-shell/<int:class_shell_id>/assignments/', GoToCourseView.as_view(), name='assignment'),
    path('students/', GoToCourseView.as_view(), name='student_list'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
