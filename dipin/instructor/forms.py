from django import forms
from .models import ClassShell, CourseFile, Course, Question, Quiz, Exercise, Assignment, AssignmentFile, BaseQuestion, ExerciseQuestion  

class ClassShellForm(forms.ModelForm):
    class Meta:
        model = ClassShell
        fields = ['semester', 'section_number', 'year', 'course_name']

class CourseFileForm(forms.ModelForm):
    class Meta:
        model = CourseFile
        fields = ['file']  

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['text', 'title']
    text = forms.CharField(widget=forms.Textarea(attrs={'cols': 80, 'rows': 10}))

class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ['text', 'title', 'due_date','total_marks', 'max_attempts']
    text = forms.CharField(widget=forms.Textarea(attrs={'cols': 40, 'rows': 10}))

class AssignmentFileForm(forms.ModelForm):
    class Meta:
        model = AssignmentFile
        fields = ['assignment_file']

# Quiz Form
class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ['title', 'grading_percentage', 'due_date', 'max_attempts', 'timer']

# Exercise Form
class ExerciseForm(forms.ModelForm):  # Corrected spelling here
    class Meta:
        model = Exercise
        fields = ['title', 'grading_percentage', 'due_date', 'max_attempts', 'timer']

# Base Question Form
class BaseQuestionForm(forms.ModelForm):
    class Meta:
        model = BaseQuestion
        fields = ['text', 'type', 'choice_1', 'choice_2', 'choice_3', 'choice_4','mark','mcq_answer','tf_answer']
    mcq_answer = forms.ChoiceField(choices=[
        ('Choice 1', 'Choice 1'),
        ('Choice 2', 'Choice 2'),
        ('Choice 3', 'Choice 3'),
        ('Choice 4', 'Choice 4'),
    ], required=False)   
    tf_answer = forms.ChoiceField(choices=[
        ('True', 'True'),  
        ('False', 'False'),  
    ], required=False)  
    essay_answer = forms.CharField(label='Essay Answer', widget=forms.Textarea, required=False)

class QuestionForm(BaseQuestionForm):
    class Meta(BaseQuestionForm.Meta):
        model = Question  

class ExerciseQuestionForm(BaseQuestionForm):
    class Meta(BaseQuestionForm.Meta):
        model = ExerciseQuestion  
