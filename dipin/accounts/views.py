from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login
from django.contrib.auth.forms import AuthenticationForm
from .forms import UserRegistrationForm
from django.contrib.auth.decorators import login_required

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)  # Create instance but don't save yet
            user.set_password(form.cleaned_data['password1'])
            
            # Assign roles based on email domain
            if user.email.endswith('@bulldogs.aamu.edu'):
                user.is_student = True
            elif user.email.endswith('@aamu.edu'):
                user.is_instructor = True

            user.save()
            auth_login(request, user)
            return redirect_based_on_role(user)  # Pass the user object here
    else:
        form = UserRegistrationForm()

    return render(request, 'registration/register.html', {'form': form})

def front_page(request):
    if request.method == 'POST':  # What happens after hitting submit?
        form = AuthenticationForm(request.POST)
        if form.is_valid():  # Does userid, password match?
            user = form.get_user()
            auth_login(request, user)
            return redirect_based_on_role(user)  # Pass the user object here
    else:  # Handles both GET and other request methods
        form = AuthenticationForm()  # Initialize the form for GET requests and any other requests

    return render(request, 'registration/login.html', {'form': form})
    

def redirect_based_on_role(user):
    if user.is_student:
        return redirect('student:course_list')
    elif user.is_instructor:
        return redirect('instructor:class_shell_list')
    else:
        return redirect('home')  


@login_required
def profile(request):
     return redirect_based_on_role(request.user)