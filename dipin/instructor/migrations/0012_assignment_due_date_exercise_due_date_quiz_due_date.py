# Generated by Django 5.1.4 on 2025-01-31 19:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('instructor', '0011_exercisequestion_mark_question_mark'),
    ]

    operations = [
        migrations.AddField(
            model_name='assignment',
            name='due_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='exercise',
            name='due_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='quiz',
            name='due_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
