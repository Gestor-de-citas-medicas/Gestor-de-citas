#!/usr/bin/env python
"""
Direct test: Create an appointment and send email
Ejecutar: python test_send_email.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from appointments.models import Appointment
from appointments.emails import send_appointment_confirmation
from datetime import date, time

User = get_user_model()

print("\n" + "="*60)
print("TEST: Create appointment and send email via Gmail")
print("="*60 + "\n")

# Obtener un paciente y un doctor
patient = User.objects.filter(role='PATIENT').first()
doctor = User.objects.filter(role='DOCTOR').first()

if not patient or not doctor:
    print("❌ No patient or doctor found in the database")
    exit(1)

print(f"Paciente: {patient.username} ({patient.email})")
print(f"Doctor: {doctor.username} ({doctor.email})\n")

# Clean up old appointments from today to avoid UNIQUE constraint conflicts
Appointment.objects.filter(doctor=doctor, date=date.today()).delete()

# Create an appointment at a new time slot
try:
    appointment = Appointment.objects.create(
        patient=patient,
        doctor=doctor,
        date=date.today(),
        start_time=time(14, 30),  # Diferente hora
        end_time=time(15, 30),
        reason="Gmail email test",
        status=Appointment.Status.PENDING
    )
    print(f"✅ Appointment created: #{appointment.pk}\n")
    
    # Intentar enviar email
    print("Intentando enviar email con Gmail...\n")
    send_appointment_confirmation(appointment)
    print("\n✅ Test completed - Check your inbox")
    
except Exception as e:
    print(f"\n❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
