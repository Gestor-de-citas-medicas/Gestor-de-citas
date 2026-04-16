#!/usr/bin/env python
"""
Script para verificar la configuración de emails y los usuarios registrados.
Ejecutar: python check_emails.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings
from django.core.mail import send_mail
from accounts.models import User

print("\n" + "="*70)
print("VERIFICACIÓN DE CONFIGURACIÓN DE EMAILS")
print("="*70)

# 1. Verificar configuración
print("\n1️⃣  CONFIGURACIÓN DE EMAIL:")
print(f"   Backend: {settings.EMAIL_BACKEND}")
print(f"   From Email: {settings.DEFAULT_FROM_EMAIL}")

# 2. Verificar usuarios
print("\n2️⃣  USUARIOS REGISTRADOS:")
users = User.objects.all()
print(f"   Total de usuarios: {users.count()}\n")

for user in users:
    role_display = {
        "PATIENT": "👤 Paciente",
        "DOCTOR": "👨‍⚕️  Doctor",
        "ADMIN": "⚙️  Admin"
    }.get(user.role, user.role)
    
    email_status = "✓ Con email" if user.email else "❌ SIN EMAIL"
    print(f"   {role_display}: {user.username} - {user.first_name} {user.last_name}")
    print(f"      Email: {user.email or 'NO ASIGNADO'} {email_status}")

# 3. Enviar email de prueba
print("\n3️⃣  ENVÍO DE EMAIL DE PRUEBA:")
print("\n   Selecciona usuarios para enviarles un email de prueba:")
for i, user in enumerate(users, 1):
    print(f"   {i}. {user.username} ({user.email or 'SIN EMAIL'})")

choice = input("\n   Ingresa el número del usuario (o 'salir'): ").strip()
if choice.lower() != 'salir' and choice.isdigit():
    idx = int(choice) - 1
    if 0 <= idx < len(users):
        user = users[idx]
        if not user.email:
            print(f"\n❌ El usuario {user.username} no tiene email registrado.")
        else:
            print(f"\n📧 Enviando email de prueba a {user.email}...")
            try:
                send_mail(
                    subject="Email de Prueba - Sistema de Gestión de Citas",
                    message="Este es un email de prueba para verificar que el sistema de emails está funcionando correctamente.",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
                print(f"✓ Email enviado exitosamente a {user.email}")
            except Exception as e:
                print(f"❌ Error al enviar email: {str(e)}")

print("\n" + "="*70)
print("FIN DE VERIFICACIÓN")
print("="*70 + "\n")
