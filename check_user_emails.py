#!/usr/bin/env python
"""
Verifica si los usuarios tienen email guardado en la BD
Ejecutar: python check_user_emails.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

print("\n" + "="*60)
print("VERIFICACIÓN DE USUARIOS Y CORREOS EN LA BD")
print("="*60)

users = User.objects.all()

if not users.exists():
    print("\n❌ NO HAY USUARIOS EN LA BD")
else:
    print(f"\nTotal de usuarios: {users.count()}\n")
    
    for user in users:
        print(f"Usuario: {user.username}")
        print(f"  Nombre: {user.first_name} {user.last_name}")
        print(f"  Email: {user.email if user.email else '❌ VACÍO'}")
        print(f"  Rol: {user.role}")
        print(f"  is_active: {user.is_active}")
        print()

# Específicamente pacientes
print("="*60)
print("PACIENTES CON EMAIL:")
print("="*60)
patients = User.objects.filter(role='PATIENT')
for p in patients:
    has_email = "✅" if p.email else "❌"
    print(f"{has_email} {p.username} -> {p.email}")

# Específicamente doctores
print("\n" + "="*60)
print("DOCTORES CON EMAIL:")
print("="*60)
doctors = User.objects.filter(role='DOCTOR')
for d in doctors:
    has_email = "✅" if d.email else "❌"
    print(f"{has_email} {d.username} -> {d.email}")
