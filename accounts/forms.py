from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction

from .models import DoctorSchedule, ScheduleException, DoctorProfile

User = get_user_model()


# ── Schedule / Exception forms (unchanged) ────────────────────────────────────

class DoctorScheduleForm(forms.ModelForm):

    class Meta:
        model = DoctorSchedule
        fields = ["day_number", "start_time", "end_time"]
        widgets = {
            "day_number": forms.Select(attrs={"class": "form-control"}),
            "start_time": forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
            "end_time":   forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
        }

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start_time")
        end   = cleaned.get("end_time")
        if start and end and start >= end:
            raise forms.ValidationError("End time must be greater than start time.")
        return cleaned


class ScheduleExceptionForm(forms.ModelForm):

    class Meta:
        model  = ScheduleException
        fields = ["date", "start_time", "end_time", "type", "reason"]
        widgets = {
            "date":       forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "start_time": forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
            "end_time":   forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
            "type":       forms.Select(attrs={"class": "form-control"}),
            "reason":     forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "E.g: Administrative meeting, vacation..."
            }),
        }

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start_time")
        end   = cleaned.get("end_time")
        date  = cleaned.get("date")

        if start and end and start >= end:
            raise forms.ValidationError("End time must be greater than start time.")

        if date:
            from datetime import date as today_date
            if date < today_date.today():
                raise forms.ValidationError("You cannot create blocks in past dates.")

        return cleaned


# ── Registration forms (unchanged) ────────────────────────────────────────────

class PatientRegisterForm(UserCreationForm):
    first_name = forms.CharField(max_length=150, label="First Name")
    last_name  = forms.CharField(max_length=150, label="Last Name")
    email      = forms.EmailField(label="Email Address")

    class Meta:
        model  = User
        fields = ("username", "first_name", "last_name", "email", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role       = User.Roles.PATIENT
        user.first_name = self.cleaned_data["first_name"]
        user.last_name  = self.cleaned_data["last_name"]
        user.email      = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class DoctorRegisterForm(UserCreationForm):
    first_name     = forms.CharField(max_length=150, label="First Name")
    last_name      = forms.CharField(max_length=150, label="Last Name")
    email          = forms.EmailField(label="Email Address")
    specialty      = forms.ChoiceField(label="Specialty", choices=DoctorProfile.Specialty.choices)
    license_number = forms.CharField(max_length=50, label="Medical License / Registration")
    phone          = forms.CharField(max_length=20, label="Phone", required=False)
    bio            = forms.CharField(
        label="Professional Bio",
        required=False,
        widget=forms.Textarea(attrs={"rows": 4}),
    )
    avatar = forms.ImageField(label="Profile Photo", required=False)

    class Meta:
        model  = User
        fields = ("username", "first_name", "last_name", "email", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email

    def clean_license_number(self):
        license_number = self.cleaned_data["license_number"].strip()
        if DoctorProfile.objects.filter(license_number__iexact=license_number).exists():
            raise forms.ValidationError("That license number is already registered.")
        return license_number

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role       = User.Roles.DOCTOR
        user.first_name = self.cleaned_data["first_name"]
        user.last_name  = self.cleaned_data["last_name"]
        user.email      = self.cleaned_data["email"]
        if commit:
            user.save()
            DoctorProfile.objects.create(
                user           = user,
                full_name      = f"{user.first_name} {user.last_name}".strip(),
                specialty      = self.cleaned_data["specialty"],
                license_number = self.cleaned_data["license_number"],
                phone          = self.cleaned_data.get("phone", ""),
                bio            = self.cleaned_data.get("bio", ""),
                avatar         = self.cleaned_data.get("avatar"),
            )
        return user


# ── Profile-update forms (NEW) ─────────────────────────────────────────────────

class PatientProfileUpdateForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150, label="First Name")
    last_name  = forms.CharField(max_length=150, label="Last Name")
    email      = forms.EmailField(label="Email Address")

    class Meta:
        model  = User
        fields = ("first_name", "last_name", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({"class": "input-control"})

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        qs = User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email


class DoctorProfileUpdateForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150, label="First Name")
    last_name  = forms.CharField(max_length=150, label="Last Name")
    email      = forms.EmailField(label="Email Address")
    specialty  = forms.ChoiceField(label="Specialty", choices=DoctorProfile.Specialty.choices)
    phone      = forms.CharField(max_length=20, label="Phone", required=False)
    bio        = forms.CharField(
        label="Professional Bio",
        required=False,
        widget=forms.Textarea(attrs={"rows": 4}),
    )
    avatar = forms.ImageField(label="Profile Photo", required=False)

    class Meta:
        model  = User
        fields = ("first_name", "last_name", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and hasattr(self.instance, "doctor_profile"):
            profile = self.instance.doctor_profile
            self.fields["specialty"].initial = profile.specialty
            self.fields["phone"].initial     = profile.phone
            self.fields["bio"].initial       = profile.bio
        for field in self.fields.values():
            field.widget.attrs.update({"class": "input-control"})

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        qs = User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email

    @transaction.atomic
    def save(self, commit=True):
        user            = super().save(commit=False)
        user.first_name = self.cleaned_data["first_name"]
        user.last_name  = self.cleaned_data["last_name"]
        user.email      = self.cleaned_data["email"]
        if commit:
            user.save()
            profile           = user.doctor_profile
            profile.full_name = f"{user.first_name} {user.last_name}".strip()
            profile.specialty = self.cleaned_data["specialty"]
            profile.phone     = self.cleaned_data.get("phone", "")
            profile.bio       = self.cleaned_data.get("bio", "")
            if self.cleaned_data.get("avatar"):
                profile.avatar = self.cleaned_data["avatar"]
            profile.save()
        return user
