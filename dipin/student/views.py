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
        # --- Assignments ---
        submitted_assignment_marks = sum(a.total_marks for a in assignments if a.id in submitted_assignment_ids)
        submitted_assignment_score = sum(sub['grade'] for sub in submitted_assignments_info if sub['grade'] is not None)

        # --- Quizzes ---
        submitted_quiz_marks = sum(sum(q.mark for q in Question.objects.filter(quiz=quiz)) for quiz in quizzes if quiz.id in submitted_quiz_ids)
        submitted_quiz_score = sum(sub['grade'] for sub in submitted_quizzes_info if sub['grade'] is not None)

        # --- Exercises ---
        submitted_exercise_marks = sum(sum(eq.mark for eq in ExerciseQuestion.objects.filter(exercise=exercise)) for exercise in exercises if exercise.id in submitted_exercise_ids)
        submitted_exercise_score = sum(sub['grade'] for sub in submitted_exercises_info if sub['grade'] is not None)
        
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
        overall_total_marks = submitted_assignment_marks + submitted_quiz_marks + submitted_exercise_marks
        overall_score = submitted_assignment_score + submitted_quiz_score + submitted_exercise_score

        # Avoid division by zero
        overall_percentage = (overall_score / overall_total_marks) * 100 if overall_total_marks > 0 else 0
        grade = 'A' if overall_percentage >= 90 else 'B' if overall_percentage >= 80 else 'C' if overall_percentage >= 70 else 'D' if overall_percentage >= 60 else 'F'
        # Categories and values for submitted items
        categories = ["Assignments", "Quizzes", "Exercises", "Overall"]
        scores = [submitted_assignment_score, submitted_quiz_score, submitted_exercise_score, overall_score]
        max_marks = [submitted_assignment_marks, submitted_quiz_marks, submitted_exercise_marks, overall_total_marks]
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
            'assignments': assignments,
            'exercises': exercises,
            'files': files,
            'submitted_assignments_info': submitted_assignments_info,
            'submitted_assignment_ids': submitted_assignment_ids,
            'submitted_quizzes_info': submitted_quizzes_info,
            'submitted_quiz_ids': submitted_quiz_ids,
            'submitted_exercises_info': submitted_exercises_info,
            'submitted_exercise_ids': submitted_exercise_ids,
            'now': now,
            # Overall grade details for the interactive chart section
            'overall_total_marks': overall_total_marks,
            'overall_score': overall_score,
            'overall_percentage': overall_percentage,
            'grade': grade,
            'interactive_overall_chart': interactive_overall_chart,
            'attendance_percentage': attendance_percentage,
        })

    def post(self, request, class_shell_id):
        assignment_id = request.POST.get('assignment_id')
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
    from django.shortcuts import render, redirect, get_object_or_404
    from django.utils import timezone
    from datetime import timedelta
    # (Assume your models are imported, e.g., ClassShell, Quiz, Question, QuizAttempt, QuestionAttempt)

    class_shell = get_object_or_404(ClassShell, id=class_shell_id)
    quiz = get_object_or_404(Quiz, id=quiz_id, class_shell=class_shell)
    questions = Question.objects.filter(quiz=quiz)
    total_marks = sum(question.mark for question in questions)

    # Retrieve previous attempts for this student and quiz.
    attempts = QuizAttempt.objects.filter(student=request.user, quiz=quiz).order_by('attempt_number')
    current_attempt = attempts.count() + 1
    attempts_left = quiz.max_attempts - attempts.count()
    max_attempts_reached = (attempts_left <= 0)

    # NEW ATTEMPT: when a student clicks a "start new attempt" link.
    if "start_new_attempt" in request.GET:
        if attempts_left <= 0:
            return redirect('student:attempt_quiz', class_shell_id=class_shell_id, quiz_id=quiz_id)
        # Calculate a new end time.
        end_time = timezone.now() + timedelta(minutes=quiz.timer)
        context = {
            'quiz': quiz,
            'questions': questions,
            'score': None,
            'total_marks': total_marks,
            'class_shell': class_shell,
            'quiz_id': quiz_id,
            'already_attempted': False,
            'previous_attempts': attempts,
            'current_attempt': current_attempt,
            'attempts_left': attempts_left,
            'max_attempts_reached': max_attempts_reached,
            'end_time': end_time.timestamp(),  # Passed as seconds.
        }
        return render(request, 'attempt_quiz.html', context)

    # Viewing a previously submitted attempt (e.g., for review).
    if "view" in request.GET:
        if attempts.exists():
            # Compute highest score among all attempts.
            highest_score = max(attempt.score for attempt in attempts)
            # For review, you might still want to list all question attempts from the last submission
            attempt_to_view = attempts.last()
            question_attempts = QuestionAttempt.objects.filter(quiz_attempt=attempt_to_view)
            context = {
                'quiz': quiz,
                'already_attempted': True,
                'view_submitted': True,
                'total_marks': total_marks,
                'score': highest_score,  # Only highest score counts.
                'question_attempts': question_attempts,
                'class_shell': class_shell,
                'previous_attempts': attempts,
                'current_attempt': current_attempt,
                'attempts_left': attempts_left,
                'max_attempts_reached': max_attempts_reached,
            }
            return render(request, 'attempt_quiz.html', context)

    # Process submissions (both manual and auto submissions when time expires)
    if request.method == "POST":
        if attempts_left <= 0:
            return redirect('student:attempt_quiz', class_shell_id=class_shell_id, quiz_id=quiz_id)

        score = 0
        quiz_attempt = QuizAttempt.objects.create(
            student=request.user,
            quiz=quiz,
            class_shell=class_shell,
            total_marks=total_marks,
            attempt_number=current_attempt
        )

        # Process each question.
        for question in questions:
            user_answer = request.POST.get(f'answer_{question.id}', 'n/a')
            is_correct = False
            if user_answer != 'n/a':
                if question.type == "multiple_choice":
                    print('quiz ans', question.mcq_answer )
                    is_correct = (user_answer == question.mcq_answer)
                elif question.type == "true_false":
                    is_correct = (str(user_answer) == str(question.tf_answer))

            QuestionAttempt.objects.create(
                quiz_attempt=quiz_attempt,
                question=question,
                student_answer=user_answer,
                is_correct=is_correct,
            )
            if is_correct:
                score += question.mark

        quiz_attempt.score = score
        quiz_attempt.save()
        return redirect('student:attempt_quiz', class_shell_id=class_shell_id, quiz_id=quiz_id)

    # Default GET: Show either the summary or the quiz form.
    if attempts.exists():
        # Compute the highest score among all attempts.
        highest_score = max(attempt.score for attempt in attempts)
        context = {
            'quiz': quiz,
            'already_attempted': True,
            'view_submitted': False,
            'score': highest_score,  # Highest score is used.
            'total_marks': total_marks,
            'class_shell': class_shell,
            'previous_attempts': attempts,
            'current_attempt': current_attempt,
            'attempts_left': attempts_left,
            'max_attempts_reached': max_attempts_reached,
        }
        return render(request, 'attempt_quiz.html', context)
    else:
        # First GET request to start the quiz.
        end_time = timezone.now() + timedelta(minutes=quiz.timer)
        context = {
            'quiz': quiz,
            'questions': questions,
            'score': None,
            'total_marks': total_marks,
            'class_shell': class_shell,
            'quiz_id': quiz_id,
            'already_attempted': False,
            'previous_attempts': attempts,
            'current_attempt': current_attempt,
            'attempts_left': attempts_left,
            'max_attempts_reached': max_attempts_reached,
            'end_time': end_time.timestamp(),  # Passed as seconds.
        }
        return render(request, 'attempt_quiz.html', context)


def attempt_exercise(request, class_shell_id, exercise_id): 
    from django.shortcuts import render, get_object_or_404, redirect

    class_shell = get_object_or_404(ClassShell, id=class_shell_id)
    exercise = get_object_or_404(Exercise, id=exercise_id, class_shell=class_shell)
    exercise_questions = ExerciseQuestion.objects.filter(exercise=exercise)
    total_marks = sum(question.mark for question in exercise_questions)
    
    # Retrieve all previous attempts by the student for this exercise.
    attempts = ExerciseAttempt.objects.filter(student=request.user, exercise=exercise).order_by('attempt_number')
    current_attempt = attempts.count() + 1
    attempts_left = exercise.max_attempts - attempts.count()
    max_attempts_reached = attempts_left <= 0

    # If the student requested to view a submitted exercise, display the latest attempt’s review.
    if "view" in request.GET:
        if attempts.exists():
            attempt_to_view = attempts.last()
            question_attempts = ExerciseQuestionAttempt.objects.filter(exercise_attempt=attempt_to_view)
            context = {
                'exercise': exercise,
                'already_attempted': True,
                'view_submitted': True,
                'total_marks': total_marks,
                'score': attempt_to_view.score,
                'question_attempts': question_attempts,
                'class_shell': class_shell,
                'previous_attempts': attempts,
                'current_attempt': current_attempt,
                'attempts_left': attempts_left,
                'max_attempts_reached': max_attempts_reached,
            }
            return render(request, 'attempt_exercise.html', context)
    
    # Process a new attempt submission.
    if request.method == "POST":
        # Check if the student is allowed to attempt again.
        if attempts_left <= 0:
            # Optionally add a message notifying the student.
            return redirect('student:attempt_exercise', class_shell_id=class_shell_id, exercise_id=exercise_id)

        score = 0
        # Create a new ExerciseAttempt with the current attempt number.
        exercise_attempt = ExerciseAttempt.objects.create(
            student=request.user,
            exercise=exercise,
            class_shell=class_shell,
            total_marks=total_marks,
            attempt_number=current_attempt
        )

        for exercise_question in exercise_questions:
            user_answer = request.POST.get(f'answer_{exercise_question.id}')
            is_correct = False

            if exercise_question.type == "multiple_choice":
                if user_answer:
                    print(exercise_question.mcq_answer)
                    is_correct = user_answer == str(exercise_question.mcq_answer)
            elif exercise_question.type == "true_false":
                if user_answer is not None:  
                    is_correct = (str(user_answer).strip().lower() == str(exercise_question.tf_answer).strip().lower())
            # For essay questions, you may want to add manual grading later.

            ExerciseQuestionAttempt.objects.create(
                exercise_attempt=exercise_attempt,
                exercise_question=exercise_question,
                student_answer=user_answer,
                is_correct=is_correct,
            )

            if is_correct:
                score += exercise_question.mark

        exercise_attempt.score = score
        exercise_attempt.save()
        return redirect('student:attempt_exercise', class_shell_id=class_shell_id, exercise_id=exercise_id)

    # Handle GET requests:
    # If the student clicked "start new attempt" (and if attempts remain), show the exercise form.
    if "start_new_attempt" in request.GET:
        if attempts_left <= 0:
            return redirect('student:attempt_exercise', class_shell_id=class_shell_id, exercise_id=exercise_id)
        context = {
            'exercise': exercise,
            'exercise_questions': exercise_questions,
            'score': None,
            'total_marks': total_marks,
            'class_shell': class_shell,
            'exercise_id': exercise_id,
            'already_attempted': False,  # New attempt in progress
            'previous_attempts': attempts,
            'current_attempt': current_attempt,
            'attempts_left': attempts_left,
            'max_attempts_reached': max_attempts_reached,
        }
        return render(request, 'attempt_exercise.html', context)

    # Default GET:
    # If there are any previous attempts, show the latest attempt's details along with attempt information.
    if attempts.exists():
        last_attempt = attempts.last()
        context = {
            'exercise': exercise,
            'already_attempted': True,
            'view_submitted': False,
            'score': last_attempt.score,
            'total_marks': total_marks,
            'class_shell': class_shell,
            'previous_attempts': attempts,
            'current_attempt': current_attempt,
            'attempts_left': attempts_left,
            'max_attempts_reached': max_attempts_reached,
        }
        return render(request, 'attempt_exercise.html', context)
    else:
        # No attempts yet: show the exercise form.
        context = {
            'exercise': exercise,
            'exercise_questions': exercise_questions,
            'score': None,
            'total_marks': total_marks,
            'class_shell': class_shell,
            'exercise_id': exercise_id,
            'already_attempted': False,
            'previous_attempts': attempts,
            'current_attempt': current_attempt,
            'attempts_left': attempts_left,
            'max_attempts_reached': max_attempts_reached,
        }
        return render(request, 'attempt_exercise.html', context)
