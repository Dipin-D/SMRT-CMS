from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .views import (
    GoToCourseView,
    class_shell_list,
    QuizDetailView,
    ExerciseDetailView,
    QuizGradeView,
    ExerciseGradeView,
    InstructorAnalyticsView,
)

app_name = 'instructor'

urlpatterns = [
    path('', class_shell_list, name='class_shell_list'),
    path('course/<int:class_shell_id>/', GoToCourseView.as_view(), name='go_to_course'),
    path('quizlist/<int:class_shell_id>/', GoToCourseView.as_view(), name='quizlist'),
    path('create_quiz/<int:class_shell_id>/', GoToCourseView.as_view(), name='create_quiz'),
    path('quiz/<int:class_shell_id>/<int:quiz_id>/', QuizDetailView.as_view(), name='go_to_quiz'),
    path('exercises/<int:class_shell_id>/', GoToCourseView.as_view(), name='exercises'),
    path('exercise/<int:class_shell_id>/<int:exercise_id>/', ExerciseDetailView.as_view(), name='go_to_exercise'),
    path('class-shell/<int:class_shell_id>/assignments/', GoToCourseView.as_view(), name='assignment'),
    path('students/', GoToCourseView.as_view(), name='student_list'),
    path('quiz/grade/<int:submission_id>/', QuizGradeView.as_view(), name='quiz_grade'),
    path('exercise/grade/<int:submission_id>/', ExerciseGradeView.as_view(), name='exercise_grade'),


] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
