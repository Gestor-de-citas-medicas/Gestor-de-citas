from django.db import models
from django.conf import settings


class Appointment(models.Model):

    class Status(models.TextChoices):
        PENDING   = "PENDING",   "Pending"
        CONFIRMED = "CONFIRMED", "Confirmed"
        CANCELLED = "CANCELLED", "Cancelled"
        COMPLETED = "COMPLETED", "Completed"

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="appointments_as_patient",
        limit_choices_to={"role": "PATIENT"},
    )
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="appointments_as_doctor",
        limit_choices_to={"role": "DOCTOR"},
    )
    date       = models.DateField()
    start_time = models.TimeField()
    end_time   = models.TimeField()
    reason     = models.TextField(max_length=500, blank=True)
    status     = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["date", "start_time"]
        # Prevent double-booking: same doctor, same date, overlapping slot
        constraints = [
            models.UniqueConstraint(
                fields=["doctor", "date", "start_time"],
                name="unique_doctor_slot",
            )
        ]

    def __str__(self):
        return f"{self.date} {self.start_time} | {self.patient} → Dr. {self.doctor}"


class AppointmentReview(models.Model):
    """Post-appointment review left by the patient."""

    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.CASCADE,
        related_name="review",
    )
    rating = models.PositiveSmallIntegerField(
        choices=[(i, f"{i} Star{'s' if i > 1 else ''}") for i in range(1, 6)],
        help_text="Rate from 1 to 5 stars",
    )
    comment = models.TextField(max_length=1000, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.appointment.status != Appointment.Status.COMPLETED:
            raise ValidationError(
                "Reviews can only be submitted for completed appointments."
            )

    def __str__(self):
        return (
            f"Review #{self.pk} — {self.rating}★ by "
            f"{self.appointment.patient.username}"
        )
