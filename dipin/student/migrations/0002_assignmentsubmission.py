# Generated by Django 4.2.16 on 2024-11-18 00:46

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('instructor', '0011_exercisequestion_mark_question_mark'),
        ('student', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AssignmentSubmission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('submission_text', models.TextField()),
                ('submission_file', models.FileField(blank=True, null=True, upload_to='assignments/')),
                ('submitted_on', models.DateTimeField(auto_now_add=True)),
                ('graded', models.BooleanField(default=False)),
                ('grade', models.FloatField(blank=True, null=True)),
                ('assignment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='submissions', to='instructor.assignment')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assignment_submissions', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]