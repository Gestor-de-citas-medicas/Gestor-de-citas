from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from .models import Doctor, Disponibilidad



def buscar_doctor(request):
    especialidad = request.GET.get("especialidad")
    doctores = Doctor.objects.all()

    if especialidad:
        doctores = doctores.filter(especialidad__icontains=especialidad)

    return render(request, "busqueda/buscar_doctor.html", {
        "doctores": doctores
    })


def disponibilidad(request, doctor_id):
    doctor = Doctor.objects.get(id=doctor_id)
    horarios = Disponibilidad.objects.filter(doctor=doctor)

    return render(request, "busqueda/disponibilidad.html", {
        "doctor": doctor,
        "horarios": horarios
    })
def disponibilidad_ajax(request, doctor_id):
    doctor = get_object_or_404(Doctor, id=doctor_id)
    # Usamos los campos correctos: fecha y hora
    horarios = Disponibilidad.objects.filter(doctor=doctor).order_by('fecha', 'hora')
    return render(request, "busqueda/tabla_disponibilidad.html", {
        "doctor": doctor,
        "horarios": horarios
    })