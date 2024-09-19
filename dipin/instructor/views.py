from django.shortcuts import render, redirect, get_object_or_404
from .forms import ClassShellForm, CourseFileForm, CourseForm
from .models import ClassShell, CourseFile, Course

def create_class_shell(request):
    if request.method == 'POST':  # After hitting that submit button
        form = ClassShellForm(request.POST)
        if form.is_valid():
            class_shell = form.save(commit=False)  # Create instance but don't save yet
            class_shell.user = request.user  # Set the user
            class_shell.save()  # Save the instance with the user set
            return redirect('instructor:class_shell_list')
    else:
        form = ClassShellForm()
    return render(request, 'create_class_shell.html', {'form': form})

def class_shell_list(request):
    class_shells = ClassShell.objects.filter(user=request.user)
    return render(request, 'class_shell_list.html', {'class_shells': class_shells})


def go_to_course(request, class_shell_id):
    # Retrieve the specific ClassShell instance
    class_shell = get_object_or_404(ClassShell, id=class_shell_id)

    # Retrieve related courses and files
    courses = Course.objects.filter(class_shell=class_shell)
    files = CourseFile.objects.filter(class_shell=class_shell)

    if request.method == 'POST':
        # Initialize forms with POST data
        course_form = CourseForm(request.POST)
        file_form = CourseFileForm(request.POST, request.FILES)
        
        course_id = request.POST.get('course_id')

        if 'edit_course' in request.POST and course_id:
            # Editing existing course
            course = get_object_or_404(Course, id=course_id)
            course_form = CourseForm(request.POST, instance=course)
            if course_form.is_valid():
                course_instance = course_form.save(commit=False)
                course_instance.user = request.user
                course_instance.class_shell = class_shell
                course_instance.save()
        elif 'add_course' in request.POST:
            # Adding new course
            if course_form.is_valid():
                course_instance = course_form.save(commit=False)
                course_instance.user = request.user
                course_instance.class_shell = class_shell
                course_instance.save()

        # Handle file upload if provided
        if file_form.is_valid():
            course_file = file_form.save(commit=False)
            course_file.user = request.user
            course_file.class_shell = class_shell
            course_file.save()

        return redirect('instructor:go_to_course', class_shell_id=class_shell_id)

    else:
        # Initialize empty forms for GET requests
        course_form = CourseForm()
        file_form = CourseFileForm()

    # Render the template with context
    return render(request, 'go_to_course.html', {
        'course_form': course_form,
        'file_form': file_form,
        'class_shell': class_shell,
        'courses': courses,
        'files': files
    })
