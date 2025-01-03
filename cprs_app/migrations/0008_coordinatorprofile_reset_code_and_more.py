# Generated by Django 5.0 on 2024-09-16 12:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cprs_app', '0007_alter_studentinformation_achievements_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='coordinatorprofile',
            name='reset_code',
            field=models.CharField(blank=True, max_length=6, null=True),
        ),
        migrations.AddField(
            model_name='coordinatorprofile',
            name='reset_code_expires_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='studentprofile',
            name='reset_code',
            field=models.CharField(blank=True, max_length=6, null=True),
        ),
        migrations.AddField(
            model_name='studentprofile',
            name='reset_code_expires_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
