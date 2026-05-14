import re

with open('chatbot/tools.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace Spanish tool descriptions
content = content.replace('"Retorna la lista de especialidades médicas disponibles en el sistema."', '"Returns the list of available medical specialties in the system."')
content = content.replace('"Busca doctores activos por especialidad médica."', '"Searches for active doctors by medical specialty."')
content = content.replace('"Código de especialidad. Ejemplo: CARDIOLOGY, GENERAL, PEDIATRICS"', '"Specialty code. Example: CARDIOLOGY, GENERAL, PEDIATRICS"')
content = content.replace('"Obtiene los slots de tiempo disponibles de un doctor en una fecha específica."', '"Gets the available time slots for a doctor on a specific date."')
content = content.replace('"ID del doctor (user)."', '"Doctor ID (user)."')
content = content.replace('"Fecha en formato YYYY-MM-DD."', '"Date in YYYY-MM-DD format."')
content = content.replace('"Crea una cita médica para el paciente autenticado."', '"Creates a medical appointment for the authenticated patient."')
content = content.replace('"ID del doctor."', '"Doctor ID."')
content = content.replace('"Fecha de la cita en formato YYYY-MM-DD."', '"Appointment date in YYYY-MM-DD format."')
content = content.replace('"Hora de inicio en formato HH:MM (24h). Ej: 09:00"', '"Start time in HH:MM (24h) format. Ex: 09:00"')
content = content.replace('"Hora de fin en formato HH:MM (24h). Ej: 09:30"', '"End time in HH:MM (24h) format. Ex: 09:30"')
content = content.replace('"Motivo de la consulta (opcional)."', '"Reason for visit (optional)."')
content = content.replace('"Lista las citas del paciente autenticado (próximas y pasadas)."', '"Lists the authenticated patient appointments (upcoming and past)."')
content = content.replace('"Si es true, solo retorna citas futuras."', '"If true, returns only upcoming appointments."')
content = content.replace('"Cancela una cita del paciente autenticado."', '"Cancels an appointment for the authenticated patient."')
content = content.replace('"ID de la cita a cancelar."', '"ID of the appointment to cancel."')

# Replace error messages and logic strings
content = content.replace('f"No hay doctores disponibles para la especialidad \'{specialty}\'."', 'f"No doctors available for specialty \'{specialty}\'."')
content = content.replace('"Formato de fecha inválido. Usa YYYY-MM-DD."', '"Invalid date format. Use YYYY-MM-DD."')
content = content.replace('"No puedes agendar citas en fechas pasadas."', '"You cannot book appointments in the past."')
content = content.replace('"Doctor no encontrado."', '"Doctor not found."')
content = content.replace('"El doctor no tiene horario disponible para ese día de la semana."', '"The doctor has no available schedule for that day of the week."')
content = content.replace('"No hay horarios disponibles para esa fecha."', '"No available schedules for that date."')
content = content.replace('"Formato de fecha inválido."', '"Invalid date format."')
content = content.replace('"Formato de hora inválido. Usa HH:MM."', '"Invalid time format. Use HH:MM."')
content = content.replace('"Ese horario ya no está disponible. Selecciona otro."', '"That time slot is no longer available. Please select another one."')
content = content.replace('f"No se pudo crear la cita: {str(e)}"', 'f"Could not create the appointment: {str(e)}"')
content = content.replace('"Pendiente de confirmación"', '"Pending confirmation"')
content = content.replace('"Cita no encontrada o no tienes permiso para cancelarla."', '"Appointment not found or you do not have permission to cancel it."')
content = content.replace('"Esa cita ya está cancelada."', '"That appointment is already cancelled."')
content = content.replace('"No puedes cancelar una cita ya completada."', '"You cannot cancel an already completed appointment."')
content = content.replace('f"Cita del {appointment.date} a las {str(appointment.start_time)[:5]} cancelada exitosamente."', 'f"Appointment on {appointment.date} at {str(appointment.start_time)[:5]} cancelled successfully."')
content = content.replace('f"Herramienta desconocida: {tool_name}"', 'f"Unknown tool: {tool_name}"')
content = content.replace('f"Error ejecutando {tool_name}: {str(e)}"', 'f"Error executing {tool_name}: {str(e)}"')

with open('chatbot/tools.py', 'w', encoding='utf-8') as f:
    f.write(content)
