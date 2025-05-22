from django.shortcuts import render, redirect, get_object_or_404
from .forms import ClassShellForm, CourseFileForm, CourseForm, QuizForm, QuestionForm, AssignmentForm, AssignmentFileForm, ExerciseForm, ExerciseQuestionForm
from .models import ClassShell, CourseFile, Course, Question, Quiz, Assignment, AssignmentFile, Exercise, ExerciseQuestion, Attendance
from student.models import AssignmentSubmission, QuizAttempt, ExerciseAttempt
from django.views import View
from accounts.models import CustomUser
from django.contrib import messages
from django.db.models import Avg, Sum, Max, StdDev
import plotly.express as px
import pandas as pd
from datetime import datetime
import csv
from django.contrib.auth import get_user_model


def class_shell_list(request):
    edit_class_shell = None
    form = ClassShellForm(request.POST or None)

    if request.method == 'POST':
        class_shell_id = request.POST.get('class_shell_id')

        if class_shell_id:  
            class_shell = get_object_or_404(ClassShell, pk=class_shell_id, user=request.user)
            form = ClassShellForm(request.POST, instance=class_shell)
        else:  
            form = ClassShellForm(request.POST)
            class_shell = form.save(commit=False)
            class_shell.user = request.user

        if form.is_valid():
            form.save()
            return redirect('instructor:class_shell_list')

        elif 'delete' in request.POST:
            class_shell = get_object_or_404(ClassShell, pk=request.POST.get('class_shell_id'), user=request.user)
            class_shell.delete()
            return redirect('instructor:class_shell_list')

    class_shells = ClassShell.objects.filter(user=request.user)
    return render(request, 'class_shell_list.html', {
        'class_shells': class_shells,
        'edit_class_shell': edit_class_shell,
        'form': form,
    })


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
        #attendance
        attendance_records = Attendance.objects.filter(class_shell=class_shell).order_by('-date')
        attendance_grouped = {}
        studentwithacceswithname = class_shell.students_with_access.all()

        for record in attendance_records:
            if record.date not in attendance_grouped:
                attendance_grouped[record.date] = []
            attendance_grouped[record.date].append(record)


        # Get latest submission for each assignment, quiz, and exercise
        ungraded_submissions = {
            'assignments': AssignmentSubmission.objects.filter(graded=False, assignment__class_shell=class_shell)
                            .order_by('assignment', '-submitted_on')
                            ,

            'quizzes': QuizAttempt.objects.filter(graded=False, quiz__class_shell=class_shell, submitted=True)
                        .order_by('quiz', '-attempted_on')
                        ,

            'exercises': ExerciseAttempt.objects.filter(graded=False, exercise__class_shell=class_shell)
                        .order_by('exercise', '-attempted_on')
                        ,
        }

        graded_submissions = {
            'assignments': AssignmentSubmission.objects.filter(graded=True, assignment__class_shell=class_shell)
                            .order_by('assignment', '-submitted_on')
                            ,

            'quizzes': QuizAttempt.objects.filter(graded=True, quiz__class_shell=class_shell)
                        .order_by('quiz', '-attempted_on')
                        ,

            'exercises': ExerciseAttempt.objects.filter(graded=True, exercise__class_shell=class_shell)
                        .order_by('exercise', '-attempted_on')
                        ,
        }
        print("==== Graded Assignment Submissions ====")
        for submission in graded_submissions['assignments']:
            print(f"Assignment: {submission.assignment.title}, Student: {submission.student.username}, Attempt #: {submission.attempt_number}")


        lecture_form = CourseForm()
        lecture_file_form = CourseFileForm()
        quiz_form = QuizForm()
        exercise_form = ExerciseForm()  
        assignment_form = AssignmentForm()

   # analytics section
        # Graded submissions for each assessment type
        assignment_subs_graded = AssignmentSubmission.objects.filter(assignment__class_shell=class_shell, graded=True)
        quiz_subs_graded = QuizAttempt.objects.filter(quiz__class_shell=class_shell, graded=True)
        exercise_subs_graded = ExerciseAttempt.objects.filter(exercise__class_shell=class_shell, submitted=True)

        # Calculate average, max, and std deviation (default to 0 if none)
        avg_assignment = assignment_subs_graded.aggregate(avg=Avg('grade'))['avg'] or 0
        max_assignment = assignment_subs_graded.aggregate(max=Max('grade'))['max'] or 0
        std_assignment = assignment_subs_graded.aggregate(std=StdDev('grade'))['std'] or 0

        avg_quiz = quiz_subs_graded.aggregate(avg=Avg('grade'))['avg'] or 0
        max_quiz = quiz_subs_graded.aggregate(max=Max('grade'))['max'] or 0
        std_quiz = quiz_subs_graded.aggregate(std=StdDev('grade'))['std'] or 0

        avg_exercise = exercise_subs_graded.aggregate(avg=Avg('score'))['avg'] or 0
        max_exercise = exercise_subs_graded.aggregate(max=Max('score'))['max'] or 0
        std_exercise = exercise_subs_graded.aggregate(std=StdDev('score'))['std'] or 0

        # Prepare data for bar chart
        data_bar = {
            'Assessment Type': ['Assignments', 'Quizzes', 'Exercises'],
            'Average Grade': [avg_assignment, avg_quiz, avg_exercise],
            'Max Grade': [max_assignment, max_quiz, max_exercise],
            'Standard Deviation': [std_assignment, std_quiz, std_exercise]
        }
        df_bar = pd.DataFrame(data_bar)

        fig_bar = px.bar(
            df_bar,
            x='Assessment Type',
            y=['Average Grade', 'Max Grade'],
            barmode='group',
            title='Average vs Max Grades per Assessment Type',
            labels={'value': 'Grade', 'variable': 'Metric'}
        )

        chart_bar = fig_bar.to_html(full_html=False)
        # Prepare data for dot plot (standard deviation as point height)
        data_bar2 = {
            'Assessment Type': ['Assignments', 'Quizzes', 'Exercises'],
            'Standard Deviation': [std_assignment, std_quiz, std_exercise]
        }
        df_bar2 = pd.DataFrame(data_bar2)

        fig_bar2 = px.scatter(
            df_bar2,
            x='Assessment Type',
            y='Standard Deviation',
            size=[10, 10, 10],  # Optional: consistent dot size
            title='Grade Variability (Std. Dev.) Across Assessment Types',
            labels={'Standard Deviation': 'Grade StdDev'},
        )

        chart_bar2 = fig_bar2.to_html(full_html=False)




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
            'graded_submissions': graded_submissions,
            'chart_bar': chart_bar,
            'chart_bar2': chart_bar2,
            'attendance_grouped': attendance_grouped,
            'studentwithacceswithname':studentwithacceswithname,
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
            if 'grant_all' in request.POST:  
                selected_students = CustomUser.objects.filter(is_student=True)  
            else:
                selected_student_ids = request.POST.getlist('access_student_ids')
                selected_students = CustomUser.objects.filter(id__in=selected_student_ids, is_student=True)

            class_shell.students_with_access.set(selected_students) 

            User = get_user_model()
            # === Create Single Student Account ===
            if 'create_single' in request.POST:
                first = request.POST.get('first_name', '').strip().lower()
                last = request.POST.get('last_name', '').strip().lower()
                email = request.POST.get('email', '').strip().lower()
                username = f"{first} {last}"
                password = f"{last} {first}"

                user = User.objects.filter(username=username).first()
                if not user:
                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        password=password,
                        is_student=True
                    )
                class_shell.students_with_access.add(user)

            # === Bulk Upload Students from CSV ===
            if 'upload_csv' in request.POST and 'student_csv' in request.FILES:
                try:
                    csv_file = request.FILES['student_csv'].read().decode('utf-8').splitlines()
                    reader = csv.DictReader(csv_file)
                    for row in reader:
                        first = row['first_name'].strip().lower()
                        last = row['last_name'].strip().lower()
                        email = row['email'].strip().lower()
                        username = f"{first} {last}"
                        password = f"{last} {first}"

                        user = User.objects.filter(username=username).first()
                        if not user:
                            user = User.objects.create_user(
                                username=username,
                                email=email,
                                password=password,
                                is_student=True
                            )
                        class_shell.students_with_access.add(user)

                except Exception as e:
                    messages.error(request, f"CSV upload failed: {str(e)}")


        if 'take_attendance' in request.POST:
            try:
                date_str = request.POST.get('attendance_date')
                date = datetime.strptime(date_str, '%Y-%m-%d').date()
                students = class_shell.students_with_access.all()

                for student in students:
                    status_key = f'status_{student.id}'
                    status = request.POST.get(status_key, 'present')
                    Attendance.objects.update_or_create(
                        student=student,
                        class_shell=class_shell,
                        date=date,
                        defaults={'status': status}
                    )
                messages.success(request, 'Attendance recorded successfully!')
            except Exception as e:
                messages.error(request, f'Error saving attendance: {str(e)}')
            return redirect('instructor:go_to_course', class_shell_id=class_shell_id)
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
            assignment_instance.max_attempts = request.POST.get("max_attempts")
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
            quiz_instance.max_attempts = request.POST.get("max_attempts")
            quiz_instance.timer = request.POST.get("timer")
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
            exercise_instance.max_attempts = request.POST.get("max_attempts")
            exercise_instance.timer = request.POST.get("timer")
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
        question_form = QuestionForm()  # fallback

        if 'add_question' in request.POST:
            # Prepare dynamic choices
            choices_raw = request.POST.get('choices', '')
            choices_list = [c.strip() for c in choices_raw.split('\n') if c.strip()]
            
            # Inject choices into the form before validation
            question_form = QuestionForm(request.POST)
            question_form.fields['mcq_answers'].choices = [(c, c) for c in choices_list]

            if question_form.is_valid():
                question_instance = question_form.save(commit=False)
                question_instance.quiz = quiz

                if question_instance.type == 'multiple_choice':
                    question_instance.tf_answer = None
                    question_instance.mcq_choices = choices_list

                    selected_answers = request.POST.getlist('mcq_answers')
                    question_instance.mcq_answers = [a for a in selected_answers if a in choices_list]
                    print('question_instance.mcq_answers add',question_instance.mcq_answers)

                elif question_instance.type == 'true_false':
                    question_instance.mcq_choices = None
                    question_instance.mcq_answers = None
                    question_instance.tf_answer = question_form.cleaned_data['tf_answer']

                elif question_instance.type == 'essay':
                    question_instance.mcq_choices = None
                    question_instance.mcq_answers = None
                    question_instance.tf_answer = None

                question_instance.save()
                return redirect('instructor:go_to_quiz', class_shell_id=class_shell_id, quiz_id=quiz_id)
            else:
                print("Form errors:", question_form.errors)
        elif 'edit_question' in request.POST:
            question_id = request.POST.get('question_id')
            question_instance = get_object_or_404(Question, id=question_id)

            choices_raw = request.POST.get('choices', '')
            choices_list = [c.strip() for c in choices_raw.split('\n') if c.strip()]

            question_form = QuestionForm(request.POST, instance=question_instance)
            question_form.fields['mcq_answers'].choices = [(c, c) for c in choices_list]

            if question_form.is_valid():
                question_instance = question_form.save(commit=False)

                if question_instance.type == 'multiple_choice':
                    question_instance.tf_answer = None
                    question_instance.mcq_choices = choices_list
                    selected_answers = request.POST.getlist('mcq_answers')
                    question_instance.mcq_answers = [a for a in selected_answers if a in choices_list]
                    print('question_instance.mcq_answers upadate',question_instance.mcq_answers)

                elif question_instance.type == 'true_false':
                    question_instance.mcq_choices = None
                    question_instance.mcq_answers = None
                    question_instance.tf_answer = question_form.cleaned_data['tf_answer']

                elif question_instance.type == 'essay':
                    question_instance.mcq_choices = None
                    question_instance.mcq_answers = None
                    question_instance.tf_answer = None

                question_instance.save()
        elif "delete_question" in request.POST:
            question_id = request.POST.get('question_id')
            question_instance = get_object_or_404(Question, id=question_id)
            question_instance.delete()

        questions = Question.objects.filter(quiz=quiz)
        return render(request, 'go_to_quiz.html', {
            'quiz': quiz,
            'questions': questions,
            'question_form': question_form,
            'class_shell_id': class_shell_id
        })
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

        if 'delete_question' in request.POST:
            exercise_question_id = request.POST.get('exerciseQuestion_id')
            if exercise_question_id:
                self.handle_delete_question(exercise_question_id)
            return redirect('instructor:go_to_exercise', class_shell_id=class_shell_id, exercise_id=exercise_id)

        choices_raw = request.POST.get('choices', '')
        choices_list = [c.strip() for c in choices_raw.split('\n') if c.strip()]
        question_form.fields['mcq_answers'].choices = [(c, c) for c in choices_list]

        if 'add_question' in request.POST and question_form.is_valid():
            question_instance = question_form.save(commit=False)
            question_instance.exercise = exercise

            if question_instance.type == 'multiple_choice':
                question_instance.tf_answer = None
                question_instance.mcq_choices = choices_list
                selected_answers = request.POST.getlist('mcq_answers')
                question_instance.mcq_answers = [a for a in selected_answers if a in choices_list]

            elif question_instance.type == 'true_false':
                question_instance.mcq_choices = None
                question_instance.mcq_answers = None
                question_instance.tf_answer = question_form.cleaned_data['tf_answer']

            elif question_instance.type == 'essay':
                question_instance.mcq_choices = None
                question_instance.mcq_answers = None
                question_instance.tf_answer = None

            question_instance.save()
            return redirect('instructor:go_to_exercise', class_shell_id=class_shell_id, exercise_id=exercise_id)

        elif 'edit_question' in request.POST:
            question_id = request.POST.get('exerciseQuestion_id')
            question_instance = get_object_or_404(ExerciseQuestion, id=question_id)
            question_form = ExerciseQuestionForm(request.POST, instance=question_instance)
            question_form.fields['mcq_answers'].choices = [(c, c) for c in choices_list]

            if question_form.is_valid():
                question_instance = question_form.save(commit=False)

                if question_instance.type == 'multiple_choice':
                    question_instance.tf_answer = None
                    question_instance.mcq_choices = choices_list
                    selected_answers = request.POST.getlist('mcq_answers')
                    question_instance.mcq_answers = [a for a in selected_answers if a in choices_list]

                elif question_instance.type == 'true_false':
                    question_instance.mcq_choices = None
                    question_instance.mcq_answers = None
                    question_instance.tf_answer = question_form.cleaned_data['tf_answer']

                elif question_instance.type == 'essay':
                    question_instance.mcq_choices = None
                    question_instance.mcq_answers = None
                    question_instance.tf_answer = None

                question_instance.save()
            else:
                print("Edit form errors:", question_form.errors)

        else:
            print("Add form errors:", question_form.errors)

        return redirect('instructor:go_to_exercise', class_shell_id=class_shell_id, exercise_id=exercise_id)

    def handle_delete_question(self, question_id):
        try:
            exercise_question = get_object_or_404(ExerciseQuestion, id=question_id)
            exercise_question.delete()
        except Exception as e:
            print(f"Error deleting question: {e}")

class QuizGradeView(View):
    def get(self, request, submission_id):
        submission = get_object_or_404(QuizAttempt, id=submission_id)
        print('submission', submission)
        
        question_attempts = submission.question_attempts.all()  
        total_marks = submission.total_marks 
        score = submission.grade  
        
        class_shell = submission.quiz.class_shell  
        
        return render(request, "quiz_grade.html", {
            "quiz": submission.quiz,  
            "question_attempts": question_attempts, 
            "total_marks": total_marks,  
            "score": score,  
            "class_shell": class_shell,
            "submission": submission  
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
class InstructorAnalyticsView(View):
    def get(self, request):
        # Get all class shells created by this instructor
        class_shells = ClassShell.objects.filter(user=request.user)
        
        # Filter graded submissions for the instructor's class shells
        assignment_subs = AssignmentSubmission.objects.filter(
            assignment__class_shell__in=class_shells, graded=True
        )
        quiz_subs = QuizAttempt.objects.filter(
            quiz__class_shell__in=class_shells, graded=True
        )
        exercise_subs = ExerciseAttempt.objects.filter(
            exercise__class_shell__in=class_shells, graded=True
        )

        # Calculate average grades (default to 0 if none)
        avg_assignment = assignment_subs.aggregate(avg=Avg('grade'))['avg'] or 0
        avg_quiz = quiz_subs.aggregate(avg=Avg('grade'))['avg'] or 0
        avg_exercise = exercise_subs.aggregate(avg=Avg('grade'))['avg'] or 0

        # Prepare data for a bar chart: Average Grades per Assessment Type
        data_bar = {
            'Assessment Type': ['Assignments', 'Quizzes', 'Exercises'],
            'Average Grade': [avg_assignment, avg_quiz, avg_exercise]
        }
        df_bar = pd.DataFrame(data_bar)

        fig_bar = px.bar(
            df_bar, 
            x='Assessment Type', 
            y='Average Grade', 
            title='Average Grades per Assessment Type',
            range_y=[0, 100]  # assuming grades are between 0 and 100
        )
        chart_bar = fig_bar.to_html(full_html=False)

        # Also prepare a pie chart for graded vs ungraded submissions
        graded_count = (
            assignment_subs.count() + quiz_subs.count() + exercise_subs.count()
        )
        # Get ungraded counts from each model for this instructor’s classes
        ungraded_assignment = AssignmentSubmission.objects.filter(
            assignment__class_shell__in=class_shells, graded=False
        ).count()
        ungraded_quiz = QuizAttempt.objects.filter(
            quiz__class_shell__in=class_shells, graded=False
        ).count()
        ungraded_exercise = ExerciseAttempt.objects.filter(
            exercise__class_shell__in=class_shells, graded=False
        ).count()
        ungraded_count = ungraded_assignment + ungraded_quiz + ungraded_exercise

        data_pie = {
            'Submission Status': ['Graded', 'Ungraded'],
            'Count': [graded_count, ungraded_count]
        }
        df_pie = pd.DataFrame(data_pie)

        fig_pie = px.pie(
            df_pie, 
            names='Submission Status', 
            values='Count', 
            title='Graded vs Ungraded Submissions'
        )
        chart_pie = fig_pie.to_html(full_html=False)

        context = {
            'chart_bar': chart_bar,
            'chart_pie': chart_pie,
        }
        return render(request, 'instructor_analytics.html', context)






