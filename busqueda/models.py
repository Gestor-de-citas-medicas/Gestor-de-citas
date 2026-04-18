from django.db import models


class Doctor(models.Model):
    name = models.CharField(max_length=100)
    specialty = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Availability(models.Model):
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name='availability'  # 👈 CLAVE
    )
    date = models.DateField()
    time = models.TimeField()

    def __str__(self):
        return f"{self.doctor.name} - {self.date} {self.time}"

    class Meta:
        db_table = 'busqueda_disponibilidad'