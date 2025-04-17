from django.db import models
from instructor.models import Quiz, Question, ClassShell, Assignment, Exercise, ExerciseQuestion
from accounts.models import CustomUser

class AssignmentSubmission(models.Model):
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="assignment_submissions")
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="submissions")
    submission_text = models.TextField()
    submission_file = models.FileField(upload_to='assignments/', null=True, blank=True)
    submitted_on = models.DateTimeField(auto_now_add=True)
    graded = models.BooleanField(default=False)
    grade = models.FloatField(null=True, blank=True)
    attempt_number = models.IntegerField(default=1)
  
    def __str__(self):
        return f"Submission by {self.student} for {self.assignment}"

class QuizAttempt(models.Model):
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="quiz_attempts")
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="attempts")
    class_shell = models.ForeignKey(ClassShell, on_delete=models.CASCADE, related_name="quiz_attempts")
    score = models.FloatField(default=0)
    total_marks = models.FloatField(null=True, blank=True)
    attempted_on = models.DateTimeField(auto_now_add=True)
    graded = models.BooleanField(default=False)
    grade = models.FloatField(null=True, blank=True)
    attempt_number = models.IntegerField(default=1)
    end_time = models.DateTimeField(null=True, blank=True)
    submitted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.student} - {self.quiz} - {self.score}/{self.total_marks}"

class QuestionAttempt(models.Model):
    quiz_attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name="question_attempts")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="attempts")
    student_answer = models.TextField()
    is_correct = models.BooleanField()

    def __str__(self):
        return f"Question {self.question.id} in Quiz Attempt {self.quiz_attempt.id} - {'Correct' if self.is_correct else 'Incorrect'}"


class ExerciseAttempt(models.Model):
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="exercise_attempts")
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name="attempts")
    class_shell = models.ForeignKey(ClassShell, on_delete=models.CASCADE, related_name="exercise_attempts")
    score = models.FloatField(default=0)
    total_marks = models.FloatField(null=True, blank=True)
    attempted_on = models.DateTimeField(auto_now_add=True)
    graded = models.BooleanField(default=False)
    grade = models.FloatField(null=True, blank=True)
    attempt_number = models.IntegerField(default=1)
    end_time = models.DateTimeField(null=True, blank=True)
    submitted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.student} - {self.exercise} - {self.score}/{self.total_marks}"


class ExerciseQuestionAttempt(models.Model):
    exercise_attempt = models.ForeignKey(ExerciseAttempt, on_delete=models.CASCADE, related_name="question_attempts")
    exercise_question = models.ForeignKey(ExerciseQuestion, on_delete=models.CASCADE, related_name="attempts")
    student_answer = models.TextField()
    is_correct = models.BooleanField()

    def __str__(self):
        return f"Question {self.exercise_question.id} in Exercise Attempt {self.exercise_attempt.id} - {'Correct' if self.is_correct else 'Incorrect'}"