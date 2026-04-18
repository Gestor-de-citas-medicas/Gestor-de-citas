from django import forms
from django.contrib.auth import get_user_model
from django.db import transaction
from django.contrib.auth.forms import UserCreationForm
from .models import DoctorProfile

User = get_user_model()


# =========================
# 🔥 PATIENT REGISTER (RESTAURADO)
# =========================
class PatientRegisterForm(UserCreationForm):
    first_name = forms.CharField(max_length=150)
    last_name  = forms.CharField(max_length=150)
    email      = forms.EmailField()

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)

        user.first_name = self.cleaned_data["first_name"]
        user.last_name  = self.cleaned_data["last_name"]
        user.email      = self.cleaned_data["email"]
        user.role       = "PATIENT"

        if commit:
            user.save()

        return user


# =========================
# 🔥 DOCTOR REGISTER (RESTAURADO COMPLETO)
# =========================
class DoctorRegisterForm(UserCreationForm):
    first_name = forms.CharField(max_length=150)
    last_name  = forms.CharField(max_length=150)
    email      = forms.EmailField()

    specialty  = forms.ChoiceField(choices=DoctorProfile.Specialty.choices)
    phone      = forms.CharField(required=False)
    license    = forms.CharField(required=False)
    cv         = forms.FileField(required=False)

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)

        user.first_name = self.cleaned_data["first_name"]
        user.last_name  = self.cleaned_data["last_name"]
        user.email      = self.cleaned_data["email"]
        user.role       = "DOCTOR"

        if commit:
            user.save()

            profile = user.doctor_profile
            profile.full_name = f"{user.first_name} {user.last_name}"
            profile.specialty = self.cleaned_data["specialty"]
            profile.phone     = self.cleaned_data.get("phone")
            profile.license   = self.cleaned_data.get("license")

            if self.cleaned_data.get("cv"):
                profile.cv = self.cleaned_data["cv"]

            profile.save()

        return user


# =========================
# 🔥 PATIENT PROFILE
# =========================
class PatientProfileUpdateForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150)
    last_name  = forms.CharField(max_length=150)
    email      = forms.EmailField()

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        for f in self.fields.values():
            f.widget.attrs.update({"class": "input-control"})


# =========================
# 🔥 DOCTOR PROFILE
# =========================
class DoctorProfileUpdateForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150)
    last_name  = forms.CharField(max_length=150)
    email      = forms.EmailField()
    specialty  = forms.ChoiceField(choices=DoctorProfile.Specialty.choices)
    phone      = forms.CharField(required=False)
    bio        = forms.CharField(required=False, widget=forms.Textarea)
    avatar     = forms.ImageField(required=False)

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        if hasattr(self.instance, "doctor_profile"):
            profile = self.instance.doctor_profile
            self.fields["specialty"].initial = profile.specialty
            self.fields["phone"].initial     = profile.phone
            self.fields["bio"].initial       = profile.bio

        for f in self.fields.values():
            f.widget.attrs.update({"class": "input-control"})

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)

        if commit:
            user.save()

            profile = user.doctor_profile
            profile.full_name = f"{user.first_name} {user.last_name}"
            profile.specialty = self.cleaned_data["specialty"]
            profile.phone     = self.cleaned_data.get("phone")
            profile.bio       = self.cleaned_data.get("bio")

            if self.cleaned_data.get("avatar"):
                profile.avatar = self.cleaned_data["avatar"]

            profile.save()

        return user