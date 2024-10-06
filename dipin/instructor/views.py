from django.shortcuts import render, redirect, get_object_or_404
from .forms import ClassShellForm, CourseFileForm, CourseForm, QuizForm, QuestionForm, AssignmentForm
from .models import ClassShell, CourseFile, Course,Question, Quiz, Assignment

def create_class_shell(request):
    if request.method == 'POST':
        form = ClassShellForm(request.POST)
        if form.is_valid():
            class_shell = form.save(commit=False)
            class_shell.user = request.user
            class_shell.save()
            return redirect('instructor:class_shell_list')
    else:
        form = ClassShellForm()
    return render(request, 'create_class_shell.html', {'form': form})

def class_shell_list(request):
    class_shells = ClassShell.objects.filter(user=request.user)
    return render(request, 'class_shell_list.html', {'class_shells': class_shells})

def go_to_course(request, class_shell_id):
    # Fetch the ClassShell instance and related data
    class_shell = get_object_or_404(ClassShell, id=class_shell_id)
    class_shell = get_object_or_404(ClassShell, id=class_shell_id)
    lectures = Course.objects.filter(class_shell=class_shell)  # Still using Course model
    quizzes = Quiz.objects.filter(user=request.user, class_shell=class_shell)
    assignments = Assignment.objects.filter(class_shell=class_shell)
    files = CourseFile.objects.filter(class_shell=class_shell)  # Still using CourseFile model

    # Initialize course_form and file_form
    course_form = CourseForm()  # Still using CourseForm
    file_form = CourseFileForm()  # Still using CourseFileForm

    if request.method == 'POST':
        lecture_id = request.POST.get('lecture_id')  # Getting lecture_id from the form

        # Handling editing a lecture
        if 'edit_lecture' in request.POST and lecture_id:
            lecture = get_object_or_404(Course, id=lecture_id, class_shell=class_shell)
            course_form = CourseForm(request.POST, instance=lecture)  # Still using CourseForm
            if course_form.is_valid():
                lecture_instance = course_form.save(commit=False)
                lecture_instance.user = request.user
                lecture_instance.class_shell = class_shell
                lecture_instance.save()

                # Handle file upload if there is a file being uploaded
                if 'file' in request.FILES:
                    file_form = CourseFileForm(request.POST, request.FILES)  # Still using CourseFileForm
                    if file_form.is_valid():
                        lecture_file = file_form.save(commit=False)  # Changed from course_file to lecture_file
                        lecture_file.user = request.user
                        lecture_file.course = lecture_instance  # Associate with edited lecture
                        lecture_file.class_shell = class_shell
                        lecture_file.save()

                # Handle file removal if specified
                if 'remove_file' in request.POST:
                    file_id = request.POST.get('remove_file')  # Get the value of the checkbox
                    if file_id:
                        try:
                            lecture_file = CourseFile.objects.get(id=file_id, course=lecture_instance)  # Changed from course_file to lecture_file
                            lecture_file.delete()
                        except CourseFile.DoesNotExist:
                            print(f'File with ID {file_id} does not exist for this lecture.')

        # Handling adding a new lecture
        elif 'add_lecture' in request.POST:
            course_form = CourseForm(request.POST)  # Still using CourseForm
            if course_form.is_valid():
                lecture_instance = course_form.save(commit=False)
                lecture_instance.user = request.user
                lecture_instance.class_shell = class_shell
                lecture_instance.save()

                # Handle file upload for the new lecture
                if 'file' in request.FILES:
                    file_form = CourseFileForm(request.POST, request.FILES)  # Still using CourseFileForm
                    if file_form.is_valid():
                        lecture_file = file_form.save(commit=False)  # Changed from course_file to lecture_file
                        lecture_file.user = request.user
                        lecture_file.course = lecture_instance  # Associate with new lecture
                        lecture_file.class_shell = class_shell
                        lecture_file.save()

        # Handling deleting a lecture
        elif 'delete_lecture' in request.POST and lecture_id:
            lecture = get_object_or_404(Course, id=lecture_id, class_shell=class_shell)
            lecture.delete()

    return render(request, 'go_to_course.html', {
        'course_form': course_form,  # Still using course_form
        'file_form': file_form,      # Still using file_form
        'class_shell': class_shell,
        'lectures': lectures,
        'quizzes': quizzes,
        'assignments': assignments,
        'files': files,
    })



def create_quiz(request, class_shell_id):
    class_shell = get_object_or_404(ClassShell, id=class_shell_id)
    if request.method == 'POST':
        form = QuizForm(request.POST)
        if form.is_valid():
            quiz = form.save(commit=False)
            quiz.user = request.user
            quiz.class_shell = class_shell
            quiz.save()
            return redirect('instructor:quizlist', class_shell_id=class_shell.id)  
    else:
        form = QuizForm()
    return render(request, 'create_quiz.html', {'form': form, 'class_shell': class_shell})


def quizlist(request, class_shell_id):
    class_shell = get_object_or_404(ClassShell, id=class_shell_id)  
    quizzes = Quiz.objects.filter(user=request.user, class_shell=class_shell)

    if request.method == 'POST':
        quiz_id = request.POST.get('quiz_id')

        # Handle quiz deletion
        if 'delete_quiz' in request.POST and quiz_id:
            quiz_instance = get_object_or_404(Quiz, id=quiz_id, class_shell=class_shell)
            quiz_instance.delete()
            return redirect('instructor:quizlist', class_shell_id=class_shell.id)

        # Handle quiz editing
        if 'edit_quiz' in request.POST and quiz_id:
            quiz_instance = get_object_or_404(Quiz, id=quiz_id, class_shell=class_shell)
            quiz_form = QuizForm(request.POST, instance=quiz_instance)
            if quiz_form.is_valid():
                quiz_form.save()
                return redirect('instructor:quizlist', class_shell_id=class_shell.id)
    
    return render(request, 'quizlist.html', {
        'quizzes': quizzes,
        'class_shell': class_shell,  
        'quiz_form': QuizForm(),  
    })


def go_to_quiz(request, class_shell_id, quiz_id):
    class_shell = get_object_or_404(ClassShell, id=class_shell_id)  
    quiz_instance = get_object_or_404(Quiz, id=quiz_id, class_shell=class_shell)  
    questions = Question.objects.filter(quiz=quiz_instance)  

    if request.method == 'POST':
        question_id = request.POST.get('question_id')

        if 'edit_question' in request.POST and question_id:
            question_instance = get_object_or_404(Question, id=question_id, quiz=quiz_instance)

            question_form = QuestionForm(request.POST or None, instance=question_instance)
            if question_form.is_valid():
                new_question = question_form.save(commit=False)
                new_question.quiz = quiz_instance  
                new_question.save()  
                return redirect('instructor:go_to_quiz', class_shell_id=class_shell_id, quiz_id=quiz_id)

        elif 'add_question' in request.POST:
            question_form = QuestionForm(request.POST)
            if question_form.is_valid():
                new_question = question_form.save(commit=False)
                new_question.quiz = quiz_instance  
                new_question.save()
                return redirect('instructor:go_to_quiz', class_shell_id=class_shell_id, quiz_id=quiz_id)
                    
        elif 'delete_question' in request.POST and question_id:
            question_instance = get_object_or_404(Question, id=question_id, quiz=quiz_instance)
            question_instance.delete()

    return render(request, 'go_to_quiz.html', {
        'class_shell': class_shell,
        'quiz': quiz_instance,  
        'questions': questions,
        'question_form': QuestionForm()
    })


def assignment(request, class_shell_id):
    class_shell = get_object_or_404(ClassShell, id=class_shell_id)
    assignments = Assignment.objects.filter(class_shell=class_shell)
    files = CourseFile.objects.filter(class_shell=class_shell)

    if request.method == 'POST':
        assignment_id = request.POST.get('assignment_id')

        if 'edit_assignment' in request.POST and assignment_id:
            assignment = get_object_or_404(Assignment, id=assignment_id)  
            assignment_form = AssignmentForm(request.POST, instance=assignment)  
            if assignment_form.is_valid():
                assignment_instance = assignment_form.save(commit=False)
                assignment_instance.user = request.user
                assignment_instance.class_shell = class_shell
                assignment_instance.save()

        elif 'add_assignment' in request.POST:
            print('add assignment hit')  
            assignment_form = AssignmentForm(request.POST, request.FILES)  # Include request.FILES for file uploads
            if assignment_form.is_valid():
                assignment_instance = assignment_form.save(commit=False)
                assignment_instance.user = request.user
                assignment_instance.class_shell = class_shell
                assignment_instance.save()
                return redirect('assignment', class_shell_id=class_shell.id)

        elif 'delete_assignment' in request.POST and assignment_id:  
            assignment = get_object_or_404(Assignment, id=assignment_id)  
            assignment.delete()  

    return render(request, 'assignment.html', {  
        'assignment_form': assignment_form,  
        'class_shell': class_shell,
        'assignments': assignments,  
        'files': files,
    })
