from django import forms
from .models import DoctorSchedule

class DoctorScheduleForm(forms.ModelForm):
    class Meta:
        model = DoctorSchedule
        fields = ['day_number', 'start_time', 'end_time']
