from django import forms
from django.contrib.auth import get_user_model
from .models import Appointment

User = get_user_model()


class AppointmentForm(forms.ModelForm):

    class Meta:
        model  = Appointment
        fields = ["doctor", "date", "start_time", "end_time", "reason"]
        widgets = {
            "doctor":     forms.Select(attrs={"class": "field-input"}),
            "date":       forms.DateInput(attrs={"type": "date", "class": "field-input"}),
            "start_time": forms.TimeInput(attrs={"type": "time", "class": "field-input"}),
            "end_time":   forms.TimeInput(attrs={"type": "time", "class": "field-input"}),
            "reason":     forms.Textarea(attrs={"rows": 3, "class": "field-input", "placeholder": "Describe your reason for the visit..."}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show users with DOCTOR role in the dropdown
        self.fields["doctor"].queryset = User.objects.filter(role="DOCTOR")
        self.fields["doctor"].label    = "Doctor"
        self.fields["date"].label      = "Date"
        self.fields["start_time"].label = "Start time"
        self.fields["end_time"].label   = "End time"
        self.fields["reason"].label     = "Reason for visit"
        self.fields["reason"].required  = False

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start_time")
        end   = cleaned.get("end_time")
        if start and end and end <= start:
            raise forms.ValidationError("End time must be after start time.")
        return cleaned
