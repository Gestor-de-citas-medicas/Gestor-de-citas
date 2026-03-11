from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction

from .models import DoctorSchedule, ScheduleException, DoctorProfile

User = get_user_model()


class DoctorScheduleForm(forms.ModelForm):

    class Meta:
        model = DoctorSchedule
        fields = ["day_number", "start_time", "end_time"]
        widgets = {
            "day_number": forms.Select(attrs={
                "class": "form-control"
            }),
            "start_time": forms.TimeInput(attrs={
                "type": "time",
                "class": "form-control"
            }),
            "end_time": forms.TimeInput(attrs={
                "type": "time",
                "class": "form-control"
            }),
        }

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start_time")
        end = cleaned.get("end_time")

        if start and end and start >= end:
            raise forms.ValidationError(
                "La hora de fin debe ser mayor a la hora de inicio."
            )
        return cleaned


class ScheduleExceptionForm(forms.ModelForm):

    class Meta:
        model = ScheduleException
        fields = ["date", "start_time", "end_time", "type", "reason"]
        widgets = {
            "date": forms.DateInput(attrs={
                "type": "date",
                "class": "form-control"
            }),
            "start_time": forms.TimeInput(attrs={
                "type": "time",
                "class": "form-control"
            }),
            "end_time": forms.TimeInput(attrs={
                "type": "time",
                "class": "form-control"
            }),
            "type": forms.Select(attrs={
                "class": "form-control"
            }),
            "reason": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ej: Reunión administrativa, vacaciones..."
            }),
        }

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start_time")
        end = cleaned.get("end_time")
        date = cleaned.get("date")

        if start and end and start >= end:
            raise forms.ValidationError(
                "La hora de fin debe ser mayor a la hora de inicio."
            )

        if date:
            from datetime import date as today_date
            if date < today_date.today():
                raise forms.ValidationError(
                    "No puedes crear bloques en fechas pasadas."
                )

        return cleaned


class PatientRegisterForm(UserCreationForm):
    first_name = forms.CharField(max_length=150, label="Nombre")
    last_name = forms.CharField(max_length=150, label="Apellido")
    email = forms.EmailField(label="Correo electrónico")

    class Meta:
        model = User
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "password1",
            "password2",
        )

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Ya existe un usuario con este correo.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Roles.PATIENT
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.email = self.cleaned_data["email"]

        if commit:
            user.save()

        return user


class DoctorRegisterForm(UserCreationForm):
    first_name = forms.CharField(max_length=150, label="Nombre")
    last_name = forms.CharField(max_length=150, label="Apellido")
    email = forms.EmailField(label="Correo electrónico")
    specialty = forms.ChoiceField(
        label="Especialidad",
        choices=DoctorProfile.Specialty.choices
    )
    license_number = forms.CharField(
        max_length=50,
        label="Registro médico / Licencia"
    )
    phone = forms.CharField(
        max_length=20,
        label="Teléfono",
        required=False
    )
    bio = forms.CharField(
        label="Descripción profesional",
        required=False,
        widget=forms.Textarea(attrs={"rows": 4})
    )
    avatar = forms.ImageField(
        label="Foto de perfil",
        required=False
    )

    class Meta:
        model = User
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "password1",
            "password2",
        )

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Ya existe un usuario con este correo.")
        return email

    def clean_license_number(self):
        license_number = self.cleaned_data["license_number"].strip()
        if DoctorProfile.objects.filter(license_number__iexact=license_number).exists():
            raise forms.ValidationError("Ese número de licencia ya está registrado.")
        return license_number

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Roles.DOCTOR
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.email = self.cleaned_data["email"]

        if commit:
            user.save()

            DoctorProfile.objects.create(
                user=user,
                full_name=f"{user.first_name} {user.last_name}".strip(),
                specialty=self.cleaned_data["specialty"],
                license_number=self.cleaned_data["license_number"],
                phone=self.cleaned_data.get("phone", ""),
                bio=self.cleaned_data.get("bio", ""),
                avatar=self.cleaned_data.get("avatar"),
            )

        return user