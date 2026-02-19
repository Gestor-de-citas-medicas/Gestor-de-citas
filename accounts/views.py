from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect
from .models import DoctorSchedule
from .forms import DoctorScheduleForm
from django.shortcuts import render



def home(request):
    # Opción 1: la raíz (/) siempre redirige al login
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
        user = self.request.user
        if user.role == "ADMIN":
            return reverse_lazy("admin_dashboard")
        if user.role == "DOCTOR":
            return reverse_lazy("doctor_dashboard")
        return reverse_lazy("patient_dashboard")


@login_required
def patient_dashboard(request):
    return HttpResponse("Patient dashboard ✅")


@login_required
def doctor_dashboard(request):
    if request.user.role != "DOCTOR":
        return redirect("home")

    schedules = DoctorSchedule.objects.filter(doctor=request.user)

    if request.method == "POST":
        form = DoctorScheduleForm(request.POST)
        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.doctor = request.user
            schedule.save()
            return redirect("doctor_dashboard")
    else:
        form = DoctorScheduleForm()

    return render(request, "accounts/doctor_dashboard.html", {
        "form": form,
        "schedules": schedules
    })



@login_required
def admin_dashboard(request):
    return HttpResponse("Admin dashboard ✅")
