from django import forms
from django.contrib.auth import get_user_model
from .models import Appointment

User = get_user_model()


class AppointmentForm(forms.ModelForm):

    class Meta:
        model  = Appointment
        fields = ["doctor", "date", "start_time", "reason"]
        widgets = {
            "doctor":     forms.Select(attrs={"class": "field-input"}),
            "date":       forms.DateInput(attrs={"type": "date", "class": "field-input"}),
            "start_time": forms.TimeInput(attrs={"type": "time", "class": "field-input"}),
            "reason":     forms.Textarea(attrs={"rows": 3, "class": "field-input", "placeholder": "Describe your reason for the visit..."}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show users with DOCTOR role in the dropdown
        self.fields["doctor"].queryset = User.objects.filter(role="DOCTOR")
        self.fields["doctor"].label    = "Doctor"
        self.fields["date"].label      = "Date"
        self.fields["start_time"].label = "Appointment time"
        self.fields["reason"].label     = "Reason for visit"
        self.fields["reason"].required  = False

    def clean(self):
        cleaned = super().clean()
        # La hora de fin se calculará automáticamente (1 hora después del inicio)
        return cleaned
