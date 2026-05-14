import os
import sys
import django
from datetime import time

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.hashers import make_password
from accounts.models import User, DoctorProfile, DoctorSchedule
from appointments.models import Appointment

def run_seed():
    print("Iniciando carga de datos dummy reales para MAMP...")

    # Limpiar datos anteriores (opcional, pero ayuda a tener un entorno limpio)
    print("Limpiando doctores anteriores...")
    User.objects.filter(role=User.Roles.DOCTOR).delete()

    # Datos de los doctores a crear
    doctors_data = [
        {
            "username": "dr_mendoza",
            "email": "mendoza@mamp.com",
            "full_name": "Carlos Mendoza",
            "specialty": DoctorProfile.Specialty.CARDIOLOGY,
            "license": "MED-CARD-9938",
            "bio": "Especialista en cardiología clínica y ecocardiografía con más de 15 años de experiencia en el Hospital Central.",
            "phone": "+57 300 123 4567"
        },
        {
            "username": "dra_gomez",
            "email": "gomez@mamp.com",
            "full_name": "Laura Gómez",
            "specialty": DoctorProfile.Specialty.PEDIATRICS,
            "license": "MED-PED-2241",
            "bio": "Pediatra con subespecialidad en neonatología. Apasionada por el cuidado y desarrollo integral de los niños.",
            "phone": "+57 310 987 6543"
        },
        {
            "username": "dr_silva",
            "email": "silva@mamp.com",
            "full_name": "Andrés Silva",
            "specialty": DoctorProfile.Specialty.NEUROLOGY,
            "license": "MED-NEU-5512",
            "bio": "Neurólogo especialista en trastornos del movimiento y enfermedades neurodegenerativas.",
            "phone": "+57 315 444 3322"
        },
        {
            "username": "dra_rojas",
            "email": "rojas@mamp.com",
            "full_name": "Valentina Rojas",
            "specialty": DoctorProfile.Specialty.DERMATOLOGY,
            "license": "MED-DER-7761",
            "bio": "Dermatóloga clínica y estética. Experta en tratamientos de acné, manchas y rejuvenecimiento facial.",
            "phone": "+57 320 888 7766"
        },
        {
            "username": "dr_perez",
            "email": "perez@mamp.com",
            "full_name": "Juan Pérez",
            "specialty": DoctorProfile.Specialty.GENERAL,
            "license": "MED-GEN-1102",
            "bio": "Médico general con amplio enfoque en medicina preventiva y salud familiar.",
            "phone": "+57 301 222 3344"
        }
    ]

    password = make_password("doctor1234")

    for data in doctors_data:
        # Crear usuario
        user = User.objects.create(
            username=data["username"],
            email=data["email"],
            password=password,
            role=User.Roles.DOCTOR,
            first_name=data["full_name"].split()[0],
            last_name=" ".join(data["full_name"].split()[1:])
        )
        
        # Crear perfil
        DoctorProfile.objects.create(
            user=user,
            full_name=data["full_name"],
            specialty=data["specialty"],
            license_number=data["license"],
            bio=data["bio"],
            phone=data["phone"]
        )

        # Crear horarios (Lunes a Viernes, de 8am a 12pm y de 2pm a 6pm)
        # 1=Lunes, 2=Martes, 3=Miércoles, 4=Jueves, 5=Viernes
        for day in range(1, 6):
            # Turno mañana
            DoctorSchedule.objects.create(
                doctor=user,
                day_number=day,
                start_time=time(8, 0),
                end_time=time(12, 0)
            )
            # Turno tarde
            DoctorSchedule.objects.create(
                doctor=user,
                day_number=day,
                start_time=time(14, 0),
                end_time=time(18, 0)
            )
            
        print(f"[OK] Creado Dr. {data['full_name']} ({data['specialty']}) con sus horarios.")

    # Asegurarnos de que el paciente de prueba existe
    patient_username = "paciente1"
    if not User.objects.filter(username=patient_username).exists():
        User.objects.create(
            username=patient_username,
            email="paciente1@mamp.com",
            password=make_password("test1234"),
            role=User.Roles.PATIENT,
            first_name="Paciente",
            last_name="Prueba"
        )
        print("[OK] Creado paciente de prueba (paciente1).")

    print("\n[OK] Datos dummy cargados exitosamente!")
    print("Puedes loguearte como paciente con: paciente1 / test1234")
    print("Puedes loguearte como cualquier doctor con su username (ej. dr_mendoza) / doctor1234")

if __name__ == "__main__":
    run_seed()
