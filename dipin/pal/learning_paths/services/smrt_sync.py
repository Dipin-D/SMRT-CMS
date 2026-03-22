import datetime
import logging
import re
from typing import Dict, Optional, Tuple

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from instructor.models import ClassShell, Exercise, ExerciseQuestion, Question as SmrtQuestion, Quiz
from pal.core.models import Assessment, Course, Question, Student, StudentInteraction, Topic
from pal.learning_paths.ml.adaptive_path_lstm import DjangoIntegratedPathGenerator
from pal.learning_paths.models import LearningPath, RecommendedTopic, TopicResource, WeakTopic
from student.models import ExerciseAttempt, QuizAttempt

logger = logging.getLogger(__name__)


class SmrtPalSyncService:
    """Sync SMRT-CMS assessment activity into PAL and maintain saved learning paths."""

    DEFAULT_TIME_PER_QUESTION = datetime.timedelta(minutes=1)
    SIMPLE_TOPIC_PATTERNS = [
        ('process schedul', 'Process Scheduling'),
        ('memory', 'Memory Management'),
        ('file system', 'File Systems'),
        ('file ', 'File Handling'),
        ('operating system', 'Operating System Basics'),
        ('jdbc', 'Database Connectivity'),
        ('database', 'Database Connectivity'),
        ('spring boot', 'Spring Boot'),
        ('spring framework', 'Spring Framework'),
        ('microservice', 'Microservices'),
        ('rest api', 'REST APIs'),
        ('serialization', 'Serialization'),
        ('stream', 'File Streams'),
        ('file i/o', 'File I/O'),
        ('junit', 'Unit Testing'),
        ('mockito', 'Mocking with Mockito'),
        ('test', 'Unit Testing'),
        ('class', 'Classes and Objects'),
        ('object', 'Classes and Objects'),
        ('variable', 'Variables'),
        ('data type', 'Data Types'),
        ('print', 'Comments and Print Statements'),
        ('comment', 'Comments and Print Statements'),
        ('conditional', 'Conditional Statements'),
    ]

    def ensure_pal_student(self, user) -> Student:
        student = Student.objects.filter(user=user).first()
        if student:
            updates = []
            if student.last_login_date != user.last_login:
                student.last_login_date = user.last_login
                updates.append('last_login_date')
            if updates:
                student.save(update_fields=updates)
            return student

        student_id = (user.username or f"student-{user.pk}")[:50]
        student, created = Student.objects.get_or_create(
            student_id=student_id,
            defaults={
                'user': user,
                'major': 'Undeclared',
                'academic_level': 'freshman',
                'gpa': 0.0,
                'prior_knowledge_score': None,
                'study_frequency': 'weekly',
                'attendance_rate': 0.0,
                'participation_score': 0.0,
                'last_login_date': user.last_login,
            },
        )
        if not created and student.user_id != user.id:
            student.user = user
            student.last_login_date = user.last_login
            student.save(update_fields=['user', 'last_login_date'])
        return student

    def sync_user_activity(self, user) -> Dict[str, object]:
        student = self.ensure_pal_student(user)
        synced_interactions = 0
        latest_timestamp = None
        primary_course = None
        primary_course_ts = None

        quiz_attempts = QuizAttempt.objects.filter(
            student=user,
            question_attempts__isnull=False,
        ).select_related('quiz', 'quiz__class_shell').prefetch_related('question_attempts__question').distinct()

        for quiz_attempt in quiz_attempts:
            count, timestamp, course = self._sync_quiz_attempt(student, quiz_attempt)
            synced_interactions += count
            if timestamp and (latest_timestamp is None or timestamp > latest_timestamp):
                latest_timestamp = timestamp
            if timestamp and (primary_course_ts is None or timestamp > primary_course_ts):
                primary_course_ts = timestamp
                primary_course = course

        exercise_attempts = ExerciseAttempt.objects.filter(
            student=user,
            question_attempts__isnull=False,
        ).select_related('exercise', 'exercise__class_shell').prefetch_related('question_attempts__exercise_question').distinct()

        for exercise_attempt in exercise_attempts:
            count, timestamp, course = self._sync_exercise_attempt(student, exercise_attempt)
            synced_interactions += count
            if timestamp and (latest_timestamp is None or timestamp > latest_timestamp):
                latest_timestamp = timestamp
            if timestamp and (primary_course_ts is None or timestamp > primary_course_ts):
                primary_course_ts = timestamp
                primary_course = course

        if primary_course is None:
            primary_course = student.courses.order_by('course_id').first()

        return {
            'student': student,
            'synced_interactions': synced_interactions,
            'latest_timestamp': latest_timestamp,
            'primary_course': primary_course,
        }

    def get_user_courses(self, user):
        courses = []
        seen = set()
        class_shells = list(user.accessible_classes.all().order_by('course_name', 'section_number', 'year'))

        for class_shell in class_shells:
            course = self._resolve_course(class_shell)
            key = course.course_id or course.title
            if key and key not in seen:
                seen.add(key)
                courses.append(course)

        if class_shells:
            return courses

        student = self.ensure_pal_student(user)
        for course in student.courses.order_by('course_id'):
            key = course.course_id or course.title
            if key and key not in seen:
                seen.add(key)
                courses.append(course)

        return courses

    def get_or_create_learning_path(self, user) -> Tuple[Student, Optional[LearningPath], bool]:
        sync_result = self.sync_user_activity(user)
        student = sync_result['student']
        course = sync_result['primary_course']
        latest_timestamp = sync_result['latest_timestamp']

        if course is None:
            return student, None, False
        if not StudentInteraction.objects.filter(student=student).exists():
            return student, None, False

        latest_path = LearningPath.objects.filter(
            student=student,
            course=course,
        ).order_by('-generated_at').first()

        should_regenerate = latest_path is None
        if latest_path and not latest_path.student_stats.get('performance_based'):
            should_regenerate = True
        if latest_path and latest_path.student_stats.get('path_version') != 2:
            should_regenerate = True
        if (
            latest_path
            and latest_path.student_stats.get('attempted_topics', 0) == 0
            and StudentInteraction.objects.filter(student=student, question__topic__isnull=False).exists()
        ):
            should_regenerate = True
        if latest_path and latest_timestamp:
            should_regenerate = latest_path.generated_at < latest_timestamp
            if not latest_path.student_stats.get('performance_based'):
                should_regenerate = True
            if latest_path.student_stats.get('path_version') != 2:
                should_regenerate = True
            if (
                latest_path.student_stats.get('attempted_topics', 0) == 0
                and StudentInteraction.objects.filter(student=student, question__topic__isnull=False).exists()
            ):
                should_regenerate = True

        if not should_regenerate:
            return student, latest_path, False

        path_data = DjangoIntegratedPathGenerator().generate_comprehensive_learning_path(student.student_id)
        if not path_data:
            return student, latest_path, False

        learning_path = self._save_learning_path(student, course, path_data)
        return student, learning_path, True

    def _sync_quiz_attempt(self, student: Student, quiz_attempt: QuizAttempt):
        quiz = quiz_attempt.quiz
        course = self._resolve_course(quiz.class_shell)
        course.students.add(student)
        assessment = self._resolve_quiz_assessment(quiz, course)
        questions = list(quiz_attempt.question_attempts.all())
        per_question_time = self._get_per_question_time(
            quiz_attempt.attempted_on,
            quiz_attempt.end_time,
            len(questions),
        )
        count = 0

        for question_attempt in questions:
            question = self._resolve_quiz_question(question_attempt.question, assessment)
            _, created = StudentInteraction.objects.update_or_create(
                student=student,
                question=question,
                attempt_number=quiz_attempt.attempt_number,
                defaults={
                    'response': question_attempt.student_answer or '',
                    'correct': question_attempt.is_correct,
                    'score': float(question_attempt.question.mark) if question_attempt.is_correct else 0.0,
                    'time_taken': per_question_time,
                    'timestamp': quiz_attempt.end_time or quiz_attempt.attempted_on or timezone.now(),
                    'resource_viewed_before': False,
                },
            )
            if created:
                count += 1
            else:
                count += 1

        return count, (quiz_attempt.end_time or quiz_attempt.attempted_on), course

    def _sync_exercise_attempt(self, student: Student, exercise_attempt: ExerciseAttempt):
        exercise = exercise_attempt.exercise
        course = self._resolve_course(exercise.class_shell)
        course.students.add(student)
        assessment = self._resolve_exercise_assessment(exercise, course)
        questions = list(exercise_attempt.question_attempts.all())
        per_question_time = self._get_per_question_time(
            exercise_attempt.attempted_on,
            exercise_attempt.end_time,
            len(questions),
        )
        count = 0

        for question_attempt in questions:
            question = self._resolve_exercise_question(question_attempt.exercise_question, assessment)
            _, created = StudentInteraction.objects.update_or_create(
                student=student,
                question=question,
                attempt_number=exercise_attempt.attempt_number,
                defaults={
                    'response': question_attempt.student_answer or '',
                    'correct': question_attempt.is_correct,
                    'score': float(question_attempt.exercise_question.mark) if question_attempt.is_correct else 0.0,
                    'time_taken': per_question_time,
                    'timestamp': exercise_attempt.end_time or exercise_attempt.attempted_on or timezone.now(),
                    'resource_viewed_before': False,
                },
            )
            if created:
                count += 1
            else:
                count += 1

        return count, (exercise_attempt.end_time or exercise_attempt.attempted_on), course

    def _resolve_course(self, class_shell: ClassShell) -> Course:
        course_name = (class_shell.course_name or '').strip()
        course_code = self._extract_course_code(course_name)

        course = None
        if course_code:
            course = Course.objects.filter(course_id__iexact=course_code).first()

        if course is None:
            normalized_name = re.sub(r'[^A-Za-z0-9]+', ' ', course_name).strip()
            course = Course.objects.filter(title__icontains=normalized_name).first() if normalized_name else None

        if course is None and course_code:
            compact_code = re.sub(r'[^A-Za-z0-9]+', '', course_code).upper()
            course = Course.objects.filter(course_id__iexact=compact_code).first()

        if course is None:
            course = Course.objects.filter(course_id__iexact=course_name).first()
        if course is None:
            course = Course.objects.filter(title__iexact=course_name).first()
        if course is None:
            course_id = self._build_course_id(class_shell)
            course, _ = Course.objects.get_or_create(
                course_id=course_id,
                defaults={
                    'title': course_name or str(class_shell),
                    'description': f"Imported from SMRT-CMS section {class_shell.section_number} ({class_shell.semester} {class_shell.year})",
                },
            )
        else:
            updates = []
            if course_name and not (course.title or '').strip():
                course.title = course_name
                updates.append('title')
            if course_name and not (course.description or '').strip():
                course.description = (
                    f"Imported from SMRT-CMS section {class_shell.section_number} "
                    f"({class_shell.semester} {class_shell.year})"
                )
                updates.append('description')
            if updates:
                course.save(update_fields=updates)
        return course

    def _resolve_quiz_assessment(self, quiz: Quiz, course: Course) -> Assessment:
        assessment_id = f"smrt-quiz-{quiz.pk}"
        assessment, _ = Assessment.objects.get_or_create(
            assessment_id=assessment_id,
            defaults={
                'title': quiz.title,
                'assessment_type': 'quiz',
                'course': course,
                'date': quiz.due_date or timezone.now(),
                'proctored': False,
            },
        )
        if assessment.course_id != course.course_id or assessment.title != quiz.title:
            assessment.course = course
            assessment.title = quiz.title
            assessment.date = quiz.due_date or assessment.date or timezone.now()
            assessment.save(update_fields=['course', 'title', 'date'])
        return assessment

    def _resolve_exercise_assessment(self, exercise: Exercise, course: Course) -> Assessment:
        assessment_id = f"smrt-exercise-{exercise.pk}"
        assessment, _ = Assessment.objects.get_or_create(
            assessment_id=assessment_id,
            defaults={
                'title': exercise.title,
                'assessment_type': 'assignment',
                'course': course,
                'date': exercise.due_date or timezone.now(),
                'proctored': False,
            },
        )
        if assessment.course_id != course.course_id or assessment.title != exercise.title:
            assessment.course = course
            assessment.title = exercise.title
            assessment.date = exercise.due_date or assessment.date or timezone.now()
            assessment.save(update_fields=['course', 'title', 'date'])
        return assessment

    def _resolve_quiz_question(self, smrt_question: SmrtQuestion, assessment: Assessment) -> Question:
        question_id = f"smrt-quiz-question-{smrt_question.pk}"
        topic = self._infer_topic(assessment.course, smrt_question.text, assessment.title)
        question, created = Question.objects.get_or_create(
            question_id=question_id,
            defaults={
                'assessment': assessment,
                'text': smrt_question.text or '',
                'question_type': self._map_question_type(smrt_question.type),
                'topic': topic,
            },
        )
        if not created:
            updates = []
            if question.assessment_id != assessment.assessment_id:
                question.assessment = assessment
                updates.append('assessment')
            if question.text != (smrt_question.text or ''):
                question.text = smrt_question.text or ''
                updates.append('text')
            mapped_type = self._map_question_type(smrt_question.type)
            if question.question_type != mapped_type:
                question.question_type = mapped_type
                updates.append('question_type')
            if question.topic is None and topic is not None:
                question.topic = topic
                updates.append('topic')
            if updates:
                question.save(update_fields=updates)
        return question

    def _resolve_exercise_question(self, smrt_question: ExerciseQuestion, assessment: Assessment) -> Question:
        question_id = f"smrt-exercise-question-{smrt_question.pk}"
        topic = self._infer_topic(assessment.course, smrt_question.text, assessment.title)
        question, created = Question.objects.get_or_create(
            question_id=question_id,
            defaults={
                'assessment': assessment,
                'text': smrt_question.text or '',
                'question_type': self._map_question_type(smrt_question.type),
                'topic': topic,
            },
        )
        if not created:
            updates = []
            if question.assessment_id != assessment.assessment_id:
                question.assessment = assessment
                updates.append('assessment')
            if question.text != (smrt_question.text or ''):
                question.text = smrt_question.text or ''
                updates.append('text')
            mapped_type = self._map_question_type(smrt_question.type)
            if question.question_type != mapped_type:
                question.question_type = mapped_type
                updates.append('question_type')
            if question.topic is None and topic is not None:
                question.topic = topic
                updates.append('topic')
            if updates:
                question.save(update_fields=updates)
        return question

    def _infer_topic(self, course: Course, question_text: Optional[str], assessment_title: Optional[str]) -> Optional[Topic]:
        existing_question = Question.objects.filter(
            assessment__course=course,
            topic__isnull=False,
            text__iexact=(question_text or '').strip(),
        ).select_related('topic').first()
        if existing_question:
            return existing_question.topic

        existing_question = Question.objects.filter(
            topic__isnull=False,
            text__iexact=(question_text or '').strip(),
        ).select_related('topic').first()
        if existing_question:
            return existing_question.topic

        text = f"{assessment_title or ''} {question_text or ''}".lower()
        if not text.strip():
            return None

        topics = Topic.objects.filter(Q(course=course) | Q(course__course_id__iexact=course.course_id)).distinct()
        best_topic = None
        best_score = 0

        for topic in topics:
            tokens = self._tokenize(topic.name)
            if not tokens:
                continue
            score = sum(1 for token in tokens if token in text)
            if topic.description:
                desc_tokens = self._tokenize(topic.description)[:10]
                score += sum(0.25 for token in desc_tokens if token in text)
            if score > best_score:
                best_score = score
                best_topic = topic

        if best_topic and best_score > 0:
            return best_topic

        simple_topic_name = self._extract_simple_topic_name(question_text, assessment_title)
        if not simple_topic_name:
            return None

        topic, _ = Topic.objects.get_or_create(
            course=course,
            name=simple_topic_name,
            defaults={
                'description': f"Auto-created from SMRT-CMS activity for {course.title or course.course_id}.",
            },
        )
        return topic

    def _extract_simple_topic_name(
        self,
        question_text: Optional[str],
        assessment_title: Optional[str],
    ) -> Optional[str]:
        text = f"{assessment_title or ''} {question_text or ''}".lower().strip()
        if not text:
            return None

        for pattern, topic_name in self.SIMPLE_TOPIC_PATTERNS:
            if pattern in text:
                return topic_name

        words = [word for word in re.findall(r'[a-zA-Z]{4,}', text) if word not in {
            'which', 'following', 'write', 'sentence', 'about', 'does', 'used',
            'common', 'commonly', 'into', 'from', 'what', 'true', 'false', 'java'
        }]
        if not words:
            return None

        phrase = ' '.join(words[:3]).strip().title()
        return phrase[:100] if phrase else None

    def _save_learning_path(self, student: Student, course: Course, path_data: Dict[str, object]) -> LearningPath:
        with transaction.atomic():
            LearningPath.objects.filter(
                student=student,
                course=course,
                status='active',
            ).update(status='archived')

            learning_path = LearningPath.objects.create(
                student=student,
                course=course,
                name=f"Learning Path for {student.student_id}",
                description="Auto-generated from SMRT-CMS assessment activity",
                student_stats=path_data['student_stats'],
                total_estimated_time=path_data['total_estimated_time'],
                weak_topics_count=len(path_data['weak_topics']),
                recommended_topics_count=len(path_data['recommended_path']),
                status='active',
            )

            for order, weak_topic_data in enumerate(path_data['weak_topics']):
                topic = Topic.objects.filter(
                    name=weak_topic_data['name'],
                    course=course,
                ).first()
                if topic is None:
                    continue
                weak_topic = WeakTopic.objects.create(
                    learning_path=learning_path,
                    topic=topic,
                    current_mastery=weak_topic_data['current_mastery'],
                    prerequisites=weak_topic_data['prerequisites'],
                    related_topics=weak_topic_data['related_topics'],
                    order=order,
                )
                self._save_resources(weak_topic=weak_topic, resources=weak_topic_data['resources'])

            for priority, recommended_data in enumerate(path_data['recommended_path'], start=1):
                topic = Topic.objects.filter(
                    name=recommended_data['topic'],
                    course=course,
                ).first()
                if topic is None:
                    continue
                recommended_topic = RecommendedTopic.objects.create(
                    learning_path=learning_path,
                    topic=topic,
                    confidence=recommended_data['confidence'],
                    recommended_difficulty=recommended_data['recommended_difficulty'],
                    estimated_time_hours=recommended_data['estimated_time_hours'],
                    prerequisites=recommended_data['prerequisites'],
                    unmet_prerequisites=recommended_data['unmet_prerequisites'],
                    should_study_prerequisites_first=recommended_data['should_study_prerequisites_first'],
                    related_topics=recommended_data['related_topics'],
                    priority=priority,
                )
                self._save_resources(recommended_topic=recommended_topic, resources=recommended_data['resources'])

        return learning_path

    def _save_resources(self, resources, weak_topic=None, recommended_topic=None):
        for order, resource in enumerate(resources):
            TopicResource.objects.create(
                weak_topic=weak_topic,
                recommended_topic=recommended_topic,
                title=resource['title'],
                description=resource['description'],
                url=resource['url'],
                resource_type=resource['type'],
                difficulty=resource['difficulty'],
                estimated_time=resource['estimated_time'],
                order=order,
            )

    def _get_per_question_time(self, started_at, ended_at, question_count: int) -> datetime.timedelta:
        if question_count <= 0:
            return self.DEFAULT_TIME_PER_QUESTION
        if started_at and ended_at and ended_at >= started_at:
            total_duration = ended_at - started_at
            if total_duration.total_seconds() > 0:
                return total_duration / question_count
        return self.DEFAULT_TIME_PER_QUESTION

    def _map_question_type(self, question_type: Optional[str]) -> str:
        value = (question_type or '').lower()
        if 'multiple' in value or 'mcq' in value:
            return 'mcq'
        if 'true' in value or 'false' in value:
            return 'true_false'
        if 'fill' in value:
            return 'fill_blank'
        if 'code' in value or 'program' in value:
            return 'coding'
        if 'essay' in value:
            return 'essay'
        return 'short_answer'

    def _build_course_id(self, class_shell: ClassShell) -> str:
        base = re.sub(r'[^A-Za-z0-9]+', '-', class_shell.course_name or '').strip('-').upper()
        if not base:
            base = f"CLASS-{class_shell.pk}"
        return f"{base}-{class_shell.section_number}"[:50]

    def _extract_course_code(self, course_name: str) -> Optional[str]:
        match = re.search(r'([A-Za-z]{2,}\s*-?\s*\d{3,})', course_name or '')
        if not match:
            return None
        return re.sub(r'[^A-Za-z0-9]+', '', match.group(1)).upper()

    def _tokenize(self, value: str):
        return [token for token in re.findall(r'[a-z0-9]+', value.lower()) if len(token) > 2]
