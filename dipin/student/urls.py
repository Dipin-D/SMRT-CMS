from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from .views import course_list, go_to_course_student,attempt_quiz, attempt_exercise,while_quiz, while_exercise,autosave_answer,autosave_answer_exercise

app_name = 'student'

urlpatterns = [
    path('courses/', course_list, name='course_list'),
    path('courses/<int:class_shell_id>/', go_to_course_student.as_view(), name='go_to_course'),
    path('course/<int:class_shell_id>/lectures/<int:lecture_id>/', go_to_course_student.as_view(), name='view_lecture'),
    path('quizzes/<int:class_shell_id>/', go_to_course_student.as_view(),name='quiz_list'),
    path('attempt_quiz/<int:class_shell_id>/<int:quiz_id>/', attempt_quiz, name='attempt_quiz'),
    path('while_quiz/<int:class_shell_id>/<int:quiz_id>/', while_quiz, name='while_quiz'),
    path("autosave/", autosave_answer, name="autosave_answer"),
    path('exercise/<int:class_shell_id>/<int:exercise_id>/', attempt_exercise, name='attempt_exercise'),
    path('exercise/<int:class_shell_id>/<int:exercise_id>/while/', while_exercise, name='while_exercise'),
    path("autosaveexercise/", autosave_answer_exercise, name="autosave_answer_exercise"),
    path('courses/<int:class_shell_id>/assignments/<int:assignment_id>/', go_to_course_student.as_view(), name='view_assignment'),
    path('courses/<int:class_shell_id>/exercises/<int:exercise_id>/', go_to_course_student.as_view(), name='view_exercise'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
