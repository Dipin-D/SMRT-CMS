from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg, Max
from django.db import models
from django.utils import timezone
from datetime import timedelta
import json
from urllib.parse import quote_plus

from pal.core.models import Student, Course
from .models import LearningPath, WeakTopic, RecommendedTopic, TopicResource
from .ml.adaptive_path_lstm import DjangoIntegratedPathGenerator
from .services import SmrtPalSyncService


def _fallback_resources(topic_name):
    query = quote_plus(f"Java {topic_name}")
    return [
        {
            'title': f"Google study search: {topic_name}",
            'description': f"Free Java notes, examples, and tutorials for {topic_name}.",
            'url': f"https://www.google.com/search?q={query}+java+tutorial",
            'resource_type': 'documentation',
            'difficulty': 'beginner',
            'estimated_time': 1.0,
        },
        {
            'title': f"YouTube lessons: {topic_name}",
            'description': f"Free video walkthroughs and examples for {topic_name}.",
            'url': f"https://www.youtube.com/results?search_query={query}",
            'resource_type': 'video',
            'difficulty': 'beginner',
            'estimated_time': 1.5,
        },
        {
            'title': f"GeeksforGeeks practice: {topic_name}",
            'description': f"Free explanations, examples, and practice links for {topic_name}.",
            'url': f"https://www.google.com/search?q=site%3Ageeksforgeeks.org+{query}",
            'resource_type': 'practice',
            'difficulty': 'intermediate',
            'estimated_time': 1.0,
        },
    ]


@login_required
def student_list(request):
    """
    Level 1: Display all students with learning paths in a beautiful table.
    """
    if getattr(request.user, 'is_student', False):
        return redirect('learning_paths:my_learning_path')

    active_path_filter = models.Q(learning_paths__status='active')

    # Get students who have learning paths
    students_with_paths = Student.objects.annotate(
        path_count=Count('learning_paths', filter=active_path_filter),
        latest_path_date=Max('learning_paths__generated_at', filter=active_path_filter)
    ).filter(path_count__gt=0).order_by('-latest_path_date')
    
    # Also get students without paths for completeness
    students_without_paths = Student.objects.annotate(
        path_count=Count('learning_paths', filter=active_path_filter)
    ).filter(path_count=0)
    
    context = {
        'students_with_paths': students_with_paths,
        'students_without_paths': students_without_paths,
        'total_students': Student.objects.count(),
        'total_paths': LearningPath.objects.filter(status='active').count(),
    }
    
    return render(request, 'learning_paths/student_list.html', context)


@login_required
def student_paths(request, student_id):
    """
    Level 2: Display all learning paths for a specific student.
    """
    student = get_object_or_404(Student, student_id=student_id)

    if getattr(request.user, 'is_student', False) and student.user_id != request.user.id:
        messages.info(request, "You can only view your own learning path.")
        return redirect('learning_paths:my_learning_path')

    if student.user_id == request.user.id:
        sync_service = SmrtPalSyncService()
        _, latest_path, generated = sync_service.get_or_create_learning_path(request.user)
        if generated and latest_path:
            messages.success(request, "Your learning path has been refreshed from your latest SMRT-CMS activity.")
        elif latest_path is None:
            messages.info(request, "No quiz or exercise data has been found for your account yet.")
    
    sync_service = SmrtPalSyncService()
    enrolled_courses = []
    if student.user_id:
        enrolled_courses = sync_service.get_user_courses(student.user)

    if enrolled_courses:
        learning_paths_qs = LearningPath.objects.filter(
            student=student,
            status='active',
            course__in=enrolled_courses,
        ).select_related('course').order_by('course__course_id', '-generated_at')
    else:
        learning_paths_qs = LearningPath.objects.filter(
            student=student,
            status='active',
        ).select_related('course').order_by('course__course_id', '-generated_at')

    latest_paths = []
    seen_course_ids = set()
    for path in learning_paths_qs:
        if path.course_id in seen_course_ids:
            continue
        seen_course_ids.add(path.course_id)
        latest_paths.append(path)

    courses_without_paths = [
        course for course in enrolled_courses if course.course_id not in seen_course_ids
    ]

    # Calculate some stats
    total_paths = len(latest_paths)
    total_time = sum(path.total_estimated_time for path in latest_paths)
    avg_weak_topics = (
        sum(path.weak_topics_count for path in latest_paths) / total_paths
        if total_paths else 0
    )

    context = {
        'student': student,
        'learning_paths': latest_paths,
        'courses_without_paths': courses_without_paths,
        'total_paths': total_paths,
        'total_time': total_time,
        'avg_weak_topics': round(avg_weak_topics, 1),
    }
    
    return render(request, 'learning_paths/student_paths.html', context)


@login_required
def path_detail(request, path_id):
    """
    Level 3: Display detailed learning path with amazing visualization.
    """
    learning_path = get_object_or_404(LearningPath, id=path_id)

    if getattr(request.user, 'is_student', False) and learning_path.student.user_id != request.user.id:
        messages.info(request, "You can only view your own learning path.")
        return redirect('learning_paths:my_learning_path')
    
    # Get related data
    weak_topics = list(WeakTopic.objects.filter(learning_path=learning_path).order_by('order'))
    recommended_topics = RecommendedTopic.objects.filter(learning_path=learning_path).order_by('priority')

    for weak_topic in weak_topics:
        weak_topic.mastery_percent = round((weak_topic.current_mastery or 0) * 100, 1)
    
    # Prepare data for visualization
    path_data = {
        'nodes': [],
        'edges': [],
        'student_profile': learning_path.student_stats,
        'path_stats': {
            'total_time': learning_path.total_estimated_time,
            'weak_topics_count': learning_path.weak_topics_count,
            'recommended_topics_count': learning_path.recommended_topics_count,
            'created_at': learning_path.generated_at.isoformat(),
            'status': 'Active' if learning_path.generated_at > timezone.now() - timedelta(days=7) else 'Old'
        }
    }
    
    # Build nodes for visualization
    node_id = 0
    
    # Add start node
    path_data['nodes'].append({
        'id': node_id,
        'label': 'START',
        'type': 'start',
        'color': '#28a745',
        'size': 30,
        'font': {'size': 16, 'color': 'white'}
    })
    start_node_id = node_id
    node_id += 1
    
    # Add recommended topic nodes
    prev_node_id = start_node_id
    topic_nodes = {}
    
    for rec_topic in recommended_topics[:8]:  # Limit to 8 for better visualization
        # Determine node color based on prerequisites
        if rec_topic.should_study_prerequisites_first:
            color = '#ffc107'  # Yellow for prerequisites needed
            status = 'Prerequisites Needed'
        else:
            color = '#007bff'  # Blue for ready to study
            status = 'Ready to Study'
        
        # Determine size based on confidence
        size = 20 + (rec_topic.confidence * 20)  # Size between 20-40
        
        path_data['nodes'].append({
            'id': node_id,
            'label': rec_topic.topic.name[:20] + ('...' if len(rec_topic.topic.name) > 20 else ''),
            'full_name': rec_topic.topic.name,
            'type': 'topic',
            'color': color,
            'size': size,
            'confidence': round(rec_topic.confidence * 100, 1),
            'time_hours': rec_topic.estimated_time_hours,
            'difficulty': rec_topic.recommended_difficulty,
            'status': status,
            'prerequisites': rec_topic.prerequisites,
            'unmet_prerequisites': rec_topic.unmet_prerequisites,
            'resources': [
                {
                    'title': res.title,
                    'url': res.url,
                    'type': res.resource_type,
                    'difficulty': res.difficulty,
                    'time': res.estimated_time
                }
                for res in TopicResource.objects.filter(recommended_topic=rec_topic).order_by('order')[:5]
            ],
            'font': {'size': 12, 'color': 'white'}
        })
        
        # Add edge from previous node
        path_data['edges'].append({
            'from': prev_node_id,
            'to': node_id,
            'arrows': 'to',
            'color': {'color': '#666666'},
            'width': 2
        })
        
        topic_nodes[rec_topic.topic.name] = node_id
        prev_node_id = node_id
        node_id += 1
    
    # Add finish node
    path_data['nodes'].append({
        'id': node_id,
        'label': 'FINISH',
        'type': 'finish',
        'color': '#dc3545',
        'size': 30,
        'font': {'size': 16, 'color': 'white'}
    })
    
    # Add edge to finish
    if prev_node_id != start_node_id:
        path_data['edges'].append({
            'from': prev_node_id,
            'to': node_id,
            'arrows': 'to',
            'color': {'color': '#666666'},
            'width': 2
        })
    
    context = {
        'learning_path': learning_path,
        'weak_topics': weak_topics,
        'recommended_topics': recommended_topics,
        'path_data_json': json.dumps(path_data),
        'student_profile': learning_path.student_stats,
    }
    
    return render(request, 'learning_paths/path_detail.html', context)


@login_required
def generate_new_path(request, student_id):
    """
    Generate a new learning path for a student.
    """
    student = get_object_or_404(Student, student_id=student_id)
    if getattr(request.user, 'is_student', False) and student.user_id != request.user.id:
        messages.error(request, "You can only generate your own learning path.")
        return redirect('learning_paths:my_learning_path')

    if request.method == 'POST':
        try:
            sync_service = SmrtPalSyncService()
            _, learning_path, _ = sync_service.get_or_create_learning_path(student.user)

            if learning_path:
                messages.success(request, f'New learning path generated for student {student_id}!')
                # Redirect to the student's paths page
                return redirect('learning_paths:student_paths', student_id=student_id)
            else:
                messages.error(request, 'Failed to generate learning path. Please try again.')
        except Exception as e:
            messages.error(request, f'Error generating learning path: {str(e)}')
    
    return redirect('learning_paths:student_paths', student_id=student_id)


@login_required
def my_learning_path(request):
    """Show the logged-in student's current learning path without requiring uploads."""
    if not getattr(request.user, 'is_student', False):
        return redirect('learning_paths:student_list')

    sync_service = SmrtPalSyncService()
    student = sync_service.ensure_pal_student(request.user)

    return redirect('learning_paths:student_paths', student_id=student.student_id)


# Keep existing views for backward compatibility
@login_required
def learning_path_dashboard(request):
    """Original dashboard view."""
    return redirect('learning_paths:student_list')


@login_required
def generate_learning_path(request, student_id):
    """Original generate view."""
    return generate_new_path(request, student_id)


@login_required
def topic_resources(request, topic_id):
    """Get resources for a specific recommended topic."""
    try:
        recommended_topic = get_object_or_404(RecommendedTopic, id=topic_id)
        resources = TopicResource.objects.filter(recommended_topic=recommended_topic).order_by('order')
        
        resources_data = []
        for resource in resources:
            resources_data.append({
                'title': resource.title,
                'description': resource.description,
                'url': resource.url,
                'resource_type': resource.resource_type,
                'difficulty': resource.difficulty,
                'estimated_time': resource.estimated_time,
            })

        if not resources_data:
            resources_data = _fallback_resources(recommended_topic.topic.name)
        
        return JsonResponse({
            'topic': recommended_topic.topic.name,
            'resources': resources_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error loading resources: {str(e)}'
        }, status=500)


@login_required
def test_integrated_models(request):
    """Test the integrated models."""
    try:
        path_generator = DjangoIntegratedPathGenerator()
        
        # Test with first student
        first_student = Student.objects.first()
        if first_student:
            test_path = path_generator.generate_comprehensive_learning_path(first_student.student_id)
            
            if test_path:
                return JsonResponse({
                    'status': 'success',
                    'message': 'Models are working correctly',
                    'test_student': first_student.student_id,
                    'path_topics': len(test_path.get('recommended_path', []))
                })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Failed to generate test path'
                })
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'No students found in database'
            })
            
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Error testing models: {str(e)}'
        })
