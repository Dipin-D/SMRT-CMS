# Generated by Django 5.1.4 on 2025-04-15 20:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0010_alter_exerciseattempt_total_marks_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='exerciseattempt',
            name='submitted',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='quizattempt',
            name='submitted',
            field=models.BooleanField(default=False),
        ),
    ]
