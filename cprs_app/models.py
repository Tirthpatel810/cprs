from django.db import models
from django.utils import timezone

class CoordinatorProfile(models.Model):
    coordinator_name = models.CharField(max_length=20, blank=True)
    email = models.EmailField(max_length=254, unique=True, default=None)
    department = models.CharField(null=True, blank=True,max_length=50)
    password = models.CharField(max_length=100,default=None)
    profile_photo = models.ImageField(upload_to='profile_photos/', null=True, blank=True)
    mobile_number = models.CharField(max_length=15, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], null=True, blank=True)
    hire_date = models.DateField(null=True, blank=True)
    reset_code = models.CharField(max_length=6, blank=True, null=True)
    reset_code_expires_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Name: {self.coordinator_name} (Email:{self.email})"


class StudentProfile(models.Model):
    student_name = models.CharField(max_length=100,default=None)
    email = models.EmailField(unique=True,blank=True,null=True)
    department = models.CharField(max_length=50,default=None)
    password = models.CharField(max_length=128,default=None)
    reset_code = models.CharField(max_length=6, blank=True, null=True)
    reset_code_expires_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Name: {self.student_name} (Email:{self.email})"

class StudentInformation(models.Model):
    student_profile = models.OneToOneField(StudentProfile, on_delete=models.CASCADE, related_name='student_info')

    # New fields
    student_id = models.CharField(max_length=50, unique=True, blank=True, null=True)
    college_email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=200)
    personal_email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], blank=True, null=True)
    profile_photo = models.ImageField(upload_to='student_photos/', blank=True, null=True)
    permanent_address = models.TextField(blank=True, null=True)
    current_address = models.TextField(blank=True, null=True)
    department = models.CharField(max_length=100)
    degree_program = models.CharField(max_length=100, blank=True, null=True)
    year_of_enrollment = models.IntegerField(blank=True, null=True)
    year_of_graduation = models.IntegerField(blank=True, null=True)

    # Education details
    tenth_percentage = models.FloatField(blank=True, null=True)
    tenth_passing_year = models.IntegerField(blank=True, null=True)
    tenth_school = models.CharField(max_length=200, blank=True, null=True)

    twelfth_stream = models.CharField(max_length=50, choices=[('Science', 'Science'), ('Commerce', 'Commerce'), ('Arts', 'Arts'), ('Other', 'Other')], blank=True, null=True)
    twelfth_percentage = models.FloatField(blank=True, null=True)
    twelfth_passing_year = models.IntegerField(blank=True, null=True)
    twelfth_school = models.CharField(max_length=200, blank=True, null=True)

    ug_course = models.CharField(max_length=100, blank=True, null=True)
    ug_passing_year = models.IntegerField(blank=True, null=True)
    ug_cgpa = models.FloatField(blank=True, null=True)
    ug_college_university = models.CharField(max_length=200, blank=True, null=True)

    # Post-graduation and other education
    other_course = models.CharField(max_length=100, blank=True, null=True)
    other_passing_year = models.IntegerField(blank=True, null=True)
    other_cgpa = models.FloatField(blank=True, null=True)
    other_college_university = models.CharField(max_length=200, blank=True, null=True)

    backlogs = models.IntegerField(default=0, blank=True, null=True)
    skills = models.TextField(blank=True, null=True)
    certifications = models.TextField(blank=True, null=True)
    internship_details = models.TextField(blank=True, null=True)
    projects = models.TextField(blank=True, null=True)
    achievements = models.TextField(blank=True, null=True)
    extracurricular_activities = models.TextField(blank=True, null=True)

    resume = models.FileField(upload_to='resumes/', blank=True, null=True)
    linkedin_profile = models.URLField(blank=True, null=True)
    github_profile = models.URLField(blank=True, null=True)

    placement_preferences = models.TextField(blank=True, null=True)
    placed_status = models.BooleanField(default=False)
    job_offers = models.TextField(blank=True, null=True)
    date_of_last_update = models.DateTimeField(default=timezone.now)
    nationality = models.CharField(max_length=50, blank=True, null=True)

    def has_applied_for_job(self, job_drive):
        return AppliedJob.objects.filter(student=self, job_drive=job_drive).exists()

    def __str__(self):
        return f"Student: {self.full_name} (ID: {self.student_id})"

class JobDrive(models.Model):
    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    job_description = models.TextField()
    skills_required = models.CharField(max_length=255)
    salary = models.CharField(max_length=50)
    vacancies = models.IntegerField(default=0)
    last_date_to_apply = models.DateField()
    tentative_drive_date = models.DateField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    
class Announcement(models.Model):
    title = models.CharField(max_length=255)
    message = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    posted_by = models.ForeignKey('CoordinatorProfile', on_delete=models.CASCADE)

    def __str__(self):
        return self.title

class AppliedJob(models.Model):
    STATUS_CHOICES = (
        ('applied', 'Applied'),
        ('shortlisted', 'Shortlisted'),
        ('selected', 'Selected'),
        ('rejected', 'Rejected'),
    )

    student = models.ForeignKey(StudentInformation, on_delete=models.CASCADE)
    job_drive = models.ForeignKey(JobDrive, on_delete=models.CASCADE)
    applied_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='applied')

    def __str__(self):
        return f"{self.student.full_name} - {self.job_drive.title} - {self.status}"

class DiscussionMessage(models.Model):
    username = models.CharField(max_length=100)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.username}: {self.content[:20]}..."
