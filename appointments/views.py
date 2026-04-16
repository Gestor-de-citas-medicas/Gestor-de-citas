from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Avg, Count
from datetime import timedelta, time, datetime
from .models import Appointment, AppointmentReview
from .forms import AppointmentForm, AppointmentReviewForm
from .emails import send_appointment_confirmation, send_appointment_cancellation, send_review_request
from accounts.models import ScheduleException, User


@login_required
def appointment_list(request):
    user = request.user
    if user.role == "PATIENT":
        appointments = Appointment.objects.filter(patient=user).select_related("doctor", "review")
    elif user.role == "DOCTOR":
        appointments = Appointment.objects.filter(doctor=user).select_related("patient", "review")
    else:  # ADMIN
        appointments = Appointment.objects.all().select_related("patient", "doctor", "review")

    return render(request, "appointments/list.html", {"appointments": appointments})


@login_required
def appointment_create(request):
    if request.user.role not in ("PATIENT", "ADMIN"):
        messages.error(request, "Only patients can schedule appointments.")
        return redirect("appointment_list")

    if request.method == "POST":
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.patient = request.user
            # Calcular automáticamente la hora de fin (1 hora después del inicio)
            from datetime import time, datetime
            start = appointment.start_time
            start_dt = datetime.combine(appointment.date, start)
            end_dt = start_dt + timedelta(hours=1)
            appointment.end_time = end_dt.time()
            appointment.save()
            
            # Enviar confirmación de cita
            try:
                send_appointment_confirmation(appointment)
                messages.success(request, "¡Cita reservada exitosamente! Se han enviado confirmaciones por correo.")
            except Exception as e:
                messages.warning(request, f"Cita reservada pero hubo un error al enviar el email: {str(e)}")
            
            return redirect("appointment_list")
    else:
        form = AppointmentForm()

    return render(request, "appointments/create.html", {"form": form})


@login_required
def appointment_cancel(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)

    # Only the patient who owns it or an admin can cancel
    if request.user != appointment.patient and request.user.role != "ADMIN":
        messages.error(request, "You don't have permission to cancel this appointment.")
        return redirect("appointment_list")

    if request.method == "POST":
        appointment.status = Appointment.Status.CANCELLED
        appointment.save()
        # Send cancellation notification
        try:
            print(f"\n🔔 Attempting to send cancellation email for appointment #{appointment.pk}...")
            send_appointment_cancellation(appointment)
            messages.success(request, "Appointment cancelled. Notification emails have been sent.")
        except Exception as e:
            print(f"⚠️ Error sending cancellation email: {str(e)}")
            messages.warning(request, f"Appointment cancelled but error sending email: {str(e)}")
        
        return redirect("appointment_list")

    return render(request, "appointments/cancel_confirm.html", {"appointment": appointment})


@login_required
def appointment_confirm(request, pk):
    """Confirm a pending appointment (PENDING -> CONFIRMED)"""
    appointment = get_object_or_404(Appointment, pk=pk)
    
    # Only the doctor who has the appointment can confirm it
    if request.user != appointment.doctor and request.user.role != "ADMIN":
        messages.error(request, "You don't have permission to confirm this appointment.")
        return redirect("appointment_list")
    
    if appointment.status != Appointment.Status.PENDING:
        messages.warning(request, "Only pending appointments can be confirmed.")
        return redirect("appointment_list")
    
    appointment.status = Appointment.Status.CONFIRMED
    appointment.save()
    messages.success(request, "Appointment confirmed successfully.")
    
    return redirect("appointment_list")


@login_required
def appointment_complete(request, pk):
    """Mark appointment as completed (CONFIRMED -> COMPLETED)"""
    appointment = get_object_or_404(Appointment, pk=pk)
    
    # Only the doctor who has the appointment can mark it as completed
    if request.user != appointment.doctor and request.user.role != "ADMIN":
        messages.error(request, "You don't have permission to complete this appointment.")
        return redirect("appointment_list")
    
    if appointment.status != Appointment.Status.CONFIRMED:
        messages.warning(request, "Only confirmed appointments can be marked as completed.")
        return redirect("appointment_list")
    
    appointment.status = Appointment.Status.COMPLETED
    appointment.save()
    
    # Send review request email to patient
    try:
        send_review_request(appointment)
        messages.success(request, "Appointment completed. A review request has been sent to the patient.")
    except Exception as e:
        messages.success(request, "Appointment marked as completed.")
    
    return redirect("appointment_list")


@login_required
def available_slots_api(request):
    """
    API que retorna los slots disponibles para un doctor y fecha específicos.
    Parámetros: doctor_id (int), date (YYYY-MM-DD)
    """
    doctor_id = request.GET.get("doctor_id")
    date_str = request.GET.get("date")
    
    if not doctor_id or not date_str:
        return JsonResponse({"error": "Missing parameters"}, status=400)
    
    try:
        appointment_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        doctor = get_object_or_404(User, pk=doctor_id, role="DOCTOR")
    except:
        return JsonResponse({"error": "Invalid parameters"}, status=400)
    
    # Franjas horarias de 1 hora: 8:00 - 18:00
    DEFAULT_START_HOUR = 8
    DEFAULT_END_HOUR = 18
    SLOT_DURATION = 1  # horas
    
    slots = []
    
    # Generar todos los slots posibles
    for hour in range(DEFAULT_START_HOUR, DEFAULT_END_HOUR):
        slot_start = time(hour, 0)
        slot_end = time(hour + SLOT_DURATION, 0)
        
        # Verificar si está bloqueado por excepción
        is_blocked = ScheduleException.objects.filter(
            doctor=doctor,
            date=appointment_date,
            type="BLOCKED",
            start_time__lte=slot_start,
            end_time__gt=slot_start
        ).exists()
        
        # Verificar si hay una cita ocupando este slot
        is_booked = Appointment.objects.filter(
            doctor=doctor,
            date=appointment_date,
            start_time__lte=slot_start,
            end_time__gt=slot_start,
            status__in=[Appointment.Status.PENDING, Appointment.Status.CONFIRMED]
        ).exists()
        
        if not is_blocked and not is_booked:
            slots.append({
                "time": str(slot_start),
                "display": slot_start.strftime("%H:%M"),
            })
    
    return JsonResponse({"slots": slots})


@login_required
def review_create(request, pk):
    """Allow a patient to leave a review for a completed appointment."""
    appointment = get_object_or_404(Appointment, pk=pk)

    # Only the patient who owns the appointment can review
    if request.user != appointment.patient:
        messages.error(request, "You don't have permission to review this appointment.")
        return redirect("appointment_list")

    if appointment.status != Appointment.Status.COMPLETED:
        messages.error(request, "Only completed appointments can be reviewed.")
        return redirect("appointment_list")

    # Check if already reviewed
    if hasattr(appointment, "review"):
        messages.info(request, "You have already reviewed this appointment.")
        return redirect("appointment_list")

    if request.method == "POST":
        form = AppointmentReviewForm(request.POST)
        form.instance.appointment = appointment
        if form.is_valid():
            review = form.save()

            messages.success(request, "Thank you for your review! ⭐")
            return redirect("appointment_list")
    else:
        form = AppointmentReviewForm()

    return render(request, "appointments/review_form.html", {
        "form": form,
        "appointment": appointment,
    })


def doctor_reviews(request, pk):
    """Public view showing a doctor's reviews and average rating."""
    doctor = get_object_or_404(User, pk=pk, role="DOCTOR")

    reviews = AppointmentReview.objects.filter(
        appointment__doctor=doctor
    ).select_related("appointment", "appointment__patient")

    stats = reviews.aggregate(
        avg_rating=Avg("rating"),
        total_reviews=Count("id"),
    )
    avg_rating = stats["avg_rating"] or 0
    total_reviews = stats["total_reviews"]

    # Build star display info
    full_stars = int(avg_rating)
    has_half = (avg_rating - full_stars) >= 0.5
    empty_stars = 5 - full_stars - (1 if has_half else 0)

    # Rating distribution
    distribution = {}
    for i in range(5, 0, -1):
        count = reviews.filter(rating=i).count()
        pct = (count / total_reviews * 100) if total_reviews > 0 else 0
        distribution[i] = {"count": count, "pct": round(pct)}

    return render(request, "appointments/doctor_reviews.html", {
        "doctor": doctor,
        "reviews": reviews,
        "avg_rating": round(avg_rating, 1),
        "total_reviews": total_reviews,
        "full_stars": full_stars,
        "has_half": has_half,
        "empty_stars": empty_stars,
        "distribution": distribution,
    })
