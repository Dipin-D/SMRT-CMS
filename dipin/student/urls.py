from django.urls import path
from django.urls import path
from . import views

app_name = 'student'

urlpatterns = [
    path('', views.demo, name='demo'),

]


