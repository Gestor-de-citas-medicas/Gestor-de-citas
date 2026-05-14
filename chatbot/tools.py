"""
tools.py — Funciones que la IA puede invocar como "tool calls".
Cada función recibe `user` (request.user) para operar en nombre del paciente autenticado.
"""
from datetime import date, timedelta, datetime, time

from accounts.models import DoctorProfile, DoctorSchedule, ScheduleException, User
from appointments.models import Appointment


# ─────────────────────────────────────────────────────────────────
# Schema de herramientas — usado por los providers IA
# ─────────────────────────────────────────────────────────────────

TOOLS_SCHEMA = [
    {
        "name": "get_specialties",
        "description": "Retorna la lista de especialidades médicas disponibles en el sistema.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_doctors_by_specialty",
        "description": "Busca doctores activos por especialidad médica.",
        "parameters": {
            "type": "object",
            "properties": {
                "specialty": {
                    "type": "string",
                    "description": "Código de especialidad. Ejemplo: CARDIOLOGY, GENERAL, PEDIATRICS",
                }
            },
            "required": ["specialty"],
        },
    },
    {
        "name": "get_available_slots",
        "description": "Obtiene los slots de tiempo disponibles de un doctor en una fecha específica.",
        "parameters": {
            "type": "object",
            "properties": {
                "doctor_id": {
                    "type": "integer",
                    "description": "ID del doctor (user).",
                },
                "date": {
                    "type": "string",
                    "description": "Fecha en formato YYYY-MM-DD.",
                },
            },
            "required": ["doctor_id", "date"],
        },
    },
    {
        "name": "create_appointment",
        "description": "Crea una cita médica para el paciente autenticado.",
        "parameters": {
            "type": "object",
            "properties": {
                "doctor_id": {
                    "type": "integer",
                    "description": "ID del doctor.",
                },
                "date": {
                    "type": "string",
                    "description": "Fecha de la cita en formato YYYY-MM-DD.",
                },
                "start_time": {
                    "type": "string",
                    "description": "Hora de inicio en formato HH:MM (24h). Ej: 09:00",
                },
                "end_time": {
                    "type": "string",
                    "description": "Hora de fin en formato HH:MM (24h). Ej: 09:30",
                },
                "reason": {
                    "type": "string",
                    "description": "Motivo de la consulta (opcional).",
                },
            },
            "required": ["doctor_id", "date", "start_time", "end_time"],
        },
    },
    {
        "name": "get_my_appointments",
        "description": "Lista las citas del paciente autenticado (próximas y pasadas).",
        "parameters": {
            "type": "object",
            "properties": {
                "upcoming_only": {
                    "type": "boolean",
                    "description": "Si es true, solo retorna citas futuras.",
                }
            },
            "required": [],
        },
    },
    {
        "name": "cancel_appointment",
        "description": "Cancela una cita del paciente autenticado.",
        "parameters": {
            "type": "object",
            "properties": {
                "appointment_id": {
                    "type": "integer",
                    "description": "ID de la cita a cancelar.",
                }
            },
            "required": ["appointment_id"],
        },
    },
]


# ─────────────────────────────────────────────────────────────────
# Implementaciones de las herramientas
# ─────────────────────────────────────────────────────────────────

def get_specialties():
    """Retorna las especialidades que tienen al menos un doctor registrado."""
    profiles = DoctorProfile.objects.select_related("user").filter(
        user__role=User.Roles.DOCTOR
    )
    specialties = {}
    for p in profiles:
        code = p.specialty
        label = p.get_specialty_display()
        if code not in specialties:
            specialties[code] = label

    return {
        "specialties": [
            {"code": code, "label": label}
            for code, label in specialties.items()
        ]
    }


def get_doctors_by_specialty(specialty):
    """Retorna doctores con su perfil para una especialidad dada."""
    profiles = DoctorProfile.objects.select_related("user").filter(
        specialty=specialty.upper(),
        user__role=User.Roles.DOCTOR,
        user__is_active=True,
    )
    if not profiles.exists():
        return {"error": f"No hay doctores disponibles para la especialidad '{specialty}'."}

    doctors = []
    for p in profiles:
        doctors.append({
            "doctor_id": p.user.id,
            "name": p.full_name or p.user.get_full_name() or p.user.username,
            "specialty": p.get_specialty_display(),
            "license": p.license_number,
            "bio": p.bio[:200] if p.bio else "",
        })

    return {"doctors": doctors}


def get_available_slots(doctor_id, date_str):
    """
    Calcula los slots de 30 min disponibles de un doctor en una fecha.
    Considera: DoctorSchedule - Excepciones bloqueadas - Citas ya agendadas.
    """
    try:
        target_date = date.fromisoformat(date_str)
    except ValueError:
        return {"error": "Formato de fecha inválido. Usa YYYY-MM-DD."}

    if target_date < date.today():
        return {"error": "No puedes agendar citas en fechas pasadas."}

    try:
        doctor = User.objects.get(pk=doctor_id, role=User.Roles.DOCTOR)
    except User.DoesNotExist:
        return {"error": "Doctor no encontrado."}

    # Día de la semana: Python lunes=0, nuestro modelo domingo=0, lunes=1
    python_weekday = target_date.weekday()
    day_number = (python_weekday + 1) % 7

    schedules = DoctorSchedule.objects.filter(
        doctor=doctor, day_number=day_number, is_active=True
    )

    if not schedules.exists():
        return {"error": "El doctor no tiene horario disponible para ese día de la semana."}

    # Excepciones bloqueadas ese día
    blocked_exceptions = ScheduleException.objects.filter(
        doctor=doctor,
        date=target_date,
        type=ScheduleException.ExceptionType.BLOCKED,
    )

    # Citas ya existentes
    booked = Appointment.objects.filter(
        doctor=doctor,
        date=target_date,
        status__in=[Appointment.Status.PENDING, Appointment.Status.CONFIRMED],
    ).values_list("start_time", "end_time")
    booked_ranges = list(booked)

    def is_blocked(slot_start, slot_end):
        for exc in blocked_exceptions:
            if slot_start < exc.end_time and slot_end > exc.start_time:
                return True
        for b_start, b_end in booked_ranges:
            if slot_start < b_end and slot_end > b_start:
                return True
        return False

    slots = []
    for schedule in schedules:
        current = datetime.combine(target_date, schedule.start_time)
        end_dt = datetime.combine(target_date, schedule.end_time)
        delta = timedelta(minutes=30)

        while current + delta <= end_dt:
            slot_s = current.time()
            slot_e = (current + delta).time()
            if not is_blocked(slot_s, slot_e):
                slots.append({
                    "start_time": slot_s.strftime("%H:%M"),
                    "end_time": slot_e.strftime("%H:%M"),
                })
            current += delta

    if not slots:
        return {"error": "No hay horarios disponibles para esa fecha."}

    doctor_profile = getattr(doctor, "doctor_profile", None)
    doctor_display = doctor_profile.full_name if doctor_profile else doctor.username

    return {
        "doctor": doctor_display,
        "date": date_str,
        "slots": slots,
    }


def create_appointment(user, doctor_id, date_str, start_time_str, end_time_str, reason=""):
    """Crea una cita para el paciente `user`."""
    try:
        target_date = date.fromisoformat(date_str)
    except ValueError:
        return {"error": "Formato de fecha inválido."}

    try:
        start_t = time.fromisoformat(start_time_str)
        end_t = time.fromisoformat(end_time_str)
    except ValueError:
        return {"error": "Formato de hora inválido. Usa HH:MM."}

    try:
        doctor = User.objects.get(pk=doctor_id, role=User.Roles.DOCTOR)
    except User.DoesNotExist:
        return {"error": "Doctor no encontrado."}

    # Verificar conflicto
    conflict = Appointment.objects.filter(
        doctor=doctor,
        date=target_date,
        start_time=start_t,
        status__in=[Appointment.Status.PENDING, Appointment.Status.CONFIRMED],
    ).exists()
    if conflict:
        return {"error": "Ese horario ya no está disponible. Selecciona otro."}

    try:
        appointment = Appointment.objects.create(
            patient=user,
            doctor=doctor,
            date=target_date,
            start_time=start_t,
            end_time=end_t,
            reason=reason,
            status=Appointment.Status.PENDING,
        )
    except Exception as e:
        return {"error": f"No se pudo crear la cita: {str(e)}"}

    doctor_profile = getattr(doctor, "doctor_profile", None)
    doctor_name = doctor_profile.full_name if doctor_profile else doctor.username

    return {
        "success": True,
        "appointment_id": appointment.pk,
        "doctor": doctor_name,
        "date": date_str,
        "start_time": start_time_str,
        "end_time": end_time_str,
        "status": "Pendiente de confirmación",
    }


def get_my_appointments(user, upcoming_only=False):
    """Lista las citas del paciente."""
    qs = Appointment.objects.filter(patient=user).select_related("doctor")

    if upcoming_only:
        qs = qs.filter(date__gte=date.today()).exclude(status=Appointment.Status.CANCELLED)

    qs = qs.order_by("date", "start_time")

    appointments = []
    for a in qs[:10]:
        doctor_profile = getattr(a.doctor, "doctor_profile", None)
        doctor_name = doctor_profile.full_name if doctor_profile else a.doctor.username
        appointments.append({
            "id": a.pk,
            "doctor": doctor_name,
            "date": str(a.date),
            "start_time": str(a.start_time)[:5],
            "end_time": str(a.end_time)[:5],
            "status": a.get_status_display(),
            "reason": a.reason,
        })

    return {"appointments": appointments, "total": len(appointments)}


def cancel_appointment(user, appointment_id):
    """Cancela una cita del paciente autenticado."""
    try:
        appointment = Appointment.objects.get(pk=appointment_id, patient=user)
    except Appointment.DoesNotExist:
        return {"error": "Cita no encontrada o no tienes permiso para cancelarla."}

    if appointment.status == Appointment.Status.CANCELLED:
        return {"error": "Esa cita ya está cancelada."}

    if appointment.status == Appointment.Status.COMPLETED:
        return {"error": "No puedes cancelar una cita ya completada."}

    appointment.status = Appointment.Status.CANCELLED
    appointment.save(update_fields=["status", "updated_at"])

    return {
        "success": True,
        "message": f"Cita del {appointment.date} a las {str(appointment.start_time)[:5]} cancelada exitosamente.",
    }


# ─────────────────────────────────────────────────────────────────
# Dispatcher
# ─────────────────────────────────────────────────────────────────

def dispatch_tool(tool_name, tool_args, user):
    """Despacha la llamada al tool correcto. Siempre retorna un dict."""
    try:
        if tool_name == "get_specialties":
            return get_specialties()

        elif tool_name == "get_doctors_by_specialty":
            return get_doctors_by_specialty(tool_args.get("specialty", ""))

        elif tool_name == "get_available_slots":
            return get_available_slots(
                doctor_id=int(tool_args.get("doctor_id", 0)),
                date_str=tool_args.get("date", ""),
            )

        elif tool_name == "create_appointment":
            return create_appointment(
                user=user,
                doctor_id=int(tool_args.get("doctor_id", 0)),
                date_str=tool_args.get("date", ""),
                start_time_str=tool_args.get("start_time", ""),
                end_time_str=tool_args.get("end_time", ""),
                reason=tool_args.get("reason", ""),
            )

        elif tool_name == "get_my_appointments":
            return get_my_appointments(
                user=user,
                upcoming_only=tool_args.get("upcoming_only", False),
            )

        elif tool_name == "cancel_appointment":
            return cancel_appointment(
                user=user,
                appointment_id=int(tool_args.get("appointment_id", 0)),
            )

        else:
            return {"error": f"Herramienta desconocida: {tool_name}"}

    except Exception as e:
        return {"error": f"Error ejecutando {tool_name}: {str(e)}"}
