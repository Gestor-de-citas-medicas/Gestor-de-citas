import os
import django
from datetime import timedelta, date, time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings
if "testserver" not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append("testserver")

from django.test import Client
from appointments.models import Appointment, AppointmentReview
from accounts.models import User
from django.urls import reverse

def run_view_tests():
    print("=== TESTING VIEW ROUTES ===")
    
    # Setup
    patient = User.objects.filter(role="PATIENT").first()
    doctor = User.objects.filter(role="DOCTOR").first()
    
    if not patient or not doctor:
        print("❌ Need test users in db")
        return
        
    # Set password if needed, or we can just force_login
    client = Client()
    client.force_login(patient)
    print("✓ Logged in as Patient")
    
    # 1. Dashboard (appointment list)
    resp = client.get('/appointments/')
    print(f"GET /appointments/ : {resp.status_code}")
    assert resp.status_code == 200
    
    # 2. Doctor stats page (public access)
    resp = client.get(f'/appointments/doctor/{doctor.id}/reviews/')
    print(f"GET /appointments/doctor/{doctor.id}/reviews/ : {resp.status_code}")
    assert resp.status_code == 200
    
    # 3. Create appointment (via POST)
    print("POST /appointments/new/")
    resp = client.post('/appointments/new/', {
        'doctor': doctor.id,
        'date': date.today().isoformat(),
        'start_time': '12:00',
        'reason': 'Test UI View'
    })
    print(f"Status Code: {resp.status_code}")
    assert resp.status_code == 302, f"Expected 302 redirect, got {resp.status_code}."
    
    # Let's get the newly created appointment
    appt = Appointment.objects.get(patient=patient, doctor=doctor, start_time='12:00:00')
    print(f"✓ Created Appointment via view: #{appt.id}")
    
    # 4. Mark as completed (requires doctor access, so switch user)
    client.force_login(doctor)
    
    # Wait, the appointment defaults to PENDING. Doctor needs to CONFIRM first, then COMPLETE.
    resp = client.get(f'/appointments/{appt.id}/confirm/')
    print(f"GET /appointments/{appt.id}/confirm/ : {resp.status_code}")
    # Actually confirm might be GET or POST, check view
    # Views says: @login_required def appointment_confirm ... redirect
    # Wait, appointment_confirm is GET?!  It sets status to CONFIRMED.
    assert resp.status_code == 302
    
    resp = client.get(f'/appointments/{appt.id}/complete/')
    print(f"GET /appointments/{appt.id}/complete/ : {resp.status_code}")
    assert resp.status_code == 302
    
    # Refresh appt
    appt.refresh_from_db()
    print(f"✓ Appointment status is now: {appt.status}")
    assert appt.status == "COMPLETED"
    
    # 5. Review (requires patient access)
    client.force_login(patient)
    resp = client.get(f'/appointments/{appt.id}/review/')
    print(f"GET /appointments/{appt.id}/review/ : {resp.status_code}")
    assert resp.status_code == 200
    
    resp = client.post(f'/appointments/{appt.id}/review/', {
        'rating': 4,
        'comment': 'Good from UI test'
    })
    print(f"POST /appointments/{appt.id}/review/ : {resp.status_code}")
    assert resp.status_code == 302
    
    # Verify review
    review = AppointmentReview.objects.get(appointment=appt)
    print(f"✓ Review created via view: {review.rating} stars - {review.comment}")
    
    # Clean up
    appt.delete()
    print("✓ View tests passed and cleaned up")

if __name__ == "__main__":
    run_view_tests()
