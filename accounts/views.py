from django.contrib.auth.views import LoginView
from django.contrib.auth import login
from django.contrib import messages
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from datetime import date, timedelta, datetime

from .models import DoctorSchedule
from .forms import (
    PatientRegisterForm,
    DoctorRegisterForm,
    PatientProfileUpdateForm,
    DoctorProfileUpdateForm,
)

from appointments.models import Appointment


# =========================
# HOME
# =========================
def home(request):
    return redirect("login")


# =========================
# LOGIN
# =========================
class RoleBasedLoginView(LoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        role = self.request.user.role
        return reverse_lazy({
            "ADMIN": "admin_dashboard",
            "DOCTOR": "doctor_dashboard",
            "PATIENT": "patient_dashboard",
        }.get(role, "patient_dashboard"))


# =========================
# REGISTER
# =========================
def register_choice(request):
    return render(request, "accounts/register_choice.html")


def patient_register(request):
    form = PatientRegisterForm(request.POST or None)
    if form.is_valid():
        user = form.save()
        login(request, user)
        return redirect("patient_dashboard")
    return render(request, "accounts/register_patient.html", {"form": form})


def doctor_register(request):
    form = DoctorRegisterForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        user = form.save()
        login(request, user)
        return redirect("doctor_dashboard")
    return render(request, "accounts/register_doctor.html", {"form": form})


# =========================
# DASHBOARDS
# =========================
@login_required
def patient_dashboard(request):
    # 🔥 RESTAURA TU FLUJO REAL
    return redirect("appointment_list")


@login_required
def admin_dashboard(request):
    return HttpResponse("Admin dashboard")


@login_required
def doctor_dashboard(request):
    return render(request, "accounts/doctor_dashboard.html")


# =========================
# PROFILE UPDATE
# =========================
@login_required
def profile_update(request):

    if request.user.role == "DOCTOR":
        FormClass = DoctorProfileUpdateForm
    else:
        FormClass = PatientProfileUpdateForm

    if request.method == "POST":
        form = FormClass(
            request.POST,
            request.FILES,
            instance=request.user
        )

        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully ✅")
            return redirect("profile_update")
        else:
            messages.error(request, "Please correct the errors ❌")

    else:
        form = FormClass(instance=request.user)

    return render(request, "accounts/profile_update.html", {
        "form": form
    })


# =========================
# DELETE ACCOUNT
# =========================
@login_required
@require_http_methods(["POST"])
def profile_delete(request):
    request.user.delete()
    messages.success(request, "Account deleted successfully")
    return redirect("login")


# =========================
# CREATE SCHEDULE
# =========================
@login_required
@require_http_methods(["POST"])
def schedule_create(request):
    try:
        day_number = request.POST.get("day_number")
        start_time = request.POST.get("start_time")
        end_time = request.POST.get("end_time")

        schedule = DoctorSchedule(
            doctor=request.user,
            day_number=int(day_number),
            start_time=start_time,
            end_time=end_time,
        )

        schedule.full_clean()
        schedule.save()

        return JsonResponse({"ok": True})

    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)


# =========================
# CALENDAR EVENTS (CON ESTADOS)
# =========================
@login_required
def calendar_events(request):

    today = date.today()
    start = today - timedelta(days=7)
    end = today + timedelta(days=30)

    events = []
    schedules = DoctorSchedule.objects.filter(doctor=request.user)

    for s in schedules:
        current = start

        while current <= end:
            if current.weekday() == s.day_number:

                start_dt = datetime.combine(current, s.start_time)
                end_dt = datetime.combine(current, s.end_time)

                citas = Appointment.objects.filter(
                    doctor=request.user,
                    date=current,
                    start_time__gte=s.start_time,
                    start_time__lt=s.end_time,
                )

                if citas.exists():
                    title = "Reserved"
                    color = "#ef4444"
                else:
                    title = "Available"
                    color = "#10b981"

                events.append({
                    "title": title,
                    "start": start_dt.isoformat(),
                    "end": end_dt.isoformat(),
                    "color": color,
                })

            current += timedelta(days=1)

    return JsonResponse(events, safe=False)