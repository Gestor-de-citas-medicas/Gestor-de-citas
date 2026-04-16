#!/usr/bin/env python
"""
Test Manual: Crea una cita de prueba y envía email
Ejecutar: python test_appointment.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from accounts.models import User
from appointments.models import Appointment
from appointments.emails import send_appointment_confirmation
from datetime import date, time

print("\n" + "="*70)
print("TEST MANUAL DE CREACIÓN DE CITA Y ENVÍO DE EMAIL")
print("="*70)

# 1. Obtener un paciente y un doctor
print("\n1️⃣ Buscando paciente y doctor...")
patients = User.objects.filter(role="PATIENT")
doctors = User.objects.filter(role="DOCTOR")

if not patients:
    print("❌ No hay pacientes registrados")
    exit(1)

if not doctors:
    print("❌ No hay doctores registrados")
    exit(1)

patient = patients.first()
doctor = doctors.first()

print(f"✓ Paciente: {patient.username} ({patient.email})")
print(f"✓ Doctor: {doctor.username} ({doctor.email})")

# 2. Crear una cita de prueba
print("\n2️⃣ Creando cita de prueba...")
appointment = Appointment.objects.create(
    patient=patient,
    doctor=doctor,
    date=date(2026, 4, 20),
    start_time=time(10, 0),
    end_time=time(11, 0),
    reason="Test de cita",
    status=Appointment.Status.PENDING
)
print(f"✓ Cita creada con ID: #{appointment.pk}")

# 3. Intentar enviar el email
print("\n3️⃣ Intentando enviar email de confirmación...\n")
try:
    send_appointment_confirmation(appointment)
    print("\n✅ EMAIL ENVIADO EXITOSAMENTE")
except Exception as e:
    print(f"\n❌ ERROR AL ENVIAR EMAIL: {str(e)}")
    import traceback
    traceback.print_exc()

# 4. Limpiar (opcional)
print("\n4️⃣ Limpiando datos de prueba...")
appointment.delete()
print("✓ Cita de prueba eliminada")

print("\n" + "="*70)
print("FIN DEL TEST")
print("="*70 + "\n")
