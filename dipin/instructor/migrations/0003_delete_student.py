# Generated by Django 4.2.16 on 2024-10-27 20:35

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('instructor', '0002_student'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Student',
        ),
    ]
