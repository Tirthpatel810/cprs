# Generated by Django 5.0 on 2024-09-19 09:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cprs_app', '0008_coordinatorprofile_reset_code_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='JobDrive',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('company', models.CharField(max_length=255)),
                ('location', models.CharField(max_length=255)),
                ('job_description', models.TextField()),
                ('skills_required', models.CharField(max_length=255)),
                ('salary', models.CharField(max_length=50)),
                ('last_date_to_apply', models.DateField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
