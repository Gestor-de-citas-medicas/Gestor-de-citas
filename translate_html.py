import os
import glob
import re

replacements = {
    "Gestor de Citas Médicas": "Medical Appointment Manager",
    "Gestor de Citas": "Appointment Manager",
    "Agendar Cita": "Book Appointment",
    "Mis Citas": "My Appointments",
    "Buscar Doctor": "Find Doctor",
    "Doctores": "Doctors",
    "Mi Perfil": "My Profile",
    "Panel Médico": "Doctor Dashboard",
    "Cerrar Sesión": "Logout",
    "Iniciar Sesión": "Login",
    "Registrarse": "Register",
    "Plataforma de Citas Médicas": "Medical Appointment Platform",
    "Especialidad": "Specialty",
    "Buscar por especialidad...": "Search by specialty...",
    "Buscar": "Search",
    "Ver Disponibilidad": "View Availability",
    "No hay doctores registrados con esa especialidad.": "No doctors registered with that specialty.",
    "No se encontraron doctores.": "No doctors found.",
    "Nombre": "Name",
    "Licencia": "License",
    "Correo": "Email",
    "Contraseña": "Password",
    "Confirmar contraseña": "Confirm Password",
    "Ingresar": "Sign In",
    "Crear cuenta": "Create account",
    "¿Eres paciente o doctor?": "Are you a patient or doctor?",
    "Paciente": "Patient",
    "Doctor": "Doctor",
    "Registrar Paciente": "Register Patient",
    "Registrar Doctor": "Register Doctor",
    "Número de Licencia": "License Number",
    "Biografía": "Biography",
    "Actualizar Perfil": "Update Profile",
    "Guardar Cambios": "Save Changes",
    "Citas Pendientes": "Pending Appointments",
    "Citas Confirmadas": "Confirmed Appointments",
    "Citas Completadas": "Completed Appointments",
    "Citas Canceladas": "Cancelled Appointments",
    "Estado": "Status",
    "Fecha": "Date",
    "Hora": "Time",
    "Motivo": "Reason",
    "Paciente": "Patient",
    "Acciones": "Actions",
    "Confirmar": "Confirm",
    "Completar": "Complete",
    "Cancelar": "Cancel",
    "Cancelar Cita": "Cancel Appointment",
    "¿Estás seguro que deseas cancelar esta cita?": "Are you sure you want to cancel this appointment?",
    "Sí, Cancelar": "Yes, Cancel",
    "Volver": "Back",
    "Nueva Cita": "New Appointment",
    "Agendar": "Book",
    "Selecciona un doctor": "Select a doctor",
    "Selecciona una fecha": "Select a date",
    "Horarios Disponibles": "Available Slots",
    "No hay horarios disponibles.": "No slots available.",
    "Dejar Reseña": "Leave Review",
    "Reseñas": "Reviews",
    "Calificación": "Rating",
    "Comentario": "Comment",
    "Enviar Reseña": "Submit Review",
    "Asistente MAMP": "MAMP Assistant",
    "Escribe un mensaje...": "Type a message...",
    "Hola, soy tu asistente médico virtual. ¿En qué te puedo ayudar hoy?": "Hello, I am your virtual medical assistant. How can I help you today?",
    "Menú": "Menu",
    "Bienvenido": "Welcome",
    "No tienes citas próximas.": "You have no upcoming appointments.",
    "No tienes citas pasadas.": "You have no past appointments.",
    "Citas Próximas": "Upcoming Appointments",
    "Historial de Citas": "Appointment History",
    "Perfil": "Profile",
    "Especialidades": "Specialties",
    "Todas": "All",
    "Filtrar": "Filter",
    "Siguiente": "Next",
    "Anterior": "Previous",
    "Lunes": "Monday",
    "Martes": "Tuesday",
    "Miércoles": "Wednesday",
    "Jueves": "Thursday",
    "Viernes": "Friday",
    "Sábado": "Saturday",
    "Domingo": "Sunday",
    "Enero": "January",
    "Febrero": "February",
    "Marzo": "March",
    "Abril": "April",
    "Mayo": "May",
    "Junio": "June",
    "Julio": "July",
    "Agosto": "August",
    "Septiembre": "September",
    "Octubre": "October",
    "Noviembre": "November",
    "Diciembre": "December",
    "Teléfono": "Phone",
    "Dirección": "Address",
}

def translate_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    new_content = content
    for es, en in replacements.items():
        new_content = new_content.replace(es, en)
        
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Translated {filepath}")

for root, _, files in os.walk('.'):
    if 'venv' in root:
        continue
    for file in files:
        if file.endswith('.html'):
            translate_file(os.path.join(root, file))

