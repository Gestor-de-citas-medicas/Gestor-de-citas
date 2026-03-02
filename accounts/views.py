from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
import json

from .models import DoctorSchedule, ScheduleException
from .forms import DoctorScheduleForm, ScheduleExceptionForm


# ── Helpers ──────────────────────────────────────────────────────────────────

def doctor_required(view_func):
    """Decorator: exige login + rol DOCTOR."""
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role != "DOCTOR":
            return redirect("home")
        return view_func(request, *args, **kwargs)
    return wrapper


# ── Públicas ──────────────────────────────────────────────────────────────────

def home(request):
    return redirect("login")


class RoleBasedLoginView(LoginView):
    template_name = "accounts/login.html"

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["username"].widget.attrs.update({
            "placeholder": "Tu usuario o email",
            "autocomplete": "username"
        })
        form.fields["password"].widget.attrs.update({
            "placeholder": "••••••••",
            "autocomplete": "current-password"
        })
        return form

    def get_success_url(self):
        role = self.request.user.role
        destinations = {
            "ADMIN":   "admin_dashboard",
            "DOCTOR":  "doctor_dashboard",
            "PATIENT": "patient_dashboard",
        }
        return reverse_lazy(destinations.get(role, "patient_dashboard"))


# ── Dashboards básicos ────────────────────────────────────────────────────────

@login_required
def patient_dashboard(request):
    return HttpResponse("Patient dashboard ✅")


@login_required
def admin_dashboard(request):
    return HttpResponse("Admin dashboard ✅")


# ── Doctor: dashboard principal ───────────────────────────────────────────────

@doctor_required
def doctor_dashboard(request):
    schedules  = DoctorSchedule.objects.filter(doctor=request.user, is_active=True)
    exceptions = ScheduleException.objects.filter(doctor=request.user).order_by("date", "start_time")

    return render(request, "accounts/doctor_dashboard.html", {
        "schedules":  schedules,
        "exceptions": exceptions,
    })


# ── Doctor: horarios recurrentes (DoctorSchedule) ─────────────────────────────

@doctor_required
@require_http_methods(["POST"])
def schedule_create(request):
    form = DoctorScheduleForm(request.POST)
    if form.is_valid():
        schedule = form.save(commit=False)
        schedule.doctor = request.user
        try:
            schedule.full_clean()   # dispara validaciones del modelo (solapamiento, etc.)
            schedule.save()
        except ValidationError as e:
            return JsonResponse({"ok": False, "errors": e.message_dict}, status=400)
        return JsonResponse({"ok": True, "id": schedule.pk})
    return JsonResponse({"ok": False, "errors": form.errors}, status=400)


@doctor_required
@require_http_methods(["POST"])
def schedule_toggle(request, pk):
    """Activa o pausa un horario recurrente sin borrarlo."""
    schedule = get_object_or_404(DoctorSchedule, pk=pk, doctor=request.user)
    schedule.is_active = not schedule.is_active
    schedule.save(update_fields=["is_active"])
    return JsonResponse({"ok": True, "is_active": schedule.is_active})


@doctor_required
@require_http_methods(["POST"])
def schedule_delete(request, pk):
    schedule = get_object_or_404(DoctorSchedule, pk=pk, doctor=request.user)
    schedule.delete()
    return JsonResponse({"ok": True})


# ── Doctor: excepciones por fecha (ScheduleException) ─────────────────────────

@doctor_required
@require_http_methods(["POST"])
def exception_create(request):
    form = ScheduleExceptionForm(request.POST)
    if form.is_valid():
        exc = form.save(commit=False)
        exc.doctor = request.user
        try:
            exc.full_clean()
            exc.save()
        except ValidationError as e:
            return JsonResponse({"ok": False, "errors": e.message_dict}, status=400)
        return JsonResponse({"ok": True, "id": exc.pk})
    return JsonResponse({"ok": False, "errors": form.errors}, status=400)


@doctor_required
@require_http_methods(["POST"])
def exception_update(request, pk):
    exc  = get_object_or_404(ScheduleException, pk=pk, doctor=request.user)
    form = ScheduleExceptionForm(request.POST, instance=exc)
    if form.is_valid():
        updated = form.save(commit=False)
        try:
            updated.full_clean()
            updated.save()
        except ValidationError as e:
            return JsonResponse({"ok": False, "errors": e.message_dict}, status=400)
        return JsonResponse({"ok": True})
    return JsonResponse({"ok": False, "errors": form.errors}, status=400)


@doctor_required
@require_http_methods(["POST"])
def exception_delete(request, pk):
    exc = get_object_or_404(ScheduleException, pk=pk, doctor=request.user)
    exc.delete()
    return JsonResponse({"ok": True})


# ── API: eventos para FullCalendar ─────────────────────────────────────────────

@doctor_required
def calendar_events(request):
    """
    Devuelve todos los eventos del médico en formato FullCalendar.
    El front hace GET /doctor/calendar/events/ al cargar el calendario.
    """
    from datetime import date, timedelta

    # Rango: semana actual ± 4 semanas (ajustable con query params)
    today     = date.today()
    range_start = today - timedelta(weeks=4)
    range_end   = today + timedelta(weeks=8)

    events = []

    # 1. Horarios recurrentes → expandir en fechas concretas
    schedules = DoctorSchedule.objects.filter(doctor=request.user, is_active=True)
    current = range_start
    while current <= range_end:
        # day_number: 0=Domingo … 6=Sábado  |  weekday(): 0=Lunes … 6=Domingo
        current_day = (current.weekday() + 1) % 7  # convierte a tu convención
        for s in schedules:
            if s.day_number == current_day:
                events.append({
                    "id":        f"schedule-{s.pk}-{current}",
                    "title":     "Disponible",
                    "start":     f"{current}T{s.start_time}",
                    "end":       f"{current}T{s.end_time}",
                    "type":      "available",
                    "className": "event-available",
                    "scheduleId": s.pk,
                })
        current += timedelta(days=1)

    # 2. Excepciones (bloqueos y disponibilidad extra)
    exceptions = ScheduleException.objects.filter(
        doctor=request.user,
        date__range=(range_start, range_end)
    )
    type_map = {
        "BLOCKED":   ("Bloqueado",         "event-blocked"),
        "AVAILABLE": ("Disponible extra",  "event-available"),
    }
    for exc in exceptions:
        title, css = type_map[exc.type]
        events.append({
            "id":          f"exc-{exc.pk}",
            "title":       title,
            "start":       f"{exc.date}T{exc.start_time}",
            "end":         f"{exc.date}T{exc.end_time}",
            "type":        exc.type.lower(),
            "className":   css,
            "reason":      exc.reason,
            "exceptionId": exc.pk,
        })

    return JsonResponse(events, safe=False)