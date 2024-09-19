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
    
class CourseFile(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='course_files')  # ForeignKey allows multiple files
    class_shell = models.ForeignKey(ClassShell, on_delete=models.CASCADE)
    file = models.FileField(upload_to='course_files/')

    def __str__(self):
        return self.file.name
    
class Course(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='courses')  # ForeignKey allows multiple courses
    class_shell = models.ForeignKey(ClassShell, on_delete=models.CASCADE)
    text = models.TextField()
    title = models.CharField(max_length=200)

    def __str__(self):
        return self.title 
