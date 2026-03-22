from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from accounts.views import front_page
from django.shortcuts import redirect
from django.contrib.auth.urls import views as auth_views
from django.http import HttpResponseNotFound, HttpResponseForbidden
from pal.core import views as core_views


def redirect_to_home(request, exception=None):
    if request.path.startswith('/admin') or request.path.startswith('/accounts/login'):
        if isinstance(exception, PermissionError):
            return HttpResponseForbidden("Permission denied.")
        return HttpResponseNotFound("Page not found.")
    return redirect('/')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',front_page, name='front_page'),
    path('accounts/', include('accounts.urls', namespace='accounts')),  
    path('instructor/', include('instructor.urls', namespace='instructor')),  
    path('student/', include('student.urls', namespace='student')), 
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'), 
 # PAL URLs
    path('pal/', core_views.home, name='home'), 
    path('pal/', include('pal.urls')),
    path('pal/api/', include('pal.api.urls')),
    path('pal/data-ingestion/', include('pal.data_ingestion.urls')),
    path('pal/topic-classification/', include('pal.topic_classification.urls', namespace='topic_classification')),
    path('pal/knowledge-graph/', include('pal.knowledge_graph.urls', namespace='knowledge_graph')),
    path('pal/ml-models/', include('pal.ml_models.urls', namespace='ml_models')),
    path('pal/learning-paths/', include('pal.learning_paths.urls', namespace='learning_paths')),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
handler403 = redirect_to_home
handler404 = redirect_to_home