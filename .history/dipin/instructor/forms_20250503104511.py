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
    
    # Simulated fields to match old template/views
    choice_1 = forms.CharField(required=False)
    choice_2 = forms.CharField(required=False)
    choice_3 = forms.CharField(required=False)
    choice_4 = forms.CharField(required=False)

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
            'text', 'type', 'mark',
            'choice_1', 'choice_2', 'choice_3', 'choice_4',  # Not real model fields, handled manually
            'mcq_answers', 'tf_answer'
        ]

    def __init__(self, *args, **kwargs):
        super(BaseQuestionForm, self).__init__(*args, **kwargs)

        # Pre-fill choices from mcq_choices (JSONField)
        choices = []
        if self.instance and self.instance.mcq_choices:
            for idx, val in enumerate(self.instance.mcq_choices):
                self.fields[f'choice_{idx + 1}'].initial = val
            choices = [(c, c) for c in self.instance.mcq_choices]
        else:
            # fallback to empty form
            for i in range(1, 5):
                self.fields[f'choice_{i}'].initial = ''

        self.fields['mcq_answers'] = forms.MultipleChoiceField(
            choices=choices,
            widget=forms.CheckboxSelectMultiple,
            required=False
        )

    def clean(self):
        cleaned_data = super().clean()
        # Update mcq_choices from choice_1-4 if provided
        mcq_choices = []
        for i in range(1, 5):
            val = cleaned_data.get(f'choice_{i}')
            if val:
                mcq_choices.append(val)
        cleaned_data['mcq_choices'] = mcq_choices
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.mcq_choices = self.cleaned_data.get('mcq_choices', [])
        if commit:
            instance.save()
        return instance



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