from django.shortcuts import render, redirect, get_object_or_404
from .forms import ClassShellForm, CourseFileForm, CourseForm, QuizForm, QuestionForm, AssignmentForm, AssignmentFileForm, ExerciseForm, ExerciseQuestionForm
from .models import ClassShell, CourseFile, Course, Question, Quiz, Assignment, AssignmentFile, Exercise, ExerciseQuestion
from student.models import AssignmentSubmission, QuizAttempt, ExerciseAttempt
from django.views import View
from accounts.models import CustomUser
from django.contrib import messages
from itertools import chain

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

class GoToCourseView(View):
    def get(self, request, class_shell_id):
        class_shell = get_object_or_404(ClassShell, id=class_shell_id)
        if request.user.is_student and request.user not in class_shell.students_with_access.all():
            return redirect('no_access')
        lectures = Course.objects.filter(class_shell=class_shell)
        quizzes = Quiz.objects.filter(class_shell=class_shell)
        exercises = Exercise.objects.filter(class_shell=class_shell)
        assignments = Assignment.objects.filter(class_shell=class_shell)
        files = CourseFile.objects.filter(class_shell=class_shell)
        assignment_files=AssignmentFile.objects.filter(class_shell=class_shell)
        
        students = CustomUser.objects.filter(is_student=True)
        students_with_access = class_shell.students_with_access.values_list('id', flat=True)  # Get IDs with access
        
        ungraded_submissions = {
                'assignments': AssignmentSubmission.objects.filter(graded=False, assignment__class_shell=class_shell),
                'quizzes': QuizAttempt.objects.filter(graded=False, quiz__class_shell=class_shell),
                'exercises': ExerciseAttempt.objects.filter(graded=False, exercise__class_shell=class_shell),
            }

        graded_submissions = {
            'assignments': AssignmentSubmission.objects.filter(graded=True, assignment__class_shell=class_shell),
            'quizzes': QuizAttempt.objects.filter(graded=True, quiz__class_shell=class_shell),
            'exercises': ExerciseAttempt.objects.filter(graded=True, exercise__class_shell=class_shell),
        }

        lecture_form = CourseForm()
        lecture_file_form = CourseFileForm()
        quiz_form = QuizForm()
        exercise_form = ExerciseForm()  
        assignment_form = AssignmentForm()

        return render(request, 'go_to_course.html', {
            'lecture_form': lecture_form,
            'lecture_file_form': lecture_file_form,
            'quiz_form': quiz_form,
            'exercise_form': exercise_form,  
            'assignment_form': assignment_form,
            'class_shell': class_shell,
            'lectures': lectures,
            'quizzes': quizzes,
            'assignments':assignments,
            'exercises': exercises, 
            'files': files,
            'assignment_files':assignment_files,
            'students':students,
            'students_with_access': students_with_access,
            'ungraded_submissions': ungraded_submissions,
            'graded_submissions': graded_submissions
        })

    def post(self, request, class_shell_id):
        class_shell = get_object_or_404(ClassShell, id=class_shell_id)

        lecture_form = CourseForm(request.POST or None)
        quiz_form = QuizForm(request.POST or None)
        exercise_form = ExerciseForm(request.POST or None)  
        assignment_form = AssignmentForm(request.POST or None)

        lecture_id = request.POST.get('lecture_id')
        quiz_id = request.POST.get('quiz_id')
        exercise_id = request.POST.get('exercise_id')  
        assignment_id = request.POST.get('assignment_id')
        submission_id = request.POST.get("submission_id")

        if 'update_access' in request.POST:
            selected_student_ids = request.POST.getlist('access_student_ids')
            selected_students = CustomUser.objects.filter(id__in=selected_student_ids, is_student=True)
            class_shell.students_with_access.set(selected_students)
        # Handle lecture
        if 'add_lecture' in request.POST and lecture_form.is_valid():
            self.handle_add_lecture(lecture_form, class_shell, request.user)
        elif 'edit_lecture' in request.POST and lecture_id:
            self.handle_edit_lecture(request, class_shell, lecture_id)
        elif 'delete_lecture' in request.POST and lecture_id:
            self.handle_delete_lecture(lecture_id, class_shell)

        # Handle quiz operations
        if 'add_quiz' in request.POST and quiz_form.is_valid():
            self.handle_add_quiz(quiz_form, class_shell, request.user)
        elif 'edit_quiz' in request.POST and quiz_id:
            self.handle_edit_quiz(request, quiz_id, class_shell)
        elif 'delete_quiz' in request.POST and quiz_id:
            self.handle_delete_quiz(quiz_id, class_shell)
        # Handle exercise operations
        if 'add_exercise' in request.POST and exercise_form.is_valid():  
            self.handle_add_exercise(exercise_form, class_shell, request.user)
        elif 'edit_exercise' in request.POST and exercise_id:
            self.handle_edit_exercise(request, exercise_id, class_shell)
        elif 'delete_exercise' in request.POST and exercise_id:
            self.handle_delete_exercise(exercise_id, class_shell)

        # Handle assignment operations
        if 'add_assignment' in request.POST and assignment_form.is_valid():
            self.handle_add_assignment(assignment_form, class_shell, request.user)
        elif 'edit_assignment' in request.POST and assignment_id:
            self.handle_edit_assignment(request, class_shell, assignment_id)
        elif 'delete_assignment' in request.POST and assignment_id:
            self.handle_delete_assignment(assignment_id, class_shell)
        #handle submission grading
        if 'grade_submission' in request.POST and submission_id:
            self.handle_manage_submissions(request, submission_id)
        return redirect('instructor:go_to_course', class_shell_id=class_shell_id)

    #grading
    def handle_manage_submissions(self, request, submission_id):
        submission = None

        for model in [AssignmentSubmission, QuizAttempt, ExerciseAttempt]:
            try:
                submission = model.objects.get(id=submission_id)
                break
            except model.DoesNotExist:
                continue

        if request.method == "POST":
            grade = request.POST.get("grade")                
            if not grade:
                messages.error(request, "Grade cannot be empty.")
            else:
                try:
                    grade = float(grade)
                    if grade < 0 or grade > 100:
                        messages.error(request, "Grade must be between 0 and 100.")
                    else:
                        submission.grade = grade
                        submission.graded = True
                        submission.save()
                        messages.success(request, "Grade has been successfully saved.")
                except ValueError:
                    messages.error(request, "Please enter a valid grade between 0 and 100.")                    

    #ASSIGMENT
    def handle_add_assignment(self, form, class_shell, user):
        assignment = form.save(commit=False)
        assignment.class_shell = class_shell
        assignment.user = user
        assignment.save()

        # Handle optional file upload for the new assignment
        if 'assignment_file' in self.request.FILES: 
            assignment_file_form = AssignmentFileForm(self.request.POST, self.request.FILES)
            if assignment_file_form.is_valid():
                assignment_file = assignment_file_form.save(commit=False)
                assignment_file.assignment = assignment
                assignment_file.class_shell = class_shell
                assignment_file.user = user
                assignment_file.save()
            else:
                print("Assignment File Form Errors:", assignment_file_form.errors)  # Print form errors if any

    def handle_edit_assignment(self, request, class_shell, assignment_id):
        assignment = get_object_or_404(Assignment, id=assignment_id, class_shell=class_shell)
        assignment_form = AssignmentForm(request.POST, instance=assignment)

        if assignment_form.is_valid():
            assignment_instance = assignment_form.save(commit=False)
            assignment_instance.user = request.user
            assignment_instance.class_shell = class_shell
            assignment_instance.due_date = request.POST.get("due_date")
            assignment_instance.save()

            # Handle optional file upload during assignment editing
            if 'assignment_file' in request.FILES:  
                assignment_file_form = AssignmentFileForm(request.POST, request.FILES)
                if assignment_file_form.is_valid():
                    assignment_file = assignment_file_form.save(commit=False)
                    assignment_file.assignment = assignment_instance
                    assignment_file.class_shell = class_shell
                    assignment_file.user = request.user
                    assignment_file.save()

            # Handle file removal
            remove_files = request.POST.getlist('remove_file')  
            for file_id in remove_files:
                try:
                    assignment_file = AssignmentFile.objects.get(id=file_id, assignment=assignment)
                    assignment_file.delete()  
                except AssignmentFile.DoesNotExist:
                    pass


    def handle_delete_assignment(self, assignment_id, class_shell):
        assignment = get_object_or_404(Assignment, id=assignment_id, class_shell=class_shell)
        assignment.delete()

#LECTURE
    def handle_add_lecture(self, form, class_shell, user):
        lecture_instance = form.save(commit=False)
        lecture_instance.user = user
        lecture_instance.class_shell = class_shell
        lecture_instance.save()

        # Handle file upload for the new lecture
        if 'file' in self.request.FILES:
            file_form = CourseFileForm(self.request.POST, self.request.FILES)
            if file_form.is_valid():
                lecture_file = file_form.save(commit=False)
                lecture_file.user = user
                lecture_file.course = lecture_instance
                lecture_file.class_shell = class_shell
                lecture_file.save()

    def handle_edit_lecture(self, request, class_shell, lecture_id):
        lecture = get_object_or_404(Course, id=lecture_id, class_shell=class_shell)
        course_form = CourseForm(request.POST, instance=lecture)

        if course_form.is_valid():
            lecture_instance = course_form.save(commit=False)
            lecture_instance.user = request.user
            lecture_instance.class_shell = class_shell
            lecture_instance.save()

            # Handle file upload if there is a file being uploaded
            if 'file' in request.FILES:
                file_form = CourseFileForm(request.POST, request.FILES)
                if file_form.is_valid():
                    lecture_file = file_form.save(commit=False)
                    lecture_file.user = request.user
                    lecture_file.course = lecture_instance
                    lecture_file.class_shell = class_shell
                    lecture_file.save()

            # Handle file removal if specified
            if 'remove_file' in request.POST:
                file_id = request.POST.get('remove_file')
                if file_id:
                    try:
                        lecture_file = CourseFile.objects.get(id=file_id, course=lecture_instance)
                        lecture_file.delete()
                    except CourseFile.DoesNotExist:
                        print(f'File with ID {file_id} does not exist for this lecture.')

    def handle_delete_lecture(self, lecture_id, class_shell):
        lecture = get_object_or_404(Course, id=lecture_id, class_shell=class_shell)
        lecture.delete()
#quiz
    def handle_add_quiz(self, form, class_shell, user):
        quiz_instance = form.save(commit=False)
        quiz_instance.user = user
        quiz_instance.class_shell = class_shell
        quiz_instance.save()
    
    def handle_edit_quiz(self, request, quiz_id, class_shell):
        quiz_instance = get_object_or_404(Quiz, id=quiz_id, class_shell=class_shell)
        quiz_form = QuizForm(request.POST, instance=quiz_instance)

        if quiz_form.is_valid():
            quiz_instance = get_object_or_404(Quiz, id=quiz_id)
            quiz_instance.title = request.POST.get('title')
            quiz_instance.grading_percentage = request.POST.get('grading_percentage')
            quiz_instance.due_date = request.POST.get("due_date")
            quiz_instance.save()


    def handle_delete_quiz(self, quiz_id, class_shell):
        quiz_instance = get_object_or_404(Quiz, id=quiz_id, class_shell=class_shell)
        quiz_instance.delete()
# Exercise handling methods
    def handle_add_exercise(self, form, class_shell, user):
        exercise_instance = form.save(commit=False)
        exercise_instance.user = user
        exercise_instance.class_shell = class_shell
        exercise_instance.save()
    def handle_edit_exercise(self, request, exercise_id, class_shell):
        exercise_instance = get_object_or_404(Exercise, id=exercise_id, class_shell=class_shell)
        exercise_form = ExerciseForm(request.POST, instance=exercise_instance)

        if exercise_form.is_valid():
            exercise_instance = exercise_form.save(commit=False)
            exercise_instance.title = request.POST.get('title')
            exercise_instance.grading_percentage = request.POST.get('grading_percentage')
            exercise_instance.due_date = request.POST.get("due_date")  
            exercise_instance.save()

    def handle_delete_exercise(self, exercise_id, class_shell):
        exercise_instance = get_object_or_404(Exercise, id=exercise_id, class_shell=class_shell)  # Correct model
        exercise_instance.delete()

class QuizDetailView(View):
    def get(self, request, class_shell_id, quiz_id):
        quiz = get_object_or_404(Quiz, id=quiz_id)
        questions = Question.objects.filter(quiz=quiz)
        question_form = QuestionForm()

        return render(request, 'go_to_quiz.html', {
            'quiz': quiz,
            'questions': questions,
            'question_form': question_form,
            'class_shell_id': class_shell_id  
        })

    def post(self, request, class_shell_id, quiz_id):
        quiz = get_object_or_404(Quiz, id=quiz_id)
        question_form = QuestionForm(request.POST)

        if 'add_question' in request.POST and question_form.is_valid():
            question_instance = question_form.save(commit=False)
            question_instance.quiz = quiz
            if question_instance.type == 'multiple_choice':
                question_instance.tf_answer = None  
                question_instance.save()
            elif question_instance.type == 'true_false':
                question_instance.mcq_answer = None  
                question_instance.save()

        elif 'edit_question' in request.POST and question_form.is_valid():
            question_id = request.POST.get('question_id')
            question_instance = get_object_or_404(Question, id=question_id)
            question_instance.text = question_form.cleaned_data['text']
            question_instance.type = question_form.cleaned_data['type']
            
            if question_instance.type == 'multiple_choice':
                question_instance.tf_answer = None  
                question_instance.choice_1 = question_form.cleaned_data['choice_1']
                question_instance.choice_2 = question_form.cleaned_data['choice_2']
                question_instance.choice_3 = question_form.cleaned_data['choice_3']
                question_instance.choice_4 = question_form.cleaned_data['choice_4']
                question_instance.mcq_answer = question_form.cleaned_data['mcq_answer']
            elif question_instance.type == 'true_false':
                question_instance.mcq_answer = None  
                question_instance.tf_answer = question_form.cleaned_data['tf_answer']
                                                                         
            elif question_instance.type == 'essay':
                question_instance.essay_answer = question_form.cleaned_data['essay_answer']

            question_instance.save()

        elif 'delete_question' in request.POST:
            question_id = request.POST.get('question_id')
            self.handle_delete_question(question_id)

        return redirect('instructor:go_to_quiz', class_shell_id=class_shell_id, quiz_id=quiz_id)

    def handle_delete_question(self, question_id):
        question = get_object_or_404(Question, id=question_id)
        question.delete()




class ExerciseDetailView(View):
    def get(self, request, class_shell_id, exercise_id):
        exercise = get_object_or_404(Exercise, id=exercise_id)
        exercise_questions = ExerciseQuestion.objects.filter(exercise=exercise) 
        question_form = ExerciseQuestionForm()  

        return render(request, 'go_to_exercise.html', {
            'exercise': exercise,
            'exercise_questions': exercise_questions,
            'question_form': question_form,
            'class_shell_id': class_shell_id  
        })

    def post(self, request, class_shell_id, exercise_id):
        exercise = get_object_or_404(Exercise, id=exercise_id)
        question_form = ExerciseQuestionForm(request.POST)
        if 'add_question' in request.POST and question_form.is_valid():
            exercise_question_instance = question_form.save(commit=False)
            exercise_question_instance.exercise = exercise
            if exercise_question_instance.type == 'multiple_choice':
                exercise_question_instance.tf_answer = None  
                exercise_question_instance.save()
            elif exercise_question_instance.type == 'true_false':
                exercise_question_instance.mcq_answer = None  
                exercise_question_instance.save()
        elif 'delete_question' in request.POST:
            exercise_question_id = request.POST.get('exerciseQuestion_id')
            self.handle_delete_question(exercise_question_id)
        else:
            print("Form Errors:", question_form.errors)

        return redirect('instructor:go_to_exercise', class_shell_id=class_shell_id, exercise_id=exercise_id)

    def handle_delete_question(self, exercise_question_id):
        exercise_question = get_object_or_404(ExerciseQuestion, id=exercise_question_id)  
        exercise_question.delete()

class QuizGradeView(View):
    def get(self, request, submission_id):
        submission = get_object_or_404(QuizAttempt, id=submission_id)
        
        question_attempts = submission.question_attempts.all()  
        total_marks = submission.total_marks 
        score = submission.grade  
        
        class_shell = submission.quiz.class_shell  
        
        return render(request, "quiz_grade.html", {
            "quiz": submission.quiz,  
            "question_attempts": question_attempts, 
            "total_marks": total_marks,  
            "score": score,  
            "class_shell": class_shell  
        })
    def post(self, request, submission_id):
        submission = get_object_or_404(QuizAttempt, id=submission_id)
        
        grade = request.POST.get("grade")
        
        if grade:
            try:
                grade = float(grade)
                if 0 <= grade <= submission.total_marks:
                    submission.grade = grade
                    submission.graded = True  # Mark as graded
                    submission.save()
                    messages.success(request, "Grade has been successfully saved.")
                else:
                    messages.error(request, "Grade must be between 0 and the total marks.")
            except ValueError:
                messages.error(request, "Please enter a valid grade.")
        else:
            messages.error(request, "Grade cannot be empty.")
        
        return redirect('instructor:quiz_grade', submission_id=submission.id)
class ExerciseGradeView(View):
    def get(self, request, submission_id):
        submission = get_object_or_404(ExerciseAttempt, id=submission_id)
        
        question_attempts = submission.question_attempts.all()  
        total_marks = submission.total_marks 
        score = submission.grade  
        
        class_shell = submission.exercise.class_shell  
        
        return render(request, "exercise_grade.html", {
            "exercise": submission.exercise,  
            "question_attempts": question_attempts, 
            "total_marks": total_marks,  
            "score": score,  
            "class_shell": class_shell  
        })
    
    def post(self, request, submission_id):
        submission = get_object_or_404(ExerciseAttempt, id=submission_id)
        
        grade = request.POST.get("grade")
        
        if grade:
            try:
                grade = float(grade)
                if 0 <= grade <= submission.total_marks:
                    submission.grade = grade
                    submission.graded = True  # Mark as graded
                    submission.save()
                    messages.success(request, "Grade has been successfully saved.")
                else:
                    messages.error(request, "Grade must be between 0 and the total marks.")
            except ValueError:
                messages.error(request, "Please enter a valid grade.")
        else:
            messages.error(request, "Grade cannot be empty.")
        
        return redirect('instructor:exercise_grade', submission_id=submission.id)







