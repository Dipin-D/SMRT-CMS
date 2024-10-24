from django import forms
from .models import ClassShell, CourseFile, Course, Question, Quiz, Answer, Exercise, Assignment, AssignmentFile, BaseQuestion, ExerciseQuestion  

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
        fields = ['text', 'title']
    text = forms.CharField(widget=forms.Textarea(attrs={'cols': 40, 'rows': 10}))

class AssignmentFileForm(forms.ModelForm):
    class Meta:
        model = AssignmentFile
        fields = ['assignment_file']

# Quiz Form
class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ['title', 'grading_percentage']

# Exercise Form
class ExerciseForm(forms.ModelForm):  # Corrected spelling here
    class Meta:
        model = Exercise
        fields = ['title', 'grading_percentage']

# Base Question Form
class BaseQuestionForm(forms.ModelForm):
    class Meta:
        model = BaseQuestion
        fields = ['text', 'type']

    answer_1 = forms.CharField(label='Answer 1', max_length=200, required=False)
    answer_2 = forms.CharField(label='Answer 2', max_length=200, required=False)
    answer_3 = forms.CharField(label='Answer 3', max_length=200, required=False)
    answer_4 = forms.CharField(label='Answer 4', max_length=200, required=False)

    correct_answer = forms.ChoiceField(
        label='Correct Answer',
        choices=[
            ('1', 'Answer 1'),
            ('2', 'Answer 2'),
            ('3', 'Answer 3'),
            ('4', 'Answer 4'),
        ],
        required=False
    )
    
    true_false_answer = forms.ChoiceField(
        label='Correct Answer',
        choices=[
            ('true', 'True'),
            ('false', 'False'),
        ],
        required=False
    )

    essay_answer = forms.CharField(label='Essay Answer', widget=forms.Textarea, required=False)

class QuestionForm(BaseQuestionForm):
    class Meta(BaseQuestionForm.Meta):
        model = Question  

class ExerciseQuestionForm(BaseQuestionForm):
    class Meta(BaseQuestionForm.Meta):
        model = ExerciseQuestion  
