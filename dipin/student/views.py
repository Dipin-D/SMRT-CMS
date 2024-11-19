from django.shortcuts import render, get_object_or_404, redirect
from instructor.models import ClassShell, Course, Quiz, Assignment, Exercise, Question, CourseFile,ExerciseQuestion
from .models import QuizAttempt, QuestionAttempt,AssignmentSubmission, ExerciseQuestionAttempt, ExerciseAttempt
from accounts.models import CustomUser
from django.views import View



def course_list(request):
    student = request.user
    class_shells = ClassShell.objects.filter(students_with_access=student)
    print(f'Student: {request.user}, Accessible Class Shells: {class_shells}')
    
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
        submitted_assignments = AssignmentSubmission.objects.filter(student=request.user).values_list('assignment', 'submission_text', 'submission_file')

        submitted_assignments_info = [
            {'assignment_id': submission[0], 'submission_text': submission[1], 'submission_file': submission[2]}
            for submission in submitted_assignments
        ]
        submitted_assignment_ids = set(
        AssignmentSubmission.objects.filter(student=request.user)
        .values_list('assignment', flat=True)
        )
        
        return render(request, 'go_to_course_student.html', {
            'class_shell': class_shell,
            'lectures': lectures,
            'quizzes': quizzes,
            'assignments': assignments,
            'exercises': exercises,
            'files': files,
            'submitted_assignments': submitted_assignments,
            'submitted_assignments_info':submitted_assignments_info,
            'submitted_assignment_ids':submitted_assignment_ids,
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

def attempt_quiz(request, class_shell_id, quiz_id):
    class_shell = get_object_or_404(ClassShell, id=class_shell_id)
    quiz = get_object_or_404(Quiz, id=quiz_id, class_shell=class_shell)
    questions = Question.objects.filter(quiz=quiz)
    total_marks = sum(question.mark for question in questions)
    attempt = QuizAttempt.objects.filter(student=request.user, quiz=quiz).first()

    if attempt:
        if "view" in request.GET:
            question_attempts = QuestionAttempt.objects.filter(quiz_attempt=attempt)
            context = {
                'quiz': quiz,
                'already_attempted': True,
                'view_submitted': True,
                'total_marks': total_marks,
                'score': attempt.score,
                'question_attempts': question_attempts,
                'class_shell': class_shell,
            }
            return render(request, 'attempt_quiz.html', context)

        context = {
            'quiz': quiz,
            'already_attempted': True,
            'view_submitted': False,
            'score': attempt.score,
            'total_marks': total_marks,
            'class_shell': class_shell,
        }
        return render(request, 'attempt_quiz.html', context)

    if request.method == "POST":
        score = 0
        quiz_attempt = QuizAttempt.objects.create(
            student=request.user,
            quiz=quiz,
            class_shell=class_shell,
            total_marks=total_marks,
        )

        for question in questions:
            user_answer = request.POST.get(f'answer_{question.id}')
            is_correct = False

            if question.type == "multiple_choice":
                is_correct = user_answer == question.mcq_answer
            elif question.type == "true_false":
                is_correct = str(user_answer) == str(question.tf_answer)

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

    return render(request, 'attempt_quiz.html', {
        'quiz': quiz,
        'questions': questions,
        'score': None,
        'total_marks': total_marks,
        'class_shell': class_shell,
        'quiz_id': quiz_id,
    })

def attempt_exercise(request, class_shell_id, exercise_id):
    class_shell = get_object_or_404(ClassShell, id=class_shell_id)
    exercise = get_object_or_404(Exercise, id=exercise_id, class_shell=class_shell)
    exercise_questions = ExerciseQuestion.objects.filter(exercise=exercise)
    total_marks = sum(question.mark for question in exercise_questions)
    
    attempt = ExerciseAttempt.objects.filter(student=request.user, exercise=exercise).first()

    if attempt:
        if "view" in request.GET:
            question_attempts = ExerciseQuestionAttempt.objects.filter(exercise_attempt=attempt)
            context = {
                'exercise': exercise,
                'already_attempted': True,
                'view_submitted': True,
                'total_marks': total_marks,
                'score': attempt.score,
                'question_attempts': question_attempts,
                'class_shell': class_shell,
            }
            return render(request, 'attempt_exercise.html', context)

        context = {
            'exercise': exercise,
            'already_attempted': True,
            'view_submitted': False,
            'score': attempt.score,
            'total_marks': total_marks,
            'class_shell': class_shell,
        }
        return render(request, 'attempt_exercise.html', context)

    if request.method == "POST":
        score = 0
        exercise_attempt = ExerciseAttempt.objects.create(
            student=request.user,
            exercise=exercise,
            class_shell=class_shell,
            total_marks=total_marks,
        )

        for exercise_question in exercise_questions:
            user_answer = request.POST.get(f'answer_{exercise_question.id}')
            is_correct = False

            # Handling multiple choice questions
            if exercise_question.type == "multiple_choice":
                if user_answer:
                    is_correct = user_answer == exercise_question.mcq_answer

            # Handling true/false questions
            elif exercise_question.type == "true_false":
                if user_answer is not None:  
                    is_correct = (str(user_answer).strip().lower() == str(exercise_question.tf_answer).strip().lower())

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


    return render(request, 'attempt_exercise.html', {
        'exercise': exercise,
        'exercise_questions': exercise_questions,
        'score': None,
        'total_marks': total_marks,
        'class_shell': class_shell,
        'exercise_id': exercise_id,
    })
