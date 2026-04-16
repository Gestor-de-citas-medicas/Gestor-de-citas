import os
import django
from datetime import timedelta, date, time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from appointments.models import Appointment, AppointmentReview
from accounts.models import User
from appointments.emails import send_appointment_confirmation, send_appointment_cancellation, send_review_request

def test_full_flow():
    print("=== TESTING FULL APPOINTMENT & REVIEW FLOW ===")
    
    # 1. Get users
    patient = User.objects.filter(role="PATIENT").first()
    doctor = User.objects.filter(role="DOCTOR").first()
    
    if not patient or not doctor:
        print("❌ Cannot test: need at least 1 PATIENT and 1 DOCTOR in DB")
        return
        
    print(f"✓ Found Patient: {patient.username} and Doctor: {doctor.username}")
    
    # 2. Create appointment
    appt = Appointment.objects.create(
        patient=patient,
        doctor=doctor,
        date=date.today(),
        start_time=time(10, 0),
        end_time=time(11, 0),
        reason="Testing full flow with reviews",
        status=Appointment.Status.PENDING
    )
    print(f"✓ Created Appointment #{appt.id} (Status: {appt.status})")
    
    # 3. Confirm appointment
    appt.status = Appointment.Status.CONFIRMED
    appt.save()
    print(f"✓ Confirmed Appointment #{appt.id}")
    
    # 4. Complete appointment
    appt.status = Appointment.Status.COMPLETED
    appt.save()
    print(f"✓ Completed Appointment #{appt.id}")
    
    # Enviar email de completado/review
    try:
        send_review_request(appt)
        print("✓ Review request email sent successfully")
    except Exception as e:
        print(f"⚠️ Error sending review request email: {e}")
        
    # 5. Create Review
    try:
        review = AppointmentReview.objects.create(
            appointment=appt,
            rating=5,
            comment="Excellent doctor, highly recommended!"
        )
        print(f"✓ Created Review #{review.id} with {review.rating} stars")
    except Exception as e:
        print(f"❌ Failed to create review: {e}")
        
    # Verify we can't create another review
    try:
        review2 = AppointmentReview.objects.create(
            appointment=appt,
            rating=1,
            comment="Another one"
        )
        print(f"❌ ERROR: Was able to create a second review for the same appointment!")
    except Exception as e:
        print(f"✓ Verified one-to-one relationship (cannot create second review): {type(e).__name__}")
        
    # 6. Verify Doctor Stats
    from django.db.models import Avg, Count
    reviews = AppointmentReview.objects.filter(appointment__doctor=doctor)
    stats = reviews.aggregate(avg_rating=Avg("rating"), total=Count("id"))
    print(f"✓ Doctor {doctor.username} stats: {stats['avg_rating']} avg rating, {stats['total']} total reviews")
    
    # 7. Cleanup
    appt.delete()
    print("✓ Cleaned up test data")

if __name__ == "__main__":
    test_full_flow()
