from django import forms
from .models import DoctorSchedule, ScheduleException


class DoctorScheduleForm(forms.ModelForm):

    class Meta:
        model  = DoctorSchedule
        fields = ["day_number", "start_time", "end_time"]
        widgets = {
            "day_number": forms.Select(attrs={
                "class": "form-control"
            }),
            "start_time": forms.TimeInput(attrs={
                "type":  "time",
                "class": "form-control"
            }),
            "end_time": forms.TimeInput(attrs={
                "type":  "time",
                "class": "form-control"
            }),
        }

    def clean(self):
        cleaned = super().clean()
        start   = cleaned.get("start_time")
        end     = cleaned.get("end_time")

        if start and end and start >= end:
            raise forms.ValidationError(
                "La hora de fin debe ser mayor a la hora de inicio."
            )
        return cleaned


class ScheduleExceptionForm(forms.ModelForm):

    class Meta:
        model  = ScheduleException
        fields = ["date", "start_time", "end_time", "type", "reason"]
        widgets = {
            "date": forms.DateInput(attrs={
                "type":  "date",
                "class": "form-control"
            }),
            "start_time": forms.TimeInput(attrs={
                "type":  "time",
                "class": "form-control"
            }),
            "end_time": forms.TimeInput(attrs={
                "type":  "time",
                "class": "form-control"
            }),
            "type": forms.Select(attrs={
                "class": "form-control"
            }),
            "reason": forms.TextInput(attrs={
                "class":       "form-control",
                "placeholder": "Ej: Reunión administrativa, vacaciones..."
            }),
        }

    def clean(self):
        cleaned = super().clean()
        start   = cleaned.get("start_time")
        end     = cleaned.get("end_time")
        date    = cleaned.get("date")

        if start and end and start >= end:
            raise forms.ValidationError(
                "La hora de fin debe ser mayor a la hora de inicio."
            )

        # No permitir excepciones en fechas pasadas
        if date:
            from datetime import date as today_date
            if date < today_date.today():
                raise forms.ValidationError(
                    "No puedes crear bloques en fechas pasadas."
                )

        return cleaned