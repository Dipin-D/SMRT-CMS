# Generated by Django 5.1.4 on 2024-12-16 23:07

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('instructor', '0011_exercisequestion_mark_question_mark'),
        ('student', '0002_alter_assignmentsubmission_class_shell'),
    ]

    operations = [
        migrations.AlterField(
            model_name='assignmentsubmission',
            name='class_shell',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='instructor.classshell'),
        ),
    ]
