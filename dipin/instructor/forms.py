from django import forms
from .models import ClassShell,CourseFile,Course

class ClassShellForm(forms.ModelForm):
    class Meta:
        model = ClassShell
        fields = ['semester', 'section_number','year', 'course_name']

class CourseFileForm(forms.ModelForm):
    class Meta:
        model = CourseFile
        fields = ['file']  

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['text','title']
    text = forms.CharField(widget=forms.Textarea(attrs={'cols': 80, 'rows': 10}))