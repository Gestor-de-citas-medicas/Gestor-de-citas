# busqueda/models.py
# Los modelos Doctor y Disponibilidad han sido eliminados.
# La app busqueda ahora usa directamente los modelos reales:
#   - accounts.DoctorProfile  (datos del doctor)
#   - accounts.DoctorSchedule (horario semanal recurrente)
#   - accounts.ScheduleException (excepciones de horario)
#   - appointments.Appointment (citas existentes)
#
# Las tablas antiguas busqueda_doctor y busqueda_disponibilidad
# se eliminarán con la siguiente migración.
