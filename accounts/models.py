from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError


class User(AbstractUser):
    class Roles(models.TextChoices):
        PATIENT = "PATIENT", "Patient"
        DOCTOR  = "DOCTOR",  "Doctor"
        ADMIN   = "ADMIN",   "Admin"

    role = models.CharField(
        max_length=20,
        choices=Roles.choices,
        default=Roles.PATIENT
    )

    def clean(self):
        if self.role == self.Roles.DOCTOR and not self.email:
            raise ValidationError("A doctor must have an email address.")

    def __str__(self):
        return f"{self.username} ({self.role})"


class DoctorSchedule(models.Model):
    DAYS_OF_WEEK = [
        (0, "Sunday"),
        (1, "Monday"),
        (2, "Tuesday"),
        (3, "Wednesday"),
        (4, "Thursday"),
        (5, "Friday"),
        (6, "Saturday"),
    ]

    doctor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="schedules",
        limit_choices_to={"role": User.Roles.DOCTOR}
    )
    day_number = models.IntegerField(choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time   = models.TimeField()
    is_active  = models.BooleanField(default=True)

    class Meta:
        ordering = ["day_number", "start_time"]
        constraints = [
            models.UniqueConstraint(
                fields=["doctor", "day_number", "start_time"],
                name="unique_schedule_slot"
            )
        ]

    def clean(self):
        if self.start_time and self.end_time:
            if self.start_time >= self.end_time:
                raise ValidationError("End time must be greater than start time.")

        overlapping = DoctorSchedule.objects.filter(
            doctor=self.doctor,
            day_number=self.day_number,
            is_active=True,
            start_time__lt=self.end_time,
            end_time__gt=self.start_time,
        ).exclude(pk=self.pk)

        if overlapping.exists():
            raise ValidationError("This schedule overlaps with an existing one.")

    def __str__(self):
        status = "✓" if self.is_active else "✗"
        return f"[{status}] {self.doctor.username} — {self.get_day_number_display()} {self.start_time}–{self.end_time}"


class ScheduleException(models.Model):
    class ExceptionType(models.TextChoices):
        BLOCKED   = "BLOCKED",   "Blocked"
        AVAILABLE = "AVAILABLE", "Extra Availability"

    doctor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="schedule_exceptions",
        limit_choices_to={"role": User.Roles.DOCTOR}
    )
    date       = models.DateField()
    start_time = models.TimeField()
    end_time   = models.TimeField()
    type       = models.CharField(
        max_length=20,
        choices=ExceptionType.choices,
        default=ExceptionType.BLOCKED
    )
    reason = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["date", "start_time"]
        constraints = [
            models.UniqueConstraint(
                fields=["doctor", "date", "start_time"],
                name="unique_exception_slot"
            )
        ]

    def clean(self):
        if self.start_time and self.end_time:
            if self.start_time >= self.end_time:
                raise ValidationError("End time must be greater than start time.")

    def __str__(self):
        return f"{self.doctor.username} — {self.date} [{self.type}] {self.start_time}–{self.end_time}"


class DoctorProfile(models.Model):

    class Specialty(models.TextChoices):
        GENERAL        = "GENERAL",        "General Medicine"
        PEDIATRICS     = "PEDIATRICS",     "Pediatrics"
        CARDIOLOGY     = "CARDIOLOGY",     "Cardiology"
        DERMATOLOGY    = "DERMATOLOGY",    "Dermatology"
        GYNECOLOGY     = "GYNECOLOGY",     "Gynecology"
        NEUROLOGY      = "NEUROLOGY",      "Neurology"
        ORTHOPEDICS    = "ORTHOPEDICS",    "Orthopedics"
        PSYCHIATRY     = "PSYCHIATRY",     "Psychiatry"
        OPHTHALMOLOGY  = "OPHTHALMOLOGY",  "Ophthalmology"
        OTOLARYNGOLOGY = "OTOLARYNGOLOGY", "Otolaryngology"
        UROLOGY        = "UROLOGY",        "Urology"
        ENDOCRINOLOGY  = "ENDOCRINOLOGY",  "Endocrinology"
        OTHER          = "OTHER",          "Other"

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="doctor_profile",
        limit_choices_to={"role": User.Roles.DOCTOR}
    )
    full_name      = models.CharField(max_length=150)
    specialty      = models.CharField(
        max_length=30,
        choices=Specialty.choices,
        default=Specialty.GENERAL
    )
    license_number = models.CharField(max_length=50, unique=True)
    phone          = models.CharField(max_length=20, blank=True)
    bio            = models.TextField(blank=True)
    avatar         = models.ImageField(upload_to="avatars/", blank=True, null=True)

    def __str__(self):
        return f"Dr. {self.full_name} — {self.get_specialty_display()}"
