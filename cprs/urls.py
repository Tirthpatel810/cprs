from django.contrib import admin
from django.urls import path
import cprs_app.views as v1
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('django-administration/', admin.site.urls),
    path('', v1.login, name='login_form'),

    # Forgot password
    path('forgot-password/', v1.forgot_password, name='forgot_password'),
    path('verify-reset-code/', v1.verify_reset_code, name='verify_reset_code'),
    path('reset-password/<int:user_id>/', v1.reset_password, name='reset_password'),

    # Admin
    path('admin-dashboard/', v1.admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/<str:section>/', v1.admin_dashboard, name='admin_dashboard_section'),
    path('create-coordinator/', v1.create_coordinator, name='create_coordinator'),
    path('view-coordinators/', v1.admin_dashboard, {'section': 'view-coordinators'}, name='view_coordinators'),
    path('create-student-accounts/', v1.create_student, name='create_student'),
    path('students/', v1.admin_dashboard, {'section': 'view-students'}, name='view_students'),
    path('edit-student/<str:pk>/', v1.edit_student, name='edit_student'),
    path('delete-student/<str:pk>/', v1.delete_student, name='delete_student'),
    path('student/<str:pk>/', v1.view_student_details, name='view_student_details'),
    path('edit-coordinator/<int:pk>/', v1.edit_coordinator, name='edit_coordinator'),
    path('delete-coordinator/<int:id>/', v1.delete_coordinator, name='delete_coordinator'),

    # Coordinators
    path('coordinator-dashboard/', v1.coordinator_dashboard, name='coordinator_dashboard'),
    path('coordinator-dashboard/<str:section>/', v1.coordinator_dashboard, name='coordinator_dashboard_section'),
    path('add-job-drive/', v1.add_job_drive, name='add_job_drive'),
    path('jobs/', v1.view_jobs, name='view_jobs'),
    path('jobs/edit/<int:job_id>/', v1.edit_job, name='edit_job'),
    path('jobs/delete/<int:job_id>/', v1.delete_job, name='delete_job'),

    path('update-status/<int:applied_job_id>/', v1.update_student_status, name='update_student_status'),

    # Edit and delete announcements
    path('announcement/edit/<int:announcement_id>/', v1.edit_announcement, name='edit_announcement'),
    path('announcement/delete/<int:announcement_id>/', v1.delete_announcement, name='delete_announcement'),

    # All announcements
    # path('dashboard/all-announcements/', v1.coordinator_dashboard, {'section': 'all-announcements'}, name='all_announcements'),

    # Students
    path('student-dashboard/', v1.student_dashboard, name='student_dashboard'),
    path('student-dashboard/<str:section>/', v1.student_dashboard, name='student_dashboard_section'),
    path('apply-job/<int:job_id>/', v1.apply_job, name='apply_job'),
    path('widrow_application/<int:job_id>/', v1.widrow_application, name='widrow-application'),
    # path('discussion/', v, name='discussion'),

    path('logout/', v1.logout, name='logout'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
