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

# Base Question Form
class BaseQuestionForm(forms.ModelForm):
    text = forms.CharField(widget=forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}))

    tf_answer = forms.ChoiceField(
        choices=[('True', 'True'), ('False', 'False')],
        required=False
    )

    essay_answer = forms.CharField(
        label='Essay Answer',
        widget=forms.Textarea,
        required=False
    )

    class Meta:
        model = BaseQuestion
        fields = [
            'text', 'type', 'choice_1', 'choice_2', 'choice_3', 'choice_4',
            'mark', 'mcq_answers', 'tf_answer'
        ]

    def __init__(self, *args, **kwargs):
        super(BaseQuestionForm, self).__init__(*args, **kwargs)

        # Get choices from mcq_choices (JSONField), fallback to old 4 choices if not set
        choices = []
        if self.instance and self.instance.mcq_choices:
            choices = [(c, c) for c in self.instance.mcq_choices]
        else:
            # Fallback to existing fixed choices
            default_choices = [
                self.instance.choice_1,
                self.instance.choice_2,
                self.instance.choice_3,
                self.instance.choice_4,
            ]
            choices = [(c, c) for c in default_choices if c]

        self.fields['mcq_answers'] = forms.MultipleChoiceField(
            choices=choices,
            widget=forms.CheckboxSelectMultiple,
            required=False
        )



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