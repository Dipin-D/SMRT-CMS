from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views
from django.contrib.auth.urls import views as auth_views


app_name = 'accounts' 
urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('profile/', views.profile, name='profile'),    
    path("guest-login/", views.guest_login, name="guest_login"),


] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

