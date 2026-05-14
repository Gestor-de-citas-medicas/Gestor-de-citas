from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Avg, Count
from datetime import timedelta, time, datetime

from .models import Appointment, AppointmentReview
from .forms import AppointmentForm, AppointmentReviewForm
from .emails import (
    send_appointment_confirmation,
    send_appointment_cancellation,
    send_review_request,
    send_appointment_status_change
)

# 🔥 IMPORTANTE
from accounts.models import ScheduleException, User, DoctorSchedule


@login_required
def appointment_list(request):
    user = request.user
    if user.role == "PATIENT":
        appointments = Appointment.objects.filter(patient=user).select_related("doctor", "review")
    elif user.role == "DOCTOR":
        appointments = Appointment.objects.filter(doctor=user).select_related("patient", "review")
    else:
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
            doctor = form.cleaned_data["doctor"]
            date   = form.cleaned_data["date"]
            time_  = form.cleaned_data["start_time"]

            weekday = date.weekday()

            # 🔥 VALIDAR CONTRA CALENDARIO
            schedules = DoctorSchedule.objects.filter(
                doctor=doctor,
                day_number=weekday,
                is_active=True
            )

            valido = False
            for s in schedules:
                if s.start_time <= time_ < s.end_time:
                    valido = True
                    break

            if not valido:
                messages.error(request, "This time is not available ❌")
                return render(request, "appointments/create.html", {"form": form})

            # 🔥 EVITAR DOBLE RESERVA
            if Appointment.objects.filter(
                doctor=doctor,
                date=date,
                start_time=time_
            ).exists():
                messages.error(request, "This time is already booked ❌")
                return render(request, "appointments/create.html", {"form": form})

            appointment = form.save(commit=False)
            appointment.patient = request.user

            start_dt = datetime.combine(date, time_)
            end_dt = start_dt + timedelta(hours=1)
            appointment.end_time = end_dt.time()

            appointment.save()
            messages.success(request, "¡Cita agendada exitosamente!")
            return redirect("appointment_list")

    else:
        # Pre-fill form from query params (coming from busqueda/disponibilidad)
        initial = {}
        if request.GET.get("doctor"):
            initial["doctor"] = request.GET["doctor"]
        if request.GET.get("date"):
            initial["date"] = request.GET["date"]
        if request.GET.get("start"):
            initial["start_time"] = request.GET["start"]
        if request.GET.get("end"):
            initial["end_time"] = request.GET["end"]

        form = AppointmentForm(initial=initial)

    return render(request, "appointments/create.html", {"form": form})


@login_required
def appointment_cancel(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)

    if request.user != appointment.patient and request.user.role != "ADMIN":
        messages.error(request, "No permission.")
        return redirect("appointment_list")

    if request.method == "POST":
        appointment.status = Appointment.Status.CANCELLED
        appointment.save()

        try:
            send_appointment_cancellation(appointment)
            messages.success(request, "Cancelled ✅")
        except Exception as e:
            messages.warning(request, f"Cancelled but email failed: {str(e)}")

        return redirect("appointment_list")

    return render(request, "appointments/cancel_confirm.html", {"appointment": appointment})


@login_required
def appointment_confirm(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)

    if request.user != appointment.doctor and request.user.role != "ADMIN":
        messages.error(request, "No permission.")
        return redirect("appointment_list")

    if appointment.status != Appointment.Status.PENDING:
        messages.warning(request, "Only pending.")
        return redirect("appointment_list")

    appointment.status = Appointment.Status.CONFIRMED
    appointment.save()

    try:
        send_appointment_status_change(appointment, "CONFIRMED")
    except:
        pass

    return redirect("appointment_list")


@login_required
def appointment_complete(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)

    if request.user != appointment.doctor and request.user.role != "ADMIN":
        messages.error(request, "No permission.")
        return redirect("appointment_list")

    if appointment.status != Appointment.Status.CONFIRMED:
        messages.warning(request, "Only confirmed.")
        return redirect("appointment_list")

    appointment.status = Appointment.Status.COMPLETED
    appointment.save()

    try:
        send_appointment_status_change(appointment, "COMPLETED")
        send_review_request(appointment)
    except:
        pass

    return redirect("appointment_list")


# 🔥🔥🔥 ESTA ES LA PARTE CLAVE 🔥🔥🔥
@login_required
def available_slots_api(request):

    doctor_id = request.GET.get("doctor_id")
    date_str  = request.GET.get("date")

    if not doctor_id or not date_str:
        return JsonResponse({"error": "Missing parameters"}, status=400)

    try:
        appointment_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        doctor = get_object_or_404(User, pk=doctor_id, role="DOCTOR")
    except:
        return JsonResponse({"error": "Invalid parameters"}, status=400)

    weekday = appointment_date.weekday()

    # 🔥 USAR CALENDARIO REAL
    schedules = DoctorSchedule.objects.filter(
        doctor=doctor,
        day_number=weekday,
        is_active=True
    )

    slots = []

    for s in schedules:
        hora = datetime.combine(appointment_date, s.start_time).replace(minute=0)

        while hora.time() < s.end_time:

            slot_time = hora.time()

            is_blocked = ScheduleException.objects.filter(
                doctor=doctor,
                date=appointment_date,
                type="BLOCKED",
                start_time__lte=slot_time,
                end_time__gt=slot_time
            ).exists()

            is_booked = Appointment.objects.filter(
                doctor=doctor,
                date=appointment_date,
                start_time__lte=slot_time,
                end_time__gt=slot_time,
                status__in=[Appointment.Status.PENDING, Appointment.Status.CONFIRMED]
            ).exists()

            if not is_blocked and not is_booked:
                slots.append({
                    "time": str(slot_time),
                    "display": slot_time.strftime("%H:%M"),
                })

            hora += timedelta(hours=1)

    return JsonResponse({"slots": slots})


@login_required
def review_create(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)

    if request.user != appointment.patient:
        return redirect("appointment_list")

    if appointment.status != Appointment.Status.COMPLETED:
        return redirect("appointment_list")

    if hasattr(appointment, "review"):
        return redirect("appointment_list")

    if request.method == "POST":
        form = AppointmentReviewForm(request.POST)
        form.instance.appointment = appointment

        if form.is_valid():
            form.save()
            return redirect("appointment_list")

    else:
        form = AppointmentReviewForm()

    return render(request, "appointments/review_form.html", {
        "form": form,
        "appointment": appointment,
    })


def doctor_reviews(request, pk):
    doctor = get_object_or_404(User, pk=pk, role="DOCTOR")

    reviews = AppointmentReview.objects.filter(
        appointment__doctor=doctor
    )

    stats = reviews.aggregate(
        avg_rating=Avg("rating"),
        total_reviews=Count("id"),
    )

    return render(request, "appointments/doctor_reviews.html", {
        "doctor": doctor,
        "reviews": reviews,
        "avg_rating": stats["avg_rating"] or 0,
        "total_reviews": stats["total_reviews"],
    })