from django import forms
from django.contrib.auth import get_user_model
from .models import Appointment, AppointmentReview

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


class AppointmentReviewForm(forms.ModelForm):
    """Form for patients to leave a post-appointment review."""

    class Meta:
        model = AppointmentReview
        fields = ["rating", "comment"]
        widgets = {
            "rating": forms.HiddenInput(),
            "comment": forms.Textarea(attrs={
                "rows": 4,
                "class": "field-input",
                "placeholder": "Share your experience with this doctor (optional)...",
            }),
        }
        labels = {
            "rating": "Rating",
            "comment": "Your Review",
        }

    def clean_rating(self):
        rating = self.cleaned_data.get("rating")
        if rating is None or rating < 1 or rating > 5:
            raise forms.ValidationError("Please select a rating between 1 and 5 stars.")
        return rating
