# Generated by Django 4.2.16 on 2024-10-31 01:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('instructor', '0010_remove_exercisequestion_is_true_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='exercisequestion',
            name='mark',
            field=models.IntegerField(default=5),
        ),
        migrations.AddField(
            model_name='question',
            name='mark',
            field=models.IntegerField(default=5),
        ),
    ]
