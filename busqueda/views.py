from django.shortcuts import render
from django.db.models import Q
from django.http import JsonResponse

from datetime import date, timedelta, datetime

from accounts.models import DoctorProfile, DoctorSchedule


# 🔍 BÚSQUEDA DE DOCTORES
def buscar_doctores(request):
    query = request.GET.get('especialidad', '')
    doctores = DoctorProfile.objects.select_related('user')

    if query:
        palabras = query.split()

        filtros = Q()
        for palabra in palabras:
            filtros |= Q(full_name__icontains=palabra)
            filtros |= Q(specialty__icontains=palabra)

        doctores = doctores.filter(filtros)

    return render(request, 'busqueda/buscar_Doctor.html', {
        'doctores': doctores,
        'query': query
    })


# ⚡ DISPONIBILIDAD AJAX (FIX REAL COMPLETO)
def disponibilidad_ajax(request, doctor_id):
    horarios = DoctorSchedule.objects.filter(
        doctor_id=doctor_id,
        is_active=True
    )

    data = []

    today = date.today()
    end = today + timedelta(days=5)

    current = today

    while current <= end:

        for h in horarios:
            if current.weekday() == h.day_number:

                # 🔥 FIX 1: limpiar minutos raros
                hora = datetime.combine(current, h.start_time).replace(minute=0, second=0)

                # 🔥 FIX 2: evitar bucles incorrectos
                while hora.time() < h.end_time:

                    data.append({
                        "fecha": current.strftime("%Y-%m-%d"),
                        "hora": hora.strftime("%H:%M")
                    })

                    hora += timedelta(hours=1)

        current += timedelta(days=1)

    return JsonResponse(data, safe=False)


# 📄 DISPONIBILIDAD HTML (opcional)
def disponibilidad(request, doctor_id):
    horarios = DoctorSchedule.objects.filter(
        doctor_id=doctor_id,
        is_active=True
    )

    return render(request, 'busqueda/disponibilidad.html', {
        'disponibilidad': horarios
    })