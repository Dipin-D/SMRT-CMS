from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from accounts.views import front_page
from django.shortcuts import redirect

def redirect_to_home(request, exception=None):
    return redirect('/')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',front_page, name='front_page'),
    path('accounts/', include('accounts.urls', namespace='accounts')),  
    path('instructor/', include('instructor.urls', namespace='instructor')),  
    path('student/', include('student.urls', namespace='student')),  
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
handler403 = redirect_to_home
handler404 = redirect_to_home