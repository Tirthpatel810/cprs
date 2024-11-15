from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password,check_password
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.core.paginator import Paginator
from .models import *
import csv
import io
import pandas as pd
from .models import StudentProfile
from django.db.models import Q
import random
import string
from django.utils import timezone
from datetime import datetime, timedelta
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from django.http import HttpResponse
from io import BytesIO

from functools import wraps


def login(request):
    if request.method == 'POST':
        uname = request.POST.get('username')
        password = request.POST.get('password')

        # Check if the user is the admin
        if uname == 'django-admin' and password == 'admin147896325':
            return redirect('/django-administration/')
        
        if uname == 'coordinator123456' and password == '123456':
            request.session['role'] = 'admin'
            request.session['username'] = uname
            return redirect('admin_dashboard')

        # Check if the user is a coordinator
        try:
            coordinator = CoordinatorProfile.objects.get(email=uname)
            if check_password(password, coordinator.password):  # Hashed password checking logic
                request.session['role'] = 'coordinator'  # Store user role in the session
                request.session['username'] = uname  # Store username in the session
                return redirect('coordinator_dashboard')
            else:
                messages.error(request, 'Invalid password for coordinator.')
                return redirect('login_form')
        except CoordinatorProfile.DoesNotExist:
            pass  # Coordinator not found, continue to check for student

        # Check if the user is a student
        try:
            student = StudentProfile.objects.get(email=uname)
            if check_password(password, student.password):  # Hashed password checking logic
                request.session['role'] = 'student'  # Store user role in the session
                request.session['username'] = uname  # Store username in the session
                return redirect('student_dashboard')
            else:
                messages.error(request, 'Invalid password for student.')
                return redirect('login_form')
        except StudentProfile.DoesNotExist:
            pass  # Student not found, show error

        # If neither a coordinator nor student
        messages.error(request, 'Invalid email or password.')
        return redirect('login_form')

    return render(request, 'login.html')

def login_required(function=None):
    @wraps(function)
    def wrapper(request, *args, **kwargs):
        if 'username' not in request.session:  # Check if session has 'username'
            return redirect('login_form')  # Redirect to login page if not logged in
        return function(request, *args, **kwargs)
    return wrapper

def logout(request):
    request.session.flush()  # Clear all session data
    return redirect('login_form')

def forgot_password(request):
    if request.method == 'POST':
        email = request.POST['email']

        # Check if the email exists in either StudentProfile or CoordinatorProfile
        user = None
        try:
            user = StudentProfile.objects.get(email=email)
        except StudentProfile.DoesNotExist:
            try:
                user = CoordinatorProfile.objects.get(email=email)
            except CoordinatorProfile.DoesNotExist:
                messages.error(request, "Email not found!")
                return redirect('forgot_password')

        # Generate a random reset code
        reset_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

        # Save the reset code and expiration time (valid for 2 minutes)
        user.reset_code = reset_code
        user.reset_code_expires_at = timezone.now() + timedelta(minutes=2)
        user.save()

        # Send the reset code via email
        send_mail(
            'Password Reset Code',
            f'Your password reset code is: {reset_code}. It will expire in 2 minutes.',
            'pateltirth2833@gmail.com',
            [email],
            fail_silently=False,
        )

        messages.success(request, "A reset code has been sent to your email.")
        return redirect('verify_reset_code')

    return render(request, 'forgot_password.html')

def verify_reset_code(request):
    if request.method == 'POST':
        reset_code = request.POST['reset_code']

        # Check both StudentProfile and CoordinatorProfile for valid reset code
        user = None
        try:
            user = StudentProfile.objects.get(reset_code=reset_code, reset_code_expires_at__gt=timezone.now())
        except StudentProfile.DoesNotExist:
            try:
                user = CoordinatorProfile.objects.get(reset_code=reset_code, reset_code_expires_at__gt=timezone.now())
            except CoordinatorProfile.DoesNotExist:
                messages.error(request, "Invalid or expired reset code!")
                return redirect('verify_reset_code')

        # If reset code is valid, proceed to reset password form
        return redirect('reset_password', user_id=user.id)

    return render(request, 'verify_reset_code.html')

def reset_password(request, user_id):
    # Try to find the user in StudentProfile or CoordinatorProfile
    user = None
    try:
        user = StudentProfile.objects.get(id=user_id)
    except StudentProfile.DoesNotExist:
        try:
            user = CoordinatorProfile.objects.get(id=user_id)
        except CoordinatorProfile.DoesNotExist:
            messages.error(request, "User not found!")
            return redirect('login')

    if request.method == 'POST':
        new_password = request.POST['new_password']
        confirm_password = request.POST['confirm_password']

        if new_password != confirm_password:
            messages.error(request, "Passwords do not match!")
            return redirect('reset_password', user_id=user_id)

        # Update the user's password
        user.password = make_password(new_password)  # Set hashed password if you're not using Django's User model
        user.reset_code = None  # Clear the reset code
        user.save()

        messages.success(request, "Password has been reset successfully!")
        return redirect('login_form')

    return render(request, 'reset_password.html')

@login_required
def admin_dashboard(request, section=None):
    context = {}

    if section == 'create-coordinator':
        context['section'] = 'admin_sections/create_coordinator.html'

    elif section == 'create-student':
        context['section'] = 'admin_sections/create_student.html'

    elif section == 'view-students':
        # Get search query and sort order from the request
        search_query = request.GET.get('search', '')
        sort_order = request.GET.get('sort', '')

        # Filter students based on the search query
        students_list = StudentProfile.objects.all()
        if search_query:
            students_list = students_list.filter(
                Q(student_name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(department__icontains=search_query)
            )

        # Sort students based on the sort order
        if sort_order == 'name':
            students_list = students_list.order_by('student_name')
        elif sort_order == 'email':
            students_list = students_list.order_by('email')
        elif sort_order == 'department':
            students_list = students_list.order_by('department')

        # Paginate the filtered and sorted results
        paginator = Paginator(students_list, 9)  # Show 9 students per page
        page_number = request.GET.get('page')
        students_page = paginator.get_page(page_number)

        context['students'] = students_page
        context['search_query'] = search_query
        context['sort_order'] = sort_order
        context['section'] = 'admin_sections/view_students.html'

    elif section == 'view-coordinators':
        # Get search query and sort order from the request
        search_query = request.GET.get('search', '')
        sort_order = request.GET.get('sort', '')

        # Filter coordinators based on the search query
        coordinators_list = CoordinatorProfile.objects.all()
        if search_query:
            coordinators_list = coordinators_list.filter(
                Q(coordinator_name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(department__icontains=search_query)
            )

        # Sort coordinators based on the sort order
        if sort_order == 'name':
            coordinators_list = coordinators_list.order_by('coordinator_name')
        elif sort_order == 'email':
            coordinators_list = coordinators_list.order_by('email')
        elif sort_order == 'department':
            coordinators_list = coordinators_list.order_by('department')

        # Paginate the filtered and sorted results
        paginator = Paginator(coordinators_list, 12)  # Show 12 coordinators per page
        page_number = request.GET.get('page')
        coordinators = paginator.get_page(page_number)

        # Pass the search query and sort order back to the template to retain the values in the form
        context['coordinators'] = coordinators
        context['search_query'] = search_query
        context['sort_order'] = sort_order
        context['section'] = 'admin_sections/view_coordinators.html'

    elif section == 'job-openings':
        # Get search query and sort order from the request
        search_query = request.GET.get('search', '')
        sort_order = request.GET.get('sort', '')

        # Filter jobs based on the search query
        jobs_list = JobDrive.objects.all()
        if search_query:
            jobs_list = jobs_list.filter(
                Q(title__icontains=search_query) |
                Q(company__icontains=search_query) |
                Q(location__icontains=search_query)
            )

        # Sort jobs based on the sort order
        if sort_order == 'title':
            jobs_list = jobs_list.order_by('title')
        elif sort_order == 'company':
            jobs_list = jobs_list.order_by('company')
        elif sort_order == 'date':
            jobs_list = jobs_list.order_by('-created_at')

        # Paginate the filtered and sorted results
        paginator = Paginator(jobs_list, 9)  # Show 9 job drives per page
        page_number = request.GET.get('page')
        jobs_page = paginator.get_page(page_number)

        context['jobs'] = jobs_page
        context['search_query'] = search_query
        context['sort_order'] = sort_order
        context['section'] = 'coordinator_sections/job_openings.html'
        
    else:
        coordinator_count = CoordinatorProfile.objects.count()
        student_count = StudentProfile.objects.count()
        placed_students_count = StudentInformation.objects.filter(placed_status=True).count()
        unplaced_students_count = StudentInformation.objects.filter(placed_status=False).count()

        context = {
            'coordinator_count': coordinator_count,
            'student_count': student_count,
            'placed_students_count': placed_students_count,
            'unplaced_students_count': unplaced_students_count,
        }
        # return redirect('admin_dashboard', context)

        context['coordinator_count'] = coordinator_count
        context['student_count'] = student_count
        context['placed_students_count'] = placed_students_count
        context['unplaced_students_count'] = unplaced_students_count
        context['section'] = 'admin_sections/default.html'

    return render(request, 'admin_dashboard.html', context)

def create_coordinator(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        department = request.POST.get('department')
        password = request.POST.get('password')
        
        if CoordinatorProfile.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists.')
            return redirect('admin_dashboard_section', section='create-coordinator')
        
        CoordinatorProfile.objects.create(
            coordinator_name=name,
            email=email,
            department=department,
            password=make_password(password)
        )
        
        messages.success(request, 'Recruiter created successfully!')

        return redirect('admin_dashboard_section', section='create-coordinator')
    
    return redirect('admin_dashboard_section', section='create-coordinator')

def create_student(request):
    if request.method == 'POST':
        if 'single_account' in request.POST:
            # Handle single account creation
            name = request.POST.get('name')
            email = request.POST.get('email')
            department = request.POST.get('department')
            password = request.POST.get('password')

            if StudentProfile.objects.filter(email=email).exists():
                messages.error(request, 'Email already exists.')
            else:
                student_profile = StudentProfile.objects.create(
                    student_name=name,
                    email=email,
                    department=department,
                    password=make_password(password)
                )
                StudentInformation.objects.create(
                student_profile=student_profile,
                full_name=name,
                college_email=email,
                department=department
            )
                messages.success(request, 'Student account created successfully!')
            
            email = request.session['username']
            if CoordinatorProfile.objects.filter(email=email).exists():
                return redirect('coordinator_dashboard_section', section='add-student')
            else:
                return redirect('admin_dashboard_section', section='create-student')

        elif 'file' in request.FILES:  # Corrected this line to check for 'file'
            # Handle file upload
            uploaded_file = request.FILES['file']
            file_extension = uploaded_file.name.split('.')[-1].lower()

            if file_extension == 'csv':
                try:
                    # Handle CSV file
                    data = uploaded_file.read().decode('utf-8')
                    print("CSV File content: ", data)
                    csv_reader = csv.reader(io.StringIO(data))
                    header = next(csv_reader)  # Get header

                    required_columns = ['email', 'name', 'department', 'password']
                    if header != required_columns:  # Check if the header matches the required structure
                        raise KeyError("Invalid columns")

                    for row in csv_reader:
                        email, name, department, password = row
                        if not StudentProfile.objects.filter(email=email).exists():
                            student_profile = StudentProfile.objects.create(
                            student_name=name,
                            email=email,
                            department=department,
                            password=make_password(password))
                            StudentInformation.objects.create(
                            student_profile=student_profile,
                            full_name=name,
                            college_email=email,
                            department=department)
                    messages.success(request, 'Students created successfully from CSV!')

                except KeyError as e:
                    messages.error(request, "Invalid columns in CSV file.")
                except Exception as e:
                    messages.error(request, f"Error processing file: {str(e)}")

            elif file_extension in ['xls', 'xlsx']:
                try:
                    # Handle Excel file
                    df = pd.read_excel(uploaded_file)
                    print("Excel File content: ", df.head())

                    required_columns = ['email', 'name', 'department', 'password']
                    df_columns = df.columns.str.lower().tolist()

                    if not all(column in df_columns for column in required_columns):
                        raise KeyError("Invalid columns")

                    for index, row in df.iterrows():
                        email = row['email']
                        name = row['name']
                        department = row['department']
                        password = row['password']

                        if not StudentProfile.objects.filter(email=email).exists():
                            StudentProfile.objects.create(
                                student_name=name,
                                email=email,
                                department=department,
                                password=make_password(password)
                            )
                    messages.success(request, 'Students created successfully from Excel!')

                except KeyError as e:
                    messages.error(request, "Invalid columns in Excel file.")
                except Exception as e:
                    messages.error(request, f"Error processing file: {str(e)}")

            else:
                messages.error(request, 'Invalid file type. Only CSV and Excel files are accepted.')

            email = request.session['username']
            if CoordinatorProfile.objects.filter(email=email).exists():
                return redirect('coordinator_dashboard_section', section='add-student')
            else:
                return redirect('admin_dashboard_section', section='create-student')

    # Redirect after processing
    email = request.session['username']
    if CoordinatorProfile.objects.filter(email=email).exists():
        return redirect('coordinator_dashboard_section', section='add-student')
    else:
        return redirect('admin_dashboard_section', section='create-student')

@login_required
def student_dashboard(request, section=None):
    context = {}

    try:
        student_email = request.session.get('username')
        student_profile = StudentProfile.objects.get(email=student_email)
    except StudentProfile.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('login_form')

    if section == 'view-profile':
        pk = request.session['username']
        student = get_object_or_404(StudentInformation, college_email=pk)
        context['student'] = student
        context['section'] = 'student_details.html'

    elif section == 'edit-profile':
        pk = request.session['username']
        student_info = get_object_or_404(StudentInformation, college_email=pk)
    
        if request.method == 'POST':
            student_info.student_id = request.POST.get('student_id')

            student_info.full_name = request.POST.get('full_name')
            student_info.personal_email = request.POST.get('personal_email')
            student_info.phone_number = request.POST.get('phone_number')
            date_of_birth_str = request.POST.get('date_of_birth')
            try:
                dob_formatted = datetime.strptime(date_of_birth_str, '%Y-%m-%d').strftime('%Y-%m-%d')
            except ValueError:
                dob_formatted = datetime.strptime(date_of_birth_str, '%d/%m/%Y').strftime('%Y-%m-%d')
            student_info.date_of_birth = dob_formatted
            student_info.gender = request.POST.get('gender')
            student_info.permanent_address = request.POST.get('permanent_address')
            student_info.current_address = request.POST.get('current_address', student_info.permanent_address if request.POST.get('same_as_permanent') else student_info.current_address)
            student_info.degree_program = request.POST.get('degree_program')

            year_of_enrollment = request.POST.get('year_of_enrollment')
            if year_of_enrollment.isdigit():
                student_info.year_of_enrollment = int(year_of_enrollment)
            else:
                student_info.year_of_enrollment = 0

            year_of_graduation = request.POST.get('year_of_graduation')
            if year_of_graduation.isdigit():
                student_info.year_of_graduation = int(year_of_graduation)
            else:
                student_info.year_of_graduation = 0
            
            tenth_percentage = request.POST.get('tenth_percentage')
            if tenth_percentage.isdigit():
                student_info.tenth_percentage = float(tenth_percentage)
            else:
                student_info.tenth_percentage = 0
            
            tenth_passing_year = request.POST.get('tenth_passing_year')
            if tenth_passing_year.isdigit():
                student_info.tenth_passing_year = int(tenth_passing_year)
            else:
                student_info.tenth_passing_year = 0
            
            student_info.tenth_school = request.POST.get('tenth_school')
            student_info.twelfth_stream = request.POST.get('twelfth_stream')

            
            twelfth_percentage = request.POST.get('twelfth_percentage')
            if twelfth_percentage.isdigit():
                student_info.twelfth_percentage = float(twelfth_percentage)
            else:
                student_info.twelfth_percentage = 0
            
            twelfth_passing_year = request.POST.get('twelfth_passing_year')
            if twelfth_passing_year.isdigit():
                student_info.twelfth_passing_year = int(twelfth_passing_year)
            else:
                student_info.twelfth_passing_year = 0
            
            student_info.twelfth_school = request.POST.get('twelfth_school')
            student_info.ug_course = request.POST.get('ug_course')

            
            ug_passing_year = request.POST.get('ug_passing_year')
            if ug_passing_year.isdigit():
                student_info.ug_passing_year = int(ug_passing_year)
            else:
                student_info.ug_passing_year = 0

            ug_cgpa = request.POST.get('ug_cgpa')
            if ug_cgpa.isdigit():
                student_info.ug_cgpa = float(ug_cgpa)
            else:
                student_info.ug_cgpa = 0
            
            student_info.ug_college_university = request.POST.get('ug_college_university')
            student_info.other_course = request.POST.get('other_course')

            
            other_passing_year = request.POST.get('other_passing_year')
            if other_passing_year.isdigit():
                student_info.other_passing_year = int(other_passing_year)
            else:
                student_info.other_passing_year = 0
            
            other_cgpa = request.POST.get('other_cgpa')
            if other_cgpa.isdigit():
                student_info.other_cgpa = float(other_cgpa)
            else:
                student_info.other_cgpa = 0
            
            student_info.other_college_university = request.POST.get('other_college_university')
            student_info.backlogs = request.POST.get('backlogs')
            student_info.skills = request.POST.get('skills')
            student_info.certifications = request.POST.get('certifications')
            student_info.internship_details = request.POST.get('internship_details')
            student_info.projects = request.POST.get('projects')
            student_info.extracurricular_activities = request.POST.get('extracuronal_activities')
            student_info.achievements = request.POST.get('achievements')
            student_info.linkedin_profile = request.POST.get('linkedin_profile')
            student_info.github_profile = request.POST.get('github_profile')
            student_info.placement_preferences = request.POST.get('placement_preferences')
            student_info.placed_status = request.POST.get('placed_status')
            student_info.job_offers = request.POST.get('job_offers')
            student_info.date_of_last_update = datetime.now()
            student_info.nationality = request.POST.get('nationality')

            # Handle profile photo upload
            if request.FILES.get('profile_photo'):
                student_info.profile_photo = request.FILES.get('profile_photo')
            if request.FILES.get('resume'):
                student_info.resume = request.FILES.get('resume')

            try:
                student_info.save()
                messages.success(request, 'Student information updated successfully!')
                email = request.session['username']
                if StudentProfile.objects.filter(email=email).exists():
                    return redirect('student_dashboard_section', section='view-profile')
            except ValidationError as e:
                messages.error(request, f"Error updating student: {e}")
            
        context['student_info'] = student_info
        context['section'] = 'edit_student.html'

    elif section == 'view-placements':
        # Get all upcoming placement drives
        upcoming_job_drives = JobDrive.objects.filter(tentative_drive_date__gte=timezone.now())
        student_info = get_object_or_404(StudentInformation, college_email=request.session['username'])

        # Check if the student has applied for each job drive
        job_drives_with_status = []
        for job_drive in upcoming_job_drives:
            has_applied = student_info.has_applied_for_job(job_drive)
            job_drives_with_status.append({
                'job_drive': job_drive,
                'has_applied': has_applied
            })

        # Handle search and sorting here
        search_query = request.GET.get('search', '')
        if search_query:
            upcoming_job_drives = upcoming_job_drives.filter(
                models.Q(company__icontains=search_query) |
                models.Q(title__icontains=search_query) |
                models.Q(location__icontains=search_query)
            )

        sort_by = request.GET.get('sort_by', 'tentative_drive_date')
        upcoming_job_drives = upcoming_job_drives.order_by(sort_by)

        context = {
            'job_drives_with_status': job_drives_with_status,
            'job_drives': upcoming_job_drives,
            'student_info': student_info,
            'search_query': search_query,
            'section': 'student_sections/view_placements.html',
        }

        return render(request, 'student_dashboard.html', context)

    elif section == 'announcements':
        search_query = request.GET.get('search', '')

        # Fetch and filter all announcements
        announcements = Announcement.objects.all()
        if search_query:
            announcements = announcements.filter(
                Q(title__icontains=search_query) |
                Q(message__icontains=search_query)
            )

        context['announcements'] = announcements.order_by('-created_at')
        context['search_query'] = search_query
        
        context['section'] = 'coordinator_sections/all_announcements.html'

    elif section == 'applied-jobs':
        student = get_object_or_404(StudentInformation, college_email=request.session['username'])
        jobs = AppliedJob.objects.filter(student=student)
        context['applied_jobs'] = jobs
        context['section'] = 'student_sections/applied_jobs.html'

    elif section == 'discussion':
        msgs = DiscussionMessage.objects.all().order_by('-timestamp')

        if request.method == 'POST':
            content = request.POST.get('message')
            username = request.session.get('username')

            if content and username:
                DiscussionMessage.objects.create(username=username, content=content)
                return redirect('student_dashboard_section', section='discussion')

        context['msgs'] = msgs
        context['section'] = 'student_sections/discussion.html'

    else:
        job_drives = JobDrive.objects.exclude(tentative_drive_date__isnull=True)
        context = {
            'job_drives': job_drives,
            'student_profile': student_profile,
            'section': 'student_sections/default.html',
        }

    return render(request, 'student_dashboard.html', context)

def edit_coordinator(request, pk):
    coordinator = get_object_or_404(CoordinatorProfile, pk=pk)
    
    if request.method == 'POST':
        # Check if a new profile photo is uploaded
        if 'profile_photo' in request.FILES:
            coordinator.profile_photo = request.FILES['profile_photo']  # Update with new photo
        # Otherwise, keep the existing photo
        # If you use `coordinator.profile_photo = None` or similar logic, it will set it to default

        # Update other fields
        coordinator.coordinator_name = request.POST.get('coordinator_name')
        coordinator.email = request.POST.get('email')
        coordinator.department = request.POST.get('department')
        coordinator.mobile_number = request.POST.get('mobile_number')
        coordinator.address = request.POST.get('address')
        coordinator.date_of_birth = request.POST.get('date_of_birth')
        coordinator.gender = request.POST.get('gender')
        coordinator.hire_date = request.POST.get('hire_date')
        
        # Save the updated coordinator
        coordinator.save()
        messages.success(request, 'Coordinator details updated successfully!')
        email = request.session['username']
        if CoordinatorProfile.objects.filter(email=email).exists():
            return redirect('coordinator_dashboard_section', section='manage-profile')
        else:
            return redirect('view_coordinators')
    
    return render(request, 'edit_coordinator.html', {'coordinator': coordinator})

def delete_coordinator(request, id):
    coordinator = get_object_or_404(CoordinatorProfile, id=id)
    coordinator.delete()
    messages.success(request, 'Coordinator deleted successfully!')
    return redirect(reverse('admin_dashboard_section', args=['view-coordinators']))

def view_student_details(request, pk):
    student = get_object_or_404(StudentInformation, college_email=pk)
    return render(request, 'student_details.html', {'student': student})

@login_required
def edit_student(request, pk):
    student_info = get_object_or_404(StudentInformation, college_email=pk)
    if request.method == 'POST':

            student_info.student_id = request.POST.get('student_id')
            student_info.full_name = request.POST.get('full_name')
            student_info.personal_email = request.POST.get('personal_email')
            student_info.phone_number = request.POST.get('phone_number')
            date_of_birth_str = request.POST.get('date_of_birth')
            try:
                dob_formatted = datetime.strptime(date_of_birth_str, '%Y-%m-%d').strftime('%Y-%m-%d')
            except ValueError:
                dob_formatted = datetime.strptime(date_of_birth_str, '%d/%m/%Y').strftime('%Y-%m-%d')
            student_info.date_of_birth = dob_formatted
            student_info.gender = request.POST.get('gender')
            student_info.permanent_address = request.POST.get('permanent_address')
            student_info.current_address = request.POST.get('current_address', student_info.permanent_address if request.POST.get('same_as_permanent') else student_info.current_address)
            student_info.degree_program = request.POST.get('degree_program')

            year_of_enrollment = request.POST.get('year_of_enrollment')
            if year_of_enrollment.isdigit():
                student_info.year_of_enrollment = int(year_of_enrollment)
            else:
                student_info.year_of_enrollment = 0

            year_of_graduation = request.POST.get('year_of_graduation')
            if year_of_graduation.isdigit():
                student_info.year_of_graduation = int(year_of_graduation)
            else:
                student_info.year_of_graduation = 0
            
            tenth_percentage = request.POST.get('tenth_percentage')
            if tenth_percentage.isdigit():
                student_info.tenth_percentage = float(tenth_percentage)
            else:
                student_info.tenth_percentage = 0
            
            tenth_passing_year = request.POST.get('tenth_passing_year')
            if tenth_passing_year.isdigit():
                student_info.tenth_passing_year = int(tenth_passing_year)
            else:
                student_info.tenth_passing_year = 0
            
            student_info.tenth_school = request.POST.get('tenth_school')
            student_info.twelfth_stream = request.POST.get('twelfth_stream')

            
            twelfth_percentage = request.POST.get('twelfth_percentage')
            if twelfth_percentage.isdigit():
                student_info.twelfth_percentage = float(twelfth_percentage)
            else:
                student_info.twelfth_percentage = 0
            
            twelfth_passing_year = request.POST.get('twelfth_passing_year')
            if twelfth_passing_year.isdigit():
                student_info.twelfth_passing_year = int(twelfth_passing_year)
            else:
                student_info.twelfth_passing_year = 0
            
            student_info.twelfth_school = request.POST.get('twelfth_school')
            student_info.ug_course = request.POST.get('ug_course')

            
            ug_passing_year = request.POST.get('ug_passing_year')
            if ug_passing_year.isdigit():
                student_info.ug_passing_year = int(ug_passing_year)
            else:
                student_info.ug_passing_year = 0

            ug_cgpa = request.POST.get('ug_cgpa')
            if ug_cgpa.isdigit():
                student_info.ug_cgpa = float(ug_cgpa)
            else:
                student_info.ug_cgpa = 0
            
            student_info.ug_college_university = request.POST.get('ug_college_university')
            student_info.other_course = request.POST.get('other_course')

            
            other_passing_year = request.POST.get('other_passing_year')
            if other_passing_year.isdigit():
                student_info.other_passing_year = int(other_passing_year)
            else:
                student_info.other_passing_year = 0
            
            other_cgpa = request.POST.get('other_cgpa')
            if other_cgpa.isdigit():
                student_info.other_cgpa = float(other_cgpa)
            else:
                student_info.other_cgpa = 0
            
            student_info.other_college_university = request.POST.get('other_college_university')
            student_info.backlogs = request.POST.get('backlogs')
            student_info.skills = request.POST.get('skills')
            student_info.certifications = request.POST.get('certifications')
            student_info.internship_details = request.POST.get('internship_details')
            student_info.projects = request.POST.get('projects')
            student_info.extracurricular_activities = request.POST.get('extracuronal_activities')
            student_info.achievements = request.POST.get('achievements')
            student_info.linkedin_profile = request.POST.get('linkedin_profile')
            student_info.github_profile = request.POST.get('github_profile')
            student_info.placement_preferences = request.POST.get('placement_preferences')
            student_info.placed_status = request.POST.get('placed_status')
            student_info.job_offers = request.POST.get('job_offers')
            student_info.date_of_last_update = datetime.now()
            student_info.nationality = request.POST.get('nationality')

            # Handle profile photo upload
            if request.FILES.get('profile_photo'):
                student_info.profile_photo = request.FILES.get('profile_photo')
            if request.FILES.get('resume'):
                student_info.resume = request.FILES.get('resume')   

            try:
                student_info.save()
                messages.success(request, 'Student information updated successfully!')
                email = request.session['username']
                if StudentProfile.objects.filter(email=email).exists():
                    return redirect('student_dashboard_section', section='view-profile')
                elif CoordinatorProfile.objects.filter(email=email).exists():
                    return redirect('coordinator_dashboard_section', section='manage-students')
                else:
                    return redirect('admin_dashboard_section', section='view-students')
            except ValidationError as e:
                messages.error(request, f"Error updating student: {e}")
    
    return render(request, 'edit_student.html', {'student_info': student_info})

@login_required
def delete_student(request, pk):

    student = get_object_or_404(StudentProfile, email=pk)
    student.delete()
    messages.success(request, 'Student deleted successfully!')
    email = request.session['username']
    if CoordinatorProfile.objects.filter(email=email).exists():
        return redirect('coordinator_dashboard_section', section='manage-students')
    else:   
        return redirect('view_students')

@login_required
def coordinator_dashboard(request, section=None):
    context = {}

    if section == 'add-student':
        context['section'] = 'coordinator_sections/add_students.html'
        
    elif section == 'manage-students':
        # Get search query and sort order from the request
        search_query = request.GET.get('search', '')
        sort_order = request.GET.get('sort', '')

        # Filter students based on the search query
        students_list = StudentProfile.objects.all()
        if search_query:
            students_list = students_list.filter(
                Q(student_name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(department__icontains=search_query)
            )

        # Sort students based on the sort order
        if sort_order == 'name':
            students_list = students_list.order_by('student_name')
        elif sort_order == 'email':
            students_list = students_list.order_by('email')
        elif sort_order == 'department':
            students_list = students_list.order_by('department')

        # Paginate the filtered and sorted results
        paginator = Paginator(students_list, 9)  # Show 9 students per page
        page_number = request.GET.get('page')
        students_page = paginator.get_page(page_number)

        context['students'] = students_page
        context['search_query'] = search_query
        context['sort_order'] = sort_order
        context['section'] = 'coordinator_sections/manage_students.html'

    # Announcement section
    elif section == 'announcements':
        if request.method == 'POST':
            title = request.POST.get('title')
            message = request.POST.get('message')

            if not title or not message:
                messages.error(request, 'Both title and message are required.')
            else:
                # Create and save the announcement
                announcement = Announcement(
                    title=title,
                    message=message,
                    posted_by=get_object_or_404(CoordinatorProfile, email=request.session['username'])
                )
                announcement.save()
                messages.success(request, 'Announcement posted successfully!')
                return redirect('coordinator_dashboard_section', section='announcements')

        # Fetch announcements posted by the current coordinator
        my_announcements = Announcement.objects.filter(posted_by__email=request.session['username']).order_by('-created_at')
        context['my_announcements'] = my_announcements
        context['section'] = 'coordinator_sections/announcements.html'

    # Section for viewing all announcements (with search functionality)
    elif section == 'all-announcements':
        search_query = request.GET.get('search', '')

        # Fetch and filter all announcements
        announcements = Announcement.objects.all()
        if search_query:
            announcements = announcements.filter(
                Q(title__icontains=search_query) |
                Q(message__icontains=search_query)
            )

        context['announcements'] = announcements.order_by('-created_at')
        context['search_query'] = search_query
        context['section'] = 'coordinator_sections/all_announcements.html'

        email = request.session['username']
        if CoordinatorProfile.objects.filter(email=email).exists():
            return render(request, 'coordinator_dashboard.html', context)
        else:
            return render(request, 'student_dashboard.html', context)
    
    elif section == 'discussion':
        msgs = DiscussionMessage.objects.all().order_by('-timestamp')

        if request.method == 'POST':
            content = request.POST.get('message')
            username = request.session.get('username')

            if content and username:
                DiscussionMessage.objects.create(username=username, content=content)
                return redirect('coordinator_dashboard_section', section='discussion')

        context['msgs'] = msgs
        context['section'] = 'student_sections/discussion.html'
    
    elif section == 'placement-details':
        search_query = request.GET.get('search', '')
        search_query2 = request.GET.get('search_student', '')

        # Job Drives filtering based on search
        job_drives = JobDrive.objects.filter(company__icontains=search_query)
        context['job_drives'] = job_drives

        job_drive_id = request.GET.get('job_drive_id')
        if job_drive_id:
            job_drive = get_object_or_404(JobDrive, pk=job_drive_id)

            # Students filtering based on search (search by student_id or full_name)
            applied_jobs = AppliedJob.objects.filter(
                job_drive=job_drive
            ).filter(
                Q(student__full_name__icontains=search_query2) |
                Q(student__student_id__icontains=search_query2)
            )

            context['selected_job_drive'] = job_drive
            context['applied_jobs'] = applied_jobs

            # Check if the user wants to generate the PDF
            if 'generate_report' in request.GET:
                buffer = generate_student_report(job_drive,applied_jobs)
                response = HttpResponse(buffer, content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="applied students {job_drive.company}.pdf"'
                return response

            # Bulk status update when "Change All" button is clicked
            if request.method == 'POST':
                for applied_job in applied_jobs:
                    new_status = request.POST.get(f'status_{applied_job.id}')
                    if new_status in dict(AppliedJob.STATUS_CHOICES):
                        applied_job.status = new_status
                        applied_job.save()

                        if new_status == 'selected':
                            applied_job.student.placed_status = True
                            if not applied_job.student.job_offers:
                                applied_job.student.job_offers = applied_job.job_drive.company
                            else:
                                selected_for_jobs = applied_job.student.job_offers.split(',')
                                selected_for_jobs.append(applied_job.job_drive.company)
                                applied_job.student.job_offers = ','.join(selected_for_jobs)
                            applied_job.student.save()
                        else:
                            applied_job.student.placed_status = False
                            applied_job.student.save()

                return redirect('coordinator_dashboard_section', section='placement-details')

        context['section'] = 'coordinator_sections/placement_details.html'


    elif section == 'job-openings':
        # Get search query and sort order from the request
        search_query = request.GET.get('search', '')
        sort_order = request.GET.get('sort', '')

        # Filter jobs based on the search query
        jobs_list = JobDrive.objects.all()
        if search_query:
            jobs_list = jobs_list.filter(
                Q(title__icontains=search_query) |
                Q(company__icontains=search_query) |
                Q(location__icontains=search_query)
            )

        # Sort jobs based on the sort order
        if sort_order == 'title':
            jobs_list = jobs_list.order_by('title')
        elif sort_order == 'company':
            jobs_list = jobs_list.order_by('company')
        elif sort_order == 'date':
            jobs_list = jobs_list.order_by('-created_at')

        # Paginate the filtered and sorted results
        paginator = Paginator(jobs_list, 9)  # Show 9 job drives per page
        page_number = request.GET.get('page')
        jobs_page = paginator.get_page(page_number)

        context['jobs'] = jobs_page
        context['search_query'] = search_query
        context['sort_order'] = sort_order
        context['section'] = 'coordinator_sections/job_openings.html'

    elif section == 'manage-profile':
        coordinator = get_object_or_404(CoordinatorProfile, email=request.session['username'])
        context['coordinator'] = coordinator
        context['section'] = 'coordinator_sections/manage_profile.html'
    else:
        coordinator_count = CoordinatorProfile.objects.count()
        student_count = StudentProfile.objects.count()
        placed_students_count = StudentInformation.objects.filter(placed_status=True).count()
        unplaced_students_count = StudentInformation.objects.filter(placed_status=False).count()

        context = {
            'coordinator_count': coordinator_count,
            'student_count': student_count,
            'placed_students_count': placed_students_count,
            'unplaced_students_count': unplaced_students_count,
        }

        context['section'] = 'coordinator_sections/default.html'

    return render(request, 'coordinator_dashboard.html', context)

def update_student_status(request, applied_job_id):
    applied_job = get_object_or_404(AppliedJob, pk=applied_job_id)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(AppliedJob.STATUS_CHOICES):
            applied_job.status = new_status
            applied_job.save()

            # Update placed status if student is selected
            if new_status == 'selected':
                applied_job.student.placed_status = True
                applied_job.student.save()

    return redirect('coordinator_dashboard_section', section='placement-details')

@login_required
def add_job_drive(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        company = request.POST.get('company')
        location = request.POST.get('location')
        job_description = request.POST.get('job_description')
        skills_required = request.POST.get('skills_required')
        salary = request.POST.get('salary')
        vacancies = request.POST.get('vacancies')
        last_date_to_apply = request.POST.get('last_date_to_apply')
        tentative_drive_date = request.POST.get('tentative_drive_date')

        JobDrive.objects.create(
            title=title,
            company=company,
            location=location,
            job_description=job_description,
            skills_required=skills_required,
            salary=salary,
            vacancies=vacancies,
            last_date_to_apply=last_date_to_apply,
            tentative_drive_date=tentative_drive_date
        )
        email = request.session['username']
        if CoordinatorProfile.objects.filter(email=email).exists():
            return redirect('coordinator_dashboard_section', section='job-openings')
        else:
            return redirect('admin_dashboard_section', section='job-openings')

    return render(request, 'add_job_drive.html')

def edit_job(request, job_id):
    job = get_object_or_404(JobDrive, pk=job_id)
    
    if request.method == "POST":
        job.title = request.POST.get('title')
        job.company = request.POST.get('company')
        job.location = request.POST.get('location')
        job.last_date_to_apply = request.POST.get('last_date_to_apply')
        job.tentative_drive_date = request.POST.get('tentative_drive_date')
        job.job_description = request.POST.get('description')
        job.skills_required = request.POST.get('requirements')
        job.vacancies = request.POST.get('vacancies')
        
        job.save()
        email = request.session['username']
        if CoordinatorProfile.objects.filter(email=email).exists():
            return redirect('coordinator_dashboard_section', section='job-openings')
        else:
            return redirect('admin_dashboard_section', section='job-openings')

    return render(request, 'edit_job.html', {'job': job})

def delete_job(request, job_id):
    job = get_object_or_404(JobDrive, pk=job_id)
    job.delete()
    email = request.session['username']
    if CoordinatorProfile.objects.filter(email=email).exists():
        return redirect('coordinator_dashboard_section', section='job-openings')
    else:
        return redirect('admin_dashboard_section', section='job-openings')

def view_jobs(request):
    jobs = JobDrive.objects.all()  # Or apply filters as needed
    return render(request, 'view_jobs.html', {'jobs': jobs})

@login_required
def edit_announcement(request, announcement_id):
    announcement = get_object_or_404(Announcement, id=announcement_id, posted_by__email=request.session['username'])

    if request.method == 'POST':
        title = request.POST.get('title')
        message = request.POST.get('message')

        if not title or not message:
            messages.error(request, 'Both title and message are required.')
        else:
            announcement.title = title
            announcement.message = message
            announcement.save()
            messages.success(request, 'Announcement updated successfully!')
            return redirect('coordinator_dashboard_section', section='announcements')

    context = {
        'announcement': announcement,
    }
    return render(request, 'edit_announcement.html', context)


@login_required
def delete_announcement(request, announcement_id):
    announcement = get_object_or_404(Announcement, id=announcement_id, posted_by__email=request.session['username'])
    announcement.delete()
    messages.success(request, 'Announcement deleted successfully!')
    return redirect('coordinator_dashboard_section', section='announcements')

def apply_job(request, job_id):
    if request.method == 'POST':
        student_info = get_object_or_404(StudentInformation, college_email=request.session['username'])
        job_drive = get_object_or_404(JobDrive, id=job_id)
        
        # Check if the student has already applied
        if AppliedJob.objects.filter(student=student_info, job_drive=job_drive).exists():
            messages.warning(request, 'You have already applied for this job.')
        else:
            # Apply for the job
            AppliedJob.objects.create(student=student_info, job_drive=job_drive)
            messages.success(request, 'Successfully applied for the job.')

        return redirect('student_dashboard_section', section='view-placements')

@login_required
def widrow_application(request,job_id):
    job = get_object_or_404(AppliedJob,id=job_id)
    # remove applied job
    job.delete()
    messages.success(request, 'Application withdrawn successfully.')
    return redirect('student_dashboard_section', section='applied-jobs')

def generate_student_report(job_drive, applied_jobs):
    buffer = BytesIO()

    # Set up PDF document with custom margins
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=40, rightMargin=40, topMargin=50, bottomMargin=50)
    elements = []

    # Define basic styles and custom paragraph styles
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'TitleStyle',
        fontSize=18,
        leading=22,
        alignment=1,  # Center alignment
        textColor=colors.HexColor('#3a3a3a'),
        spaceAfter=20
    )

    header_style = ParagraphStyle(
        'HeaderStyle',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#003366'),
        spaceBefore=12,
        spaceAfter=6
    )

    info_style = ParagraphStyle(
        'InfoStyle',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#333333'),
        spaceAfter=5
    )

    # Add title with company name
    title = Paragraph(f"Students Applied for {job_drive.company}", title_style)
    elements.append(title)

    # Add a table for better formatting of each student's details
    for applied_job in applied_jobs:
        student_info = applied_job.student

        # Student Info Block Title
        student_title = Paragraph(f"<b>{student_info.full_name}</b> ({student_info.student_id})", header_style)
        elements.append(student_title)

        # Create student information as a table for better alignment
        data = [
            [Paragraph("<b>Details</b>", info_style), Paragraph('<b>Student Information</b>', info_style)],
            [Paragraph("<b>Mobile:</b>", info_style), Paragraph(student_info.phone_number or 'NA', info_style)],
            [Paragraph("<b>Email:</b>", info_style), Paragraph(student_info.student_profile.email or 'NA', info_style)],
            [Paragraph("<b>College Email:</b>", info_style), Paragraph(student_info.college_email, info_style)],
            [Paragraph("<b>Address:</b>", info_style), Paragraph(student_info.current_address or student_info.permanent_address or 'NA', info_style)],
            [Paragraph("<b>Department:</b>", info_style), Paragraph(student_info.department, info_style)],
            [Paragraph("<b>Placed Status:</b>", info_style), Paragraph('Placed' if student_info.placed_status else 'Not Placed', info_style)]
        ]

        # Table with some custom styles
        table = Table(data, colWidths=[1.5 * inch, 4.5 * inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f0f0f0')),  # Light background for labels
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#000000')),    # Dark text color
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),                          # Left alignment for text
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),                   # Font for the entire table
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e0e0')),   # Light grid color for table
        ]))

        elements.append(table)
        elements.append(Spacer(1, 12))  # Space after each student's info
    
    # Build the PDF document
    doc.build(elements)

    # Return the generated PDF
    buffer.seek(0)
    return buffer