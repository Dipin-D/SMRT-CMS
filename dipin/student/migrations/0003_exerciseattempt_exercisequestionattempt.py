# Generated by Django 4.2.16 on 2024-11-18 15:45

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('instructor', '0011_exercisequestion_mark_question_mark'),
        ('student', '0002_assignmentsubmission'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExerciseAttempt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score', models.FloatField(default=0)),
                ('total_marks', models.FloatField()),
                ('attempted_on', models.DateTimeField(auto_now_add=True)),
                ('class_shell', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='exercise_attempts', to='instructor.classshell')),
                ('exercise', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attempts', to='instructor.exercise')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='exercise_attempts', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='ExerciseQuestionAttempt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('student_answer', models.TextField()),
                ('is_correct', models.BooleanField()),
                ('exercise_attempt', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='question_attempts', to='student.exerciseattempt')),
                ('exercise_question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attempts', to='instructor.exercisequestion')),
            ],
        ),
    ]
