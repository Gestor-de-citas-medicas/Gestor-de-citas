from django import forms
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta, date as date_type

from .models import Appointment, AppointmentReview
from accounts.models import DoctorSchedule

User = get_user_model()


class AppointmentForm(forms.ModelForm):

    class Meta:
        model = Appointment
        fields = ["doctor", "date", "start_time", "reason"]
        widgets = {
            "doctor": forms.Select(attrs={"class": "field-input"}),
            "date": forms.DateInput(attrs={"type": "date", "class": "field-input"}),
            "start_time": forms.Select(attrs={"class": "field-input"}),  # 🔥 CAMBIO
            "reason": forms.Textarea(attrs={"rows": 3, "class": "field-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # doctores
        self.fields["doctor"].queryset = User.objects.filter(role="DOCTOR")

        # labels
        self.fields["doctor"].label = "Doctor"
        self.fields["date"].label = "Date"
        self.fields["start_time"].label = "Appointment time"
        self.fields["reason"].label = "Reason for visit"
        self.fields["reason"].required = False

        # 🔥 VACÍO POR DEFECTO
        self.fields["start_time"].choices = []

        # 🔥 GENERAR HORAS SI YA HAY DATA
        if "doctor" in self.data and "date" in self.data:
            try:
                doctor_id = int(self.data.get("doctor"))
                selected_date = datetime.strptime(
                    self.data.get("date"), "%Y-%m-%d"
                ).date()

                # 🔥 FIX: isoweekday() → Monday=1 … Sunday=7, matches DoctorSchedule model
                weekday = selected_date.isoweekday()

                schedules = DoctorSchedule.objects.filter(
                    doctor_id=doctor_id,
                    day_number=weekday,
                    is_active=True
                )

                choices = []
                now = datetime.now()
                is_today = (selected_date == date_type.today())

                for s in schedules:
                    hora = datetime.combine(selected_date, s.start_time).replace(minute=0)

                    while hora.time() < s.end_time:
                        # 🔥 FIX: skip past slots when booking for today
                        if not is_today or hora > now:
                            h = hora.time().strftime("%H:%M")
                            choices.append((h, h))
                        hora += timedelta(hours=1)

                self.fields["start_time"].choices = choices

            except Exception as e:
                print("ERROR HORAS:", e)

    def clean_date(self):
        d = self.cleaned_data.get("date")
        if d and d < datetime.now().date():
            raise forms.ValidationError("You cannot book appointments on a past date.")
        return d

    def clean(self):
        cleaned_data = super().clean()
        d = cleaned_data.get("date")
        start_time = cleaned_data.get("start_time")
        if d and start_time:
            if datetime.combine(d, start_time) < datetime.now():
                raise forms.ValidationError("You cannot book appointments at a past time.")
        return cleaned_data


class AppointmentReviewForm(forms.ModelForm):

    class Meta:
        model = AppointmentReview
        fields = ["rating", "comment"]
        widgets = {
            "rating": forms.HiddenInput(),
            "comment": forms.Textarea(attrs={
                "rows": 4,
                "class": "field-input",
                "placeholder": "Share your experience..."
            }),
        }

    def clean_rating(self):
        rating = self.cleaned_data.get("rating")
        if rating is None or rating < 1 or rating > 5:
            raise forms.ValidationError("Select between 1 and 5 stars")
        return rating