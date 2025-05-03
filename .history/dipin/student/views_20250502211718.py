from django.shortcuts import render, get_object_or_404, redirect
from instructor.models import (
    ClassShell, Course, Quiz, Assignment, Exercise, Question, CourseFile, ExerciseQuestion, Attendance
)
from .models import (
    QuizAttempt, QuestionAttempt, AssignmentSubmission, ExerciseQuestionAttempt, ExerciseAttempt
)
from django.views import View
from django.contrib import messages
from datetime import datetime
from datetime import timedelta
from django.utils import timezone
from django.http import JsonResponse
import plotly.graph_objects as go
import plotly.offline as opy
import pytz

def course_list(request):
    student = request.user
    class_shells = ClassShell.objects.filter(students_with_access=student)    
    return render(request, 'course_list.html', {'class_shells': class_shells})

class go_to_course_student(View):
    def get(self, request, class_shell_id):
        class_shell = get_object_or_404(ClassShell, id=class_shell_id)
        if request.user not in class_shell.students_with_access.all():
            return redirect('no_access')

        lectures = Course.objects.filter(class_shell=class_shell)
        files = CourseFile.objects.filter(class_shell=class_shell)
        quizzes = Quiz.objects.filter(class_shell=class_shell)
        exercises = Exercise.objects.filter(class_shell=class_shell)
        assignments = Assignment.objects.filter(class_shell=class_shell)
        utc_now = datetime.utcnow().replace(tzinfo=pytz.utc)
        now = utc_now - timedelta(hours=6)
        latest_assignments = AssignmentSubmission.objects.filter(student=request.user)\
            .order_by('assignment_id', '-submitted_on')\
            .distinct('assignment_id')
        latest_assignments_info = [
            {
                'assignment_id': submission.assignment.id,  
                'submission_text': submission.submission_text,
                'submission_file': submission.submission_file,
                'grade': submission.grade,
                'total_marks': submission.assignment.total_marks if submission.assignment else None
            }
            for submission in latest_assignments
        ]

        latest_quizzes = QuizAttempt.objects.filter(student=request.user)\
            .order_by('quiz_id', '-attempted_on')\
            .distinct('quiz_id')

        # --- Assignments ---
        submitted_assignments = AssignmentSubmission.objects.filter(student=request.user).values_list(
            'assignment', 'submission_text', 'submission_file', 'grade'
        )
        submitted_assignments_info = [
            {
                'assignment_id': submission[0],
                'submission_text': submission[1],
                'submission_file': submission[2],
                'grade': submission[3],
                'total_marks': Assignment.objects.get(id=submission[0]).total_marks
            }
            for submission in submitted_assignments
        ]
        submitted_assignment_ids = set(
            AssignmentSubmission.objects.filter(student=request.user)
            .values_list('assignment', flat=True)
        )
        
        # --- Quizzes ---
        submitted_quizzes = QuizAttempt.objects.filter(student=request.user, quiz__class_shell=class_shell)
        submitted_quizzes_info = [
            {'grade': quiz_attempt.grade,'quiz_id': quiz_attempt.quiz.id, 'score': quiz_attempt.score, 'total_marks': quiz_attempt.total_marks}
            for quiz_attempt in submitted_quizzes
        ]
        submitted_quiz_ids = set(
            submitted_quizzes.values_list('quiz', flat=True)
        )
        # --- Exercises ---
        submitted_exercises = ExerciseAttempt.objects.filter(student=request.user, exercise__class_shell=class_shell)
        submitted_exercises_info = [
            { 'grade': exercise_attempt.grade,'exercise_id': exercise_attempt.exercise.id, 'score': exercise_attempt.score, 'total_marks': exercise_attempt.total_marks}
            for exercise_attempt in submitted_exercises
        ]
        submitted_exercise_ids = set(
            submitted_exercises.values_list('exercise', flat=True)
        )

        # --- Attendance ---
        attendance_records = Attendance.objects.filter(student=request.user, class_shell=class_shell)
        total_attendance_days = attendance_records.count()

        if total_attendance_days > 0:
            present_days = attendance_records.filter(status__in=['present', 'excused']).count()
            late_days = attendance_records.filter(status='late').count()
            attendance_percentage = ((present_days * 1.0) + (late_days * 0.75)) / total_attendance_days * 100
        else:
            attendance_percentage = 100  # Default to 100% if no attendance records exist

        # Calculate overall marks and scores based on submitted items only
        submitted_assignment_marks = sum(a.total_marks for a in assignments if a.id in submitted_assignment_ids)
        submitted_assignment_score = sum(sub['grade'] for sub in submitted_assignments_info if sub['grade'] is not None)

        # --- Quizzes ---
        submitted_quiz_marks = sum(sum(q.mark for q in Question.objects.filter(quiz=quiz)) for quiz in quizzes if quiz.id in submitted_quiz_ids)
        submitted_quiz_score = sum(sub['grade'] for sub in submitted_quizzes_info if sub['grade'] is not None)

        # Calculate overall marks and scores without exercises
        overall_total_marks = submitted_assignment_marks + submitted_quiz_marks
        overall_score = submitted_assignment_score + submitted_quiz_score

        # Avoid division by zero
        overall_percentage = (overall_score / overall_total_marks) * 100 if overall_total_marks > 0 else 0
        grade = 'A' if overall_percentage >= 90 else 'B' if overall_percentage >= 80 else 'C' if overall_percentage >= 70 else 'D' if overall_percentage >= 60 else 'F'

        # Categories and values for submitted items (without exercises)
        categories = ["Assignments", "Quizzes", "Overall"]
        scores = [submitted_assignment_score, submitted_quiz_score, overall_score]
        max_marks = [submitted_assignment_marks, submitted_quiz_marks, overall_total_marks]
        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=categories,
            y=scores,
            name="Grade Achieved",
            marker_color="#800000",  
            textposition='outside'
        ))

        fig.add_trace(go.Bar(
            x=categories,
            y=max_marks,
            name="Total Marks",
            marker_color="#f5f5f5",  
            textposition='outside'
        ))

        fig.update_layout(
            title="Grade Breakdown",
            title_x=0.5,  
            barmode='group',
            template="plotly_white"
        )
        interactive_overall_chart = opy.plot(fig, output_type='div', include_plotlyjs=False)

        return render(request, 'go_to_course_student.html', {
            'class_shell': class_shell,
            'lectures': lectures,
            'quizzes': quizzes,
            'exercises': exercises,
            'assignments': assignments,
            'files': files,
            'submitted_assignments_info': submitted_assignments_info,
            'submitted_assignment_ids': submitted_assignment_ids,
            'submitted_quizzes_info': submitted_quizzes_info,
            'submitted_quiz_ids': submitted_quiz_ids,
            'submitted_exercises_info': submitted_exercises_info,
            'submitted_exercise_ids': submitted_exercise_ids,
            'now': now,
            'latest_assignments': latest_assignments,
            "latest_quizzes": latest_quizzes,
            'latest_assignments_info': latest_assignments_info,
            # Overall grade details for the interactive chart section
            'overall_total_marks': overall_total_marks,
            'overall_score': overall_score,
            'overall_percentage': overall_percentage,
            'grade': grade,
            'interactive_overall_chart': interactive_overall_chart,
            'attendance_percentage': attendance_percentage,
        })


    def post(self, request, class_shell_id):
        # Handle form submission for assignments
        assignment_id = request.POST.get('assignment_id')
        if assignment_id:
            assignment = get_object_or_404(Assignment, id=assignment_id)
            submission_text = request.POST.get('submission_text')
            submission_file = request.FILES.get('submission_file')

            assignment_submission = AssignmentSubmission(
                assignment=assignment,
                student=request.user,
                submission_text=submission_text,
            )

            if submission_file:
                assignment_submission.submission_file = submission_file    
            assignment_submission.save()
            return redirect('student:go_to_course', class_shell_id=class_shell_id)



def attempt_quiz(request, class_shell_id, quiz_id):
    class_shell = get_object_or_404(ClassShell, id=class_shell_id)
    quiz = get_object_or_404(Quiz, id=quiz_id, class_shell=class_shell)
    questions = Question.objects.filter(quiz=quiz)
    total_marks = sum(question.mark for question in questions)

    # Retrieve previous attempts for this student and quiz.
    attempts = QuizAttempt.objects.filter(student=request.user, quiz=quiz).order_by('attempt_number')
    attempts_left = quiz.max_attempts - attempts.count()
    current_attempt = attempts.count()
    ongoing_attempt = QuizAttempt.objects.filter(
            student=request.user, quiz=quiz, attempt_number=current_attempt, end_time__gt=timezone.now(), submitted=False 
        ).first()
    
    max_attempts_reached = (attempts_left <= 0)
    
    if not attempts.exists():
            current_attempt+=1  
            end_time = timezone.now() + timedelta(minutes=quiz.timer)
            quiz_attempt = QuizAttempt.objects.create(
                student=request.user,
                quiz=quiz,
                class_shell=class_shell,
                total_marks=total_marks,
                attempt_number=current_attempt,
                end_time=end_time
            )
            print('first attempt created:',quiz_attempt)

            return redirect('student:while_quiz', class_shell_id=class_shell_id, quiz_id=quiz_id)
    # NEW ATTEMPT: when a student clicks "start new attempt"
    if "start_new_attempt" in request.GET:       

        # If no ongoing attempt exists or the current attempt has expired, create a new one
        if not ongoing_attempt:
            current_attempt += 1
            end_time = timezone.now() + timedelta(minutes=quiz.timer)
            quiz_attempt = QuizAttempt.objects.create(
                student=request.user,
                quiz=quiz,
                class_shell=class_shell,
                total_marks=total_marks,
                attempt_number=current_attempt,
                end_time=end_time
            )
            quiz_attempt.save()
            print('New attempt created:', quiz_attempt.attempt_number)

        return redirect('student:while_quiz', class_shell_id=class_shell_id, quiz_id=quiz_id)


    # Viewing a previously submitted attempt
    if "view" in request.GET:
        attempt_to_view = attempts.last()
        question_attempts = QuestionAttempt.objects.filter(quiz_attempt=attempt_to_view)
        print('latest attempt',question_attempts)

        return render(request, 'attempt_quiz.html', {
            'quiz': quiz,
            'already_attempted': True,
            'view_submitted': True,
            'total_marks': total_marks,
            'question_attempts': question_attempts,
            'class_shell': class_shell,
            'previous_attempts': attempts,
            'current_attempt': current_attempt,
            'attempts_left': attempts_left,
            'max_attempts_reached': max_attempts_reached,
            'ongoing_attempt': ongoing_attempt,
        })

    # Default GET: Show attempt history or quiz options.
    if attempts.exists():
        print('attempt',attempts)
        highest_score = max(attempt.score for attempt in attempts)
        return render(request, 'attempt_quiz.html', {
            'quiz': quiz,
            'already_attempted': True,
            'view_submitted': False,
            'score': highest_score,
            'total_marks': total_marks,
            'class_shell': class_shell,
            'previous_attempts': attempts,
            'current_attempt': current_attempt,
            'attempts_left': attempts_left,
            'max_attempts_reached': max_attempts_reached,
            'ongoing_attempt': ongoing_attempt,
        })

def while_quiz(request, class_shell_id, quiz_id):
    class_shell = get_object_or_404(ClassShell, id=class_shell_id)
    quiz = get_object_or_404(Quiz, id=quiz_id, class_shell=class_shell)
    questions = Question.objects.filter(quiz=quiz)

    # Get latest attempt
    quiz_attempt = QuizAttempt.objects.filter(student=request.user, quiz=quiz).order_by('-attempt_number').first()
    quiz_attempt_id = quiz_attempt.id
    current_time = timezone.now()
    remaining_time = int((quiz_attempt.end_time - current_time).total_seconds())

    # Get the saved answers from the database
    saved_answers = {
        qa.question.id: qa.student_answer
        for qa in QuestionAttempt.objects.filter(quiz_attempt=quiz_attempt)
    }

    # Pass saved answers to the template
    for question in questions:
        question.saved_answer = saved_answers.get(question.id)
    for question in questions:
        QuestionAttempt.objects.get_or_create(
            quiz_attempt=quiz_attempt,
            question=question,
            defaults={
                'student_answer': 'n/a',
                'is_correct': False
            }
        )
    if request.method == 'POST':
        # Handle form submission
        score = 0
        for question in questions:
            user_answer = request.POST.get(f'answer_{question.id}', 'n/a')
            is_correct = False
            if user_answer != 'n/a':
                if question.type == "multiple_choice":
                    is_correct = (user_answer == question.mcq_answers)
                elif question.type == "true_false":
                    is_correct = (str(user_answer) == str(question.tf_answer))

            QuestionAttempt.objects.update_or_create(
                quiz_attempt=quiz_attempt,
                question=question,
                defaults={
                    'student_answer': user_answer,
                    'is_correct': is_correct
                }
            )

            if is_correct:
                score += question.mark

        quiz_attempt.score = score
        quiz_attempt.submitted = True
        quiz_attempt.save()
        return redirect('student:attempt_quiz', class_shell_id=class_shell_id, quiz_id=quiz_id)

    return render(request, 'while_quiz.html', {
        'class_shell_id': class_shell_id,
        'quiz_id': quiz_id,
        'questions': questions,
        'remaining_time': remaining_time,
        'quiz_attempt_id': quiz_attempt_id,
    })


def autosave_answer(request):
    question_id = request.POST.get('question_id')
    selected_answer = request.POST.get('selected_answer')
    quiz_attempt_id = request.POST.get('quiz_attempt_id')

    if not all([question_id, selected_answer, quiz_attempt_id]):
        return JsonResponse({
            'error': 'Missing parameters',
            'received': dict(request.POST)
        }, status=400)

    try:
        quiz_attempt = QuizAttempt.objects.get(id=quiz_attempt_id, student=request.user)
        question = Question.objects.get(id=question_id)

        # Check if selected answer is correct
        if question.type == "multiple_choice":
            is_correct = (selected_answer == question.mcq_answer)
        elif question.type == "true_false":
            is_correct = (selected_answer == str(question.tf_answer))

        # Save or update the answer attempt
        QuestionAttempt.objects.update_or_create(
            quiz_attempt=quiz_attempt,
            question=question,
            defaults={
                'student_answer': selected_answer,
                'is_correct': is_correct
            }
        )

        # Recalculate score based on all current attempts
        total_score = 0
        attempts = QuestionAttempt.objects.filter(quiz_attempt=quiz_attempt)
        for attempt in attempts:
            if attempt.is_correct:
                total_score += attempt.question.mark

        # Update score in quiz attempt
        quiz_attempt.score = total_score
        quiz_attempt.save()

        return JsonResponse({'success': True, 'updated_score': total_score})

    except QuizAttempt.DoesNotExist:
        return JsonResponse({'error': 'Quiz attempt not found'}, status=404)
    except Question.DoesNotExist:
        return JsonResponse({'error': 'Question not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)



def attempt_exercise(request, class_shell_id, exercise_id):
    class_shell = get_object_or_404(ClassShell, id=class_shell_id)
    exercise = get_object_or_404(Exercise, id=exercise_id, class_shell=class_shell)
    questions = ExerciseQuestion.objects.filter(exercise=exercise)
    total_marks = sum(question.mark for question in questions)

    attempts = ExerciseAttempt.objects.filter(student=request.user, exercise=exercise).order_by('attempt_number')
    attempts_left = exercise.max_attempts - attempts.count()
    current_attempt = attempts.count()
    ongoing_attempt = ExerciseAttempt.objects.filter(
        student=request.user, exercise=exercise, attempt_number=current_attempt, end_time__gt=timezone.now(), submitted=False
    ).first()
    max_attempts_reached = (attempts_left <= 0)

    if not attempts.exists():
        current_attempt += 1
        end_time = timezone.now() + timedelta(minutes=exercise.timer)
        exercise_attempt = ExerciseAttempt.objects.create(
            student=request.user,
            exercise=exercise,
            class_shell=class_shell,
            total_marks=total_marks,
            attempt_number=current_attempt,
            end_time=end_time
        )
        return redirect('student:while_exercise', class_shell_id=class_shell_id, exercise_id=exercise_id)

    if "start_new_attempt" in request.GET:
        if not ongoing_attempt:
            current_attempt += 1
            end_time = timezone.now() + timedelta(minutes=exercise.timer)
            exercise_attempt = ExerciseAttempt.objects.create(
                student=request.user,
                exercise=exercise,
                class_shell=class_shell,
                total_marks=total_marks,
                attempt_number=current_attempt,
                end_time=end_time
            )
        return redirect('student:while_exercise', class_shell_id=class_shell_id, exercise_id=exercise_id)

    if "view" in request.GET:
        attempt_to_view = attempts.last()
        question_attempts = ExerciseQuestionAttempt.objects.filter(exercise_attempt=attempt_to_view)
        return render(request, 'attempt_exercise.html', {
            'exercise': exercise,
            'already_attempted': True,
            'view_submitted': True,
            'total_marks': total_marks,
            'question_attempts': question_attempts,
            'class_shell': class_shell,
            'previous_attempts': attempts,
            'current_attempt': current_attempt,
            'attempts_left': attempts_left,
            'max_attempts_reached': max_attempts_reached,
            'ongoing_attempt': ongoing_attempt,
        })

    if attempts.exists():
        highest_score = max(attempt.score for attempt in attempts)
        return render(request, 'attempt_exercise.html', {
            'exercise': exercise,
            'already_attempted': True,
            'view_submitted': False,
            'score': highest_score,
            'total_marks': total_marks,
            'class_shell': class_shell,
            'previous_attempts': attempts,
            'current_attempt': current_attempt,
            'attempts_left': attempts_left,
            'max_attempts_reached': max_attempts_reached,
            'ongoing_attempt': ongoing_attempt,
        })
def while_exercise(request, class_shell_id, exercise_id):
    class_shell = get_object_or_404(ClassShell, id=class_shell_id)
    exercise = get_object_or_404(Exercise, id=exercise_id, class_shell=class_shell)
    questions = ExerciseQuestion.objects.filter(exercise=exercise)

    exercise_attempt = ExerciseAttempt.objects.filter(student=request.user, exercise=exercise).order_by('-attempt_number').first()
    exercise_attempt_id = exercise_attempt.id
    current_time = timezone.now()
    remaining_time = int((exercise_attempt.end_time - current_time).total_seconds())

    saved_answers = {
        eaq.exercise_question.id: eaq.student_answer
        for eaq in ExerciseQuestionAttempt.objects.filter(exercise_attempt=exercise_attempt)
    }

    for question in questions:
        question.saved_answer = saved_answers.get(question.id)
        ExerciseQuestionAttempt.objects.get_or_create(
            exercise_attempt=exercise_attempt,
            exercise_question=question,
            defaults={
                'student_answer': 'n/a',
                'is_correct': False
            }
        )

    if request.method == 'POST':
        print('post vayo')

        score = 0
        for question in questions:
            user_answer = request.POST.get(f'answer_{question.id}', 'n/a')
            is_correct = False
            if user_answer != 'n/a':
                if question.type == "multiple_choice":
                    is_correct = (user_answer == question.mcq_answer)
                elif question.type == "true_false":
                    is_correct = (str(user_answer) == str(question.tf_answer))

            ExerciseQuestionAttempt.objects.update_or_create(
                exercise_attempt=exercise_attempt,
                exercise_question=question,
                defaults={
                    'student_answer': user_answer,
                    'is_correct': is_correct
                }
            )

            if is_correct:
                score += question.mark

        exercise_attempt.score = score
        exercise_attempt.submitted = True
        exercise_attempt.save()
        print('submit vayo')
        return redirect('student:attempt_exercise', class_shell_id=class_shell_id, exercise_id=exercise_id)
    print('submit vayana')

    return render(request, 'while_exercise.html', {
        'class_shell_id': class_shell_id,
        'exercise_id': exercise_id,
        'questions': questions,
        'remaining_time': remaining_time,
        'exercise_attempt_id': exercise_attempt_id,
    })
def autosave_answer_exercise(request):
    exercise_question_id = request.POST.get('question_id')
    selected_answer = request.POST.get('selected_answer')
    exercise_attempt_id = request.POST.get('exercise_attempt_id')
    if not all([exercise_question_id, selected_answer, exercise_attempt_id]):
        return JsonResponse({
            'error': 'Missing parameters',
            'received': dict(request.POST)
        }, status=400)

    try:
        print('here')

        exercise_attempt = ExerciseAttempt.objects.get(id=exercise_attempt_id, student=request.user)
        exercise_question = ExerciseQuestion.objects.get(id=exercise_question_id)

        # Check if the selected answer is correct
        is_correct = False
        if exercise_question.type == "multiple_choice":
            is_correct = (selected_answer == str(exercise_question.mcq_answer))
        elif exercise_question.type == "true_false":
            is_correct = (selected_answer == str(exercise_question.tf_answer))

        # Save or update the answer attempt
        ExerciseQuestionAttempt.objects.update_or_create(
            exercise_attempt=exercise_attempt,
            exercise_question=exercise_question,
            defaults={
                'student_answer': selected_answer,
                'is_correct': is_correct
            }
        )

        # Recalculate score based on all current attempts
        total_score = 0
        attempts = ExerciseQuestionAttempt.objects.filter(exercise_attempt=exercise_attempt)
        for attempt in attempts:
            if attempt.is_correct:
                total_score += attempt.exercise_question.mark

        # Update score in exercise attempt
        exercise_attempt.score = total_score
        exercise_attempt.save()

        return JsonResponse({'success': True, 'updated_score': total_score})

    except ExerciseAttempt.DoesNotExist:
        return JsonResponse({'error': 'Exercise attempt not found'}, status=404)
    except ExerciseQuestion.DoesNotExist:
        return JsonResponse({'error': 'Exercise question not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
