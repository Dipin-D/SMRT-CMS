# Generated by Django 4.2.16 on 2024-10-30 23:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('instructor', '0007_exercisequestion_question_question_question'),
    ]

    operations = [
        migrations.RenameField(
            model_name='exercisequestion',
            old_name='question',
            new_name='question_text',
        ),
        migrations.RenameField(
            model_name='question',
            old_name='question',
            new_name='question_text',
        ),
    ]
