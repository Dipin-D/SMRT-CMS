from django.db import models
from django.conf import settings

class ClassShell(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
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
    text = models.CharField(max_length=255)
    answer = models.CharField(max_length=5)
    type = models.CharField(max_length=20)

    class Meta:
        abstract = True  
    def __str__(self):
        return self.text
class BaseAnswer(models.Model):
    text = models.CharField(max_length=200)
    is_correct = models.BooleanField(default=False)

    class Meta:
        abstract = True  
    def __str__(self):
        return self.text
    
class Quiz(models.Model):  
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='quizzes')
    class_shell = models.ForeignKey(ClassShell, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    grading_percentage = models.FloatField(default=10)

    def __str__(self):
        return self.title

class Question(BaseQuestion):  
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
class Answer(BaseAnswer):  
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')

class Exercise(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='exercises')
    class_shell = models.ForeignKey(ClassShell, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    grading_percentage = models.FloatField(default=10)


    def __str__(self):
        return self.title

class ExerciseQuestion(BaseQuestion):  
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
class ExerciseAnswer(BaseAnswer): 
    question = models.ForeignKey(ExerciseQuestion, on_delete=models.CASCADE, related_name='answers')