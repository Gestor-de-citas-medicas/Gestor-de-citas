"""
Script to verify users and their email addresses in the database.
"""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from accounts.models import User

print("USER & EMAIL VERIFICATION")
print("=" * 50)

users = User.objects.all()
print(f"\nTotal users: {users.count()}\n")

for user in users:
    print(f"  Username : {user.username}")
    print(f"  Role     : {user.role}")
    print(f"  Email    : {user.email if user.email else '❌ EMPTY'}")
    print()

# Patients specifically
print("\n--- PATIENTS ---")
for p in User.objects.filter(role="PATIENT"):
    has_email = "✅" if p.email else "❌"
    print(f"  {p.username} — {has_email} {p.email}")

# Doctors specifically
print("\n--- DOCTORS ---")
for d in User.objects.filter(role="DOCTOR"):
    has_email = "✅" if d.email else "❌"
    print(f"  {d.username} — {has_email} {d.email}")
