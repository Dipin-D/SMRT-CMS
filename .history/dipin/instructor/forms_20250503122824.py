from django import forms
from .models import ClassShell, CourseFile, Course, Question, Quiz, Exercise, Assignment, AssignmentFile, BaseQuestion, ExerciseQuestion,Attendance  

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

class BaseQuestionForm(forms.ModelForm):
    text = forms.CharField(widget=forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}))
    type = forms.ChoiceField(choices=[
        ('multiple_choice', 'Multiple Choice'),
        ('true_false', 'True/False'),
        ('essay', 'Essay'),
    ], widget=forms.Select(attrs={'class': 'form-select'}))
    mark = forms.IntegerField(min_value=1, initial=5)

    choices = forms.CharField(required=False, widget=forms.Textarea(
        attrs={'rows': 3, 'class': 'form-control'}))

    mcq_answers = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple,
        choices=[]
    )

    tf_answer = forms.ChoiceField(
        choices=[('True', 'True'), ('False', 'False')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    essay_answer = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Question  # Or BaseQuestion if you're using abstract inheritance
        fields = ['text', 'type', 'mark', 'choices', 'mcq_answers', 'tf_answer']

    
class QuestionForm(BaseQuestionForm):
    class Meta(BaseQuestionForm.Meta):
        model = Question  

class ExerciseQuestionForm(BaseQuestionForm):
    class Meta(BaseQuestionForm.Meta):
        model = ExerciseQuestion  
class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['student', 'class_shell', 'date', 'status']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }