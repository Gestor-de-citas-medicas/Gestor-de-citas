"""
busqueda/views.py — Búsqueda de doctores y disponibilidad.
Usa los modelos REALES: accounts.DoctorProfile, accounts.DoctorSchedule, appointments.Appointment.
"""
from datetime import date, timedelta, datetime, time
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required

from accounts.models import DoctorProfile, DoctorSchedule, ScheduleException, User
from appointments.models import Appointment


@login_required
def buscar_doctor(request):
    """Busca doctores reales por especialidad usando DoctorProfile."""
    query = request.GET.get("especialidad", "").strip()

    profiles = DoctorProfile.objects.select_related("user").filter(
        user__is_active=True,
        user__role=User.Roles.DOCTOR,
    )

    if query:
        # Buscar por nombre o por especialidad (display name)
        from django.db.models import Q
        profiles = profiles.filter(
            Q(full_name__icontains=query) |
            Q(specialty__icontains=query) |
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query)
        )

    # Especialidades disponibles para el filtro de chips
    all_specialties = DoctorProfile.Specialty.choices

    return render(request, "busqueda/buscar_doctor.html", {
        "doctores": profiles,
        "query": query,
        "specialties": all_specialties,
    })


@login_required
def disponibilidad(request, doctor_id):
    """
    Muestra los slots disponibles de un doctor para los próximos 7 días.
    Calcula slots reales de 30 min usando DoctorSchedule menos citas existentes y excepciones bloqueadas.
    """
    doctor_user = get_object_or_404(User, pk=doctor_id, role=User.Roles.DOCTOR)
    profile = getattr(doctor_user, "doctor_profile", None)

    # Calcular slots para los próximos 7 días
    today = date.today()
    days_range = [today + timedelta(days=i) for i in range(7)]

    all_slots = []
    for target_date in days_range:
        slots = _get_slots_for_date(doctor_user, target_date)
        for slot in slots:
            all_slots.append({
                "date": target_date,
                "date_display": target_date.strftime("%a %d %b"),
                "start_time": slot["start"],
                "end_time": slot["end"],
                "start_display": slot["start"].strftime("%H:%M"),
                "end_display": slot["end"].strftime("%H:%M"),
            })

    return render(request, "busqueda/disponibilidad.html", {
        "doctor": doctor_user,
        "profile": profile,
        "slots": all_slots,
    })


@login_required
def disponibilidad_ajax(request, doctor_id):
    """AJAX: Retorna tabla de slots disponibles para un doctor."""
    doctor_user = get_object_or_404(User, pk=doctor_id, role=User.Roles.DOCTOR)
    profile = getattr(doctor_user, "doctor_profile", None)

    # Slots para los próximos 7 días
    today = date.today()
    days_range = [today + timedelta(days=i) for i in range(7)]

    all_slots = []
    for target_date in days_range:
        slots = _get_slots_for_date(doctor_user, target_date)
        for slot in slots:
            all_slots.append({
                "date": target_date,
                "date_display": target_date.strftime("%a %d %b"),
                "start_time": slot["start"],
                "end_time": slot["end"],
                "start_display": slot["start"].strftime("%H:%M"),
                "end_display": slot["end"].strftime("%H:%M"),
            })

    return render(request, "busqueda/tabla_disponibilidad.html", {
        "doctor": doctor_user,
        "profile": profile,
        "slots": all_slots,
    })


def _get_slots_for_date(doctor_user: User, target_date: date) -> list[dict]:
    """
    Calcula slots de 30 minutos disponibles para un doctor en una fecha específica.
    Tiene en cuenta:
    - DoctorSchedule (horario recurrente semanal)
    - ScheduleException bloqueadas (días cancelados)
    - Appointment existentes (citas ya reservadas)
    """
    # Convertir weekday de Python (lunes=0) a nuestro esquema (domingo=0)
    python_weekday = target_date.weekday()
    day_number = (python_weekday + 1) % 7

    # Horarios del doctor para ese día de la semana
    schedules = DoctorSchedule.objects.filter(
        doctor=doctor_user, day_number=day_number, is_active=True
    )

    if not schedules.exists():
        return []

    # Excepciones bloqueadas para esa fecha
    blocked = ScheduleException.objects.filter(
        doctor=doctor_user,
        date=target_date,
        type=ScheduleException.ExceptionType.BLOCKED,
    )

    # Citas ya reservadas para esa fecha
    booked = Appointment.objects.filter(
        doctor=doctor_user,
        date=target_date,
        status__in=[Appointment.Status.PENDING, Appointment.Status.CONFIRMED],
    ).values_list("start_time", "end_time")
    booked_ranges = list(booked)

    def is_blocked(slot_start: time, slot_end: time) -> bool:
        for exc in blocked:
            if slot_start < exc.end_time and slot_end > exc.start_time:
                return True
        for b_start, b_end in booked_ranges:
            if slot_start < b_end and slot_end > b_start:
                return True
        return False

    slots = []
    delta = timedelta(minutes=30)

    for schedule in schedules:
        current = datetime.combine(target_date, schedule.start_time)
        end_dt = datetime.combine(target_date, schedule.end_time)

        while current + delta <= end_dt:
            slot_s = current.time()
            slot_e = (current + delta).time()
            if not is_blocked(slot_s, slot_e):
                slots.append({"start": slot_s, "end": slot_e})
            current += delta

    return slots