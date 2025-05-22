from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login
from django.contrib.auth.forms import AuthenticationForm
from .forms import UserRegistrationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth import get_user_model

User = get_user_model()

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email'].lower()

            # Check if email already exists
            if User.objects.filter(email=email).exists():
                messages.error(request, "An account with this email already exists.")
                return render(request, 'registration/register.html', {'form': form})

            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password1'])

            # Assign roles
            if email.endswith('@bulldogs.aamu.edu'):
                user.is_student = True
            elif email.endswith('@aamu.edu'):
                user.is_instructor = True

            user.email = email  
            user.save()
            auth_login(request, user)
            return redirect_based_on_role(user)
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

def guest_login(request):

    user = authenticate(username='guest', password='dipin123')

    if user is not None:
        login(request, user)
        return redirect('student:course_list')
    

def redirect_based_on_role(user):
    if user.is_student:
        return redirect('student:course_list')
    elif user.is_instructor:
        return redirect('instructor:class_shell_list')
    else:
        return redirect('front_page')  


@login_required
def profile(request):
     return redirect_based_on_role(request.user)

