from django import forms
from .models import CoordinatorProfile

class CoordinatorForm(forms.ModelForm):
    class Meta:
        model = CoordinatorProfile
        fields = ['coordinator_name', 'email', 'department', 'mobile_number', 'address', 'date_of_birth', 'gender', 'hire_date', 'profile_photo']
