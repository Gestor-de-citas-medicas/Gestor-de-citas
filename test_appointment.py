#!/usr/bin/env python
"""
Manual Test: Creates a test appointment and sends email
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
print("MANUAL TEST: APPOINTMENT CREATION AND EMAIL SENDING")
print("="*70)

# 1. Obtener un paciente y un doctor
print("\n1️⃣ Looking up patient and doctor...")
patients = User.objects.filter(role="PATIENT")
doctors = User.objects.filter(role="DOCTOR")

if not patients:
    print("❌ No patients registered in the database")
    exit(1)

if not doctors:
    print("❌ No doctors registered in the database")
    exit(1)

patient = patients.first()
doctor = doctors.first()

print(f"✓ Patient: {patient.username} ({patient.email})")
print(f"✓ Doctor: {doctor.username} ({doctor.email})")

# 2. Create a test appointment
print("\n2️⃣ Creating test appointment...")
appointment = Appointment.objects.create(
    patient=patient,
    doctor=doctor,
    date=date(2026, 4, 20),
    start_time=time(10, 0),
    end_time=time(11, 0),
    reason="Test appointment",
    status=Appointment.Status.PENDING
)
print(f"✓ Appointment created with ID: #{appointment.pk}")

# 3. Intentar enviar el email
print("\n3️⃣ Sending confirmation email...\n")
try:
    send_appointment_confirmation(appointment)
    print("\n✅ EMAIL SENT SUCCESSFULLY")
except Exception as e:
    print(f"\n❌ ERROR WHILE SENDING EMAIL: {str(e)}")
    import traceback
    traceback.print_exc()

# 4. Limpiar (opcional)
print("\n4️⃣ Cleaning up: deleting test appointment...")
appointment.delete()
print("✓ Test appointment deleted")

print("\n" + "="*70)
print("TEST ENDED")
print("="*70 + "\n")
