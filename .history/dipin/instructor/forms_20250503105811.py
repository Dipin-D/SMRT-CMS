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
    
    # Dynamic choices field
    choices = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        help_text="Enter each choice on a new line (for multiple choice questions)"
    )
    
    # Will be populated with checkboxes in __init__
    mcq_answers = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple,
        choices=[]  # Will be populated dynamically
    )
    
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
        fields = ['text', 'type', 'mark', 'choices', 'mcq_answers', 'tf_answer']

    def __init__(self, *args, **kwargs):
        super(BaseQuestionForm, self).__init__(*args, **kwargs)
        
        # Initialize choices textarea from mcq_choices
        if self.instance and self.instance.mcq_choices:
            self.fields['choices'].initial = "\n".join(self.instance.mcq_choices)
            
        # Set up mcq_answers choices and initial values
        choices = []
        if self.instance and self.instance.mcq_choices:
            choices = [(c, c) for c in self.instance.mcq_choices]
            
            # Set initial values for mcq_answers if they exist
            if self.instance.mcq_answers:
                self.fields['mcq_answers'].initial = self.instance.mcq_answers
        
        self.fields['mcq_answers'].choices = choices

    def clean(self):
        cleaned_data = super().clean()
        
        # Process choices from textarea
        choices_text = cleaned_data.get('choices', '')
        mcq_choices = [c.strip() for c in choices_text.split('\n') if c.strip()]
        cleaned_data['mcq_choices'] = mcq_choices
        
        # Convert mcq_answers to JSON-serializable format
        if 'mcq_answers' in cleaned_data:
            cleaned_data['mcq_answers'] = list(cleaned_data['mcq_answers'])
        
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.mcq_choices = self.cleaned_data.get('mcq_choices', [])
        
        # Handle mcq_answers - store as list in JSONField
        if 'mcq_answers' in self.cleaned_data:
            instance.mcq_answers = self.cleaned_data['mcq_answers']
        else:
            instance.mcq_answers = None
            
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