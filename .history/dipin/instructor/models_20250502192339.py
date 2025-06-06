from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model


class ClassShell(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    students_with_access = models.ManyToManyField(get_user_model(), blank=True, related_name="accessible_classes")
    course_name = models.CharField(max_length=100)
    section_number = models.IntegerField()
    semester = models.CharField(max_length=50)
    year = models.IntegerField()

    def __str__(self):
        return f'{self.course_name} - {self.section_number} ({self.semester} {self.year})'   
    
# Base Model for Course and Assignment
class BaseContent(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    class_shell = models.ForeignKey(ClassShell, on_delete=models.CASCADE)
    text = models.TextField()
    title = models.CharField(max_length=200)

    class Meta:
        abstract = True  

    def __str__(self):
        return self.title

# Course Model
class Course(BaseContent):  
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='courses')

# Assignment Model
class Assignment(BaseContent):  
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='assignments')
    due_date = models.DateTimeField(null=True, blank=True)
    total_marks = models.IntegerField(default=5)
    max_attempts = models.IntegerField(default=3)



# Base FILE Model for CourseFile and AssignmentFile
class BaseFile(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    class_shell = models.ForeignKey(ClassShell, on_delete=models.CASCADE)
    file = models.FileField(upload_to='files/')

    class Meta:
        abstract = True  

    def __str__(self):
        return self.file.name

# CourseFile Model
class CourseFile(BaseFile):  
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='course_files')

# AssignmentFile Model
class AssignmentFile(BaseFile):  
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='assignment_files') 
    assignment_file = models.FileField(upload_to='assignment_files/')  
    def __str__(self):
        return self.assignment_file.name

class BaseQuestion(models.Model):
    text = models.TextField(null=True)
    type = models.CharField(max_length=255)
    answer = models.CharField(max_length=255)
    mark = models.IntegerField(default=5)

    # Fields for multiple-choice questions
    choice_1 = models.CharField(max_length=255, blank=True,null=True)
    choice_2 = models.CharField(max_length=255, blank=True,null=True)
    choice_3 = models.CharField(max_length=255, blank=True,null=True)
    choice_4 = models.CharField(max_length=255, blank=True,null=True)
    mcq_answers = models.JSONField(blank=True, null=True)
    # Field for true/false questions
    tf_answer = models.BooleanField(null=True, blank=True)

    class Meta:
        abstract = True  
    def __str__(self):
        return self.text
    
class Quiz(models.Model):  
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='quizzes')
    class_shell = models.ForeignKey(ClassShell, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    grading_percentage = models.FloatField(default=10)
    due_date = models.DateTimeField(null=True, blank=True)
    max_attempts = models.IntegerField(default=3)
    timer = models.PositiveIntegerField(default=30)

    def __str__(self):
        return self.title

class Question(BaseQuestion):  
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)

class Exercise(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='exercises')
    class_shell = models.ForeignKey(ClassShell, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    grading_percentage = models.FloatField(default=10)
    due_date = models.DateTimeField(null=True, blank=True)
    max_attempts = models.IntegerField(default=3)
    timer = models.PositiveIntegerField(default=30)

    def __str__(self):
        return self.title

class ExerciseQuestion(BaseQuestion):  
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)

class Attendance(models.Model):
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('excused', 'Excused'),
    ]

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    class_shell = models.ForeignKey('ClassShell', on_delete=models.CASCADE)
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)  

    class Meta:
        unique_together = ('student', 'class_shell', 'date')

    def __str__(self):
        return f"{self.student} - {self.date} - {self.status}"



