# Generated by Django 5.1.4 on 2025-03-27 17:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0009_alter_exerciseattempt_total_marks_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='exerciseattempt',
            name='total_marks',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='quizattempt',
            name='total_marks',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
