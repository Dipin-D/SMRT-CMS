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
    
    
class Course(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='courses')
    class_shell = models.ForeignKey(ClassShell, on_delete=models.CASCADE)
    text = models.TextField()
    title = models.CharField(max_length=200)

    def __str__(self):
        return self.title 

class CourseFile(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='course_files')
    class_shell = models.ForeignKey(ClassShell, on_delete=models.CASCADE)
    file = models.FileField(upload_to='course_files/')

    def __str__(self):
        return self.file.name

class Quiz(models.Model):  
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='quizzes')
    class_shell = models.ForeignKey(ClassShell, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    grading_percentage = models.FloatField(default=0)

    def __str__(self):
        return self.title

class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    text = models.CharField(max_length=255)
    answer = models.CharField(max_length=5)  
    type = models.CharField(max_length=20)  

    def __str__(self):
        return self.text

class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    text = models.CharField(max_length=200)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text

class Assignment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='assignments')
    class_shell = models.ForeignKey(ClassShell, on_delete=models.CASCADE)
    text = models.TextField()
    title = models.CharField(max_length=200)
    def __str__(self):
        return self.title 
