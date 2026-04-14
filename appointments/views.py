from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Appointment
from .forms import AppointmentForm


@login_required
def appointment_list(request):
    user = request.user
    if user.role == "PATIENT":
        appointments = Appointment.objects.filter(patient=user).select_related("doctor")
    elif user.role == "DOCTOR":
        appointments = Appointment.objects.filter(doctor=user).select_related("patient")
    else:  # ADMIN
        appointments = Appointment.objects.all().select_related("patient", "doctor")

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
            appointment.save()
            messages.success(request, "Appointment scheduled successfully!")
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
        messages.success(request, "Appointment cancelled.")
        return redirect("appointment_list")

    return render(request, "appointments/cancel_confirm.html", {"appointment": appointment})
