from django.shortcuts import render, get_object_or_404, redirect
from instructor.models import ClassShell, Course, Quiz, Assignment, Exercise, Question, CourseFile
from accounts.models import CustomUser

def course_list(request):
    student = request.user
    class_shells = ClassShell.objects.filter(students_with_access=student)
    print(f'Student: {request.user}, Accessible Class Shells: {class_shells}')
    
    return render(request, 'course_list.html', {'class_shells': class_shells})

def go_to_course(request, class_shell_id):
    class_shell = get_object_or_404(ClassShell, id=class_shell_id)
    if request.user not in class_shell.students_with_access.all():
        return redirect('no_access')

    lectures = Course.objects.filter(class_shell=class_shell)
    files = CourseFile.objects.filter(class_shell=class_shell)
    quizzes = Quiz.objects.filter(class_shell=class_shell)
    exercises = Exercise.objects.filter(class_shell=class_shell)
    assignments = Assignment.objects.filter(class_shell=class_shell)

    return render(request, 'go_to_course_student.html', {
        'class_shell': class_shell,
        'lectures': lectures,
        'quizzes': quizzes,
        'assignments': assignments,
        'exercises': exercises,
        'files': files,
    })

def view_lecture(request, class_shell_id, lecture_id):
    class_shell = get_object_or_404(ClassShell, id=class_shell_id)
    if request.user not in class_shell.students_with_access.all():
        return redirect('no_access')

    lecture = get_object_or_404(Course, id=lecture_id, class_shell=class_shell)

    return render(request, 'view_lecture.html', {'lecture': lecture})

def quiz_list(request, class_shell_id):
    quizzes = Quiz.objects.filter(class_shell__id=class_shell_id)

    return render(request, 'quiz_list.html', {
        'quizzes': quizzes,
        'class_shell_id': class_shell_id,
    })

def attempt_quiz(request, class_shell_id, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, class_shell__id=class_shell_id)
    questions = Question.objects.filter(quiz=quiz) 
    score = None
    total_questions = questions.count()

    if request.method == "POST":
        score = 0
        for question in questions:
            answer = request.POST.get(f'answer_{question.id}')

            correct_answers = question.answers.filter(is_correct=True).values_list('text', flat=True)
            if answer in correct_answers:
                score += 1

        context = {
            'quiz': quiz,
            'questions': questions,
            'score': score,
            'total_questions': total_questions,
        }
        return render(request, 'attempt_quiz.html', context)

    return render(request, 'attempt_quiz.html', {
        'quiz': quiz,
        'questions': questions,
        'score': score,
        'class_shell_id': class_shell_id,
        'quiz_id':quiz_id 
    })

def view_assignment(request, class_shell_id, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id, class_shell__id=class_shell_id)
    return render(request, 'view_assignment.html', {'assignment': assignment})

def view_exercise(request, class_shell_id, exercise_id):
    exercise = get_object_or_404(Exercise, id=exercise_id, class_shell__id=class_shell_id)
    return render(request, 'view_exercise.html', {'exercise': exercise})
