# Generated by Django 5.1.4 on 2025-05-03 00:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('instructor', '0018_alter_exercisequestion_text_alter_question_text'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='exercisequestion',
            name='mcq_answer',
        ),
        migrations.RemoveField(
            model_name='question',
            name='mcq_answer',
        ),
        migrations.AddField(
            model_name='exercisequestion',
            name='mcq_answers',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='question',
            name='mcq_answers',
            field=models.JSONField(blank=True, null=True),
        ),
    ]
