# Generated by Django 2.1.11 on 2019-08-27 16:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fastrunner', '0018_auto_20190719_1148'),
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='belong_project',
            field=models.ManyToManyField(blank=True, to='fastrunner.Project'),
        ),
    ]
