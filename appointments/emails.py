from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def send_appointment_confirmation(appointment):
    """
    Send appointment confirmation to patient and doctor
    """
    try:
        print(f"\n{'='*60}")
        print(f"SENDING CONFIRMATION - Appointment #{appointment.pk}")
        print(f"{'='*60}")
        
        # Verify basic data
        print(f"Patient: {appointment.patient.first_name} ({appointment.patient.email})")
        print(f"Doctor: {appointment.doctor.first_name} ({appointment.doctor.email})")
        print(f"Date: {appointment.date}, Time: {appointment.start_time}-{appointment.end_time}")
        
        # Validate emails
        if not appointment.patient.email:
            raise ValueError("Patient does not have a registered email")
        if not appointment.doctor.email:
            raise ValueError("Doctor does not have a registered email")
        
        subject = f"Appointment Confirmation - {appointment.date}"
        
        # Context data
        context = {
            "appointment": appointment,
            "patient": appointment.patient,
            "doctor": appointment.doctor,
            "date": appointment.date,
            "start_time": appointment.start_time,
            "end_time": appointment.end_time,
            "reason": appointment.reason,
        }
        
        # Email to patient
        print("\n📧 Rendering patient template...")
        patient_message = render_to_string(
            "appointments/emails/patient_confirmation.html", 
            context
        )
        print("✓ Template rendered successfully")
        
        print(f"📤 Sending email to patient ({appointment.patient.email})...")
        send_mail(
            subject=subject,
            message=f"Your appointment has been confirmed for {appointment.date} at {appointment.start_time}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[appointment.patient.email],
            html_message=patient_message,
            fail_silently=False,
        )
        print("✓ Email to patient sent successfully")
        logger.info(f"Confirmation email sent to patient: {appointment.patient.email}")
        
        # Email to doctor
        print(f"\n📧 Rendering doctor template...")
        doctor_message = render_to_string(
            "appointments/emails/doctor_confirmation.html",
            context
        )
        print("✓ Template rendered successfully")
        
        print(f"📤 Sending email to doctor ({appointment.doctor.email})...")
        send_mail(
            subject=subject,
            message=f"Appointment confirmed with {appointment.patient.first_name} for {appointment.date} at {appointment.start_time}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[appointment.doctor.email],
            html_message=doctor_message,
            fail_silently=False,
        )
        print("✓ Email to doctor sent successfully")
        logger.info(f"Confirmation email sent to doctor: {appointment.doctor.email}")
        print(f"\n{'='*60}")
        print("✓ CONFIRMATION SENT SUCCESSFULLY")
        print(f"{'='*60}\n")
        
    except Exception as e:
        print(f"\n{'='*60}")
        print(f"❌ ERROR SENDING EMAIL: {str(e)}")
        print(f"{'='*60}\n")
        logger.error(f"Error sending confirmation email: {str(e)}", exc_info=True)
        raise


def send_appointment_cancellation(appointment):
    """
    Send appointment cancellation notification to patient and doctor
    """
    try:
        print(f"\n{'='*60}")
        print(f"SENDING CANCELLATION - Appointment #{appointment.pk}")
        print(f"{'='*60}")
        
        # Verify basic data
        print(f"Patient: {appointment.patient.first_name} ({appointment.patient.email})")
        print(f"Doctor: {appointment.doctor.first_name} ({appointment.doctor.email})")
        
        # Validate emails
        if not appointment.patient.email:
            raise ValueError("Patient does not have a registered email")
        if not appointment.doctor.email:
            raise ValueError("Doctor does not have a registered email")
        
        subject = f"Appointment Cancelled - {appointment.date}"
        
        context = {
            "appointment": appointment,
            "patient": appointment.patient,
            "doctor": appointment.doctor,
            "date": appointment.date,
            "start_time": appointment.start_time,
        }
        
        # Email to patient
        print("\n📧 Rendering patient cancellation template...")
        patient_message = render_to_string(
            "appointments/emails/patient_cancellation.html",
            context
        )
        print("✓ Template rendered successfully")
        
        print(f"📤 Sending email to patient ({appointment.patient.email})...")
        send_mail(
            subject=subject,
            message=f"Your appointment on {appointment.date} at {appointment.start_time} has been cancelled",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[appointment.patient.email],
            html_message=patient_message,
            fail_silently=False,
        )
        print("✓ Email to patient sent successfully")
        logger.info(f"Cancellation email sent to patient: {appointment.patient.email}")
        
        # Email to doctor
        print(f"\n📧 Rendering doctor cancellation template...")
        doctor_message = render_to_string(
            "appointments/emails/doctor_cancellation.html",
            context
        )
        print("✓ Template rendered successfully")
        
        print(f"📤 Sending email to doctor ({appointment.doctor.email})...")
        send_mail(
            subject=subject,
            message=f"Appointment with {appointment.patient.first_name} on {appointment.date} at {appointment.start_time} has been cancelled",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[appointment.doctor.email],
            html_message=doctor_message,
            fail_silently=False,
        )
        print("✓ Email to doctor sent successfully")
        logger.info(f"Cancellation email sent to doctor: {appointment.doctor.email}")
        print(f"\n{'='*60}")
        print("✓ CANCELLATION SENT SUCCESSFULLY")
        print(f"{'='*60}\n")
        
    except Exception as e:
        print(f"\n{'='*60}")
        print(f"❌ ERROR SENDING EMAIL: {str(e)}")
        print(f"{'='*60}\n")
        logger.error(f"Error sending cancellation email: {str(e)}", exc_info=True)
        raise


def send_review_request(appointment):
    """
    Send a review request email to the patient after appointment is completed.
    """
    try:
        print(f"\n{'='*60}")
        print(f"SENDING REVIEW REQUEST - Appointment #{appointment.pk}")
        print(f"{'='*60}")

        if not appointment.patient.email:
            raise ValueError("Patient does not have a registered email")

        subject = f"How was your appointment? Leave a review! - {appointment.date}"

        context = {
            "appointment": appointment,
            "patient": appointment.patient,
            "doctor": appointment.doctor,
            "date": appointment.date,
            "start_time": appointment.start_time,
        }

        print("\n📧 Rendering review request template...")
        patient_message = render_to_string(
            "appointments/emails/review_request.html",
            context
        )
        print("✓ Template rendered successfully")

        print(f"📤 Sending review request to patient ({appointment.patient.email})...")
        send_mail(
            subject=subject,
            message=f"Your appointment on {appointment.date} has been completed. We'd love to hear your feedback!",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[appointment.patient.email],
            html_message=patient_message,
            fail_silently=False,
        )
        print("✓ Review request email sent successfully")
        logger.info(f"Review request sent to: {appointment.patient.email}")
        print(f"\n{'='*60}")
        print("✓ REVIEW REQUEST SENT SUCCESSFULLY")
        print(f"{'='*60}\n")

    except Exception as e:
        print(f"\n{'='*60}")
        print(f"❌ ERROR SENDING REVIEW REQUEST: {str(e)}")
        print(f"{'='*60}\n")
        logger.error(f"Error sending review request email: {str(e)}", exc_info=True)
        raise
