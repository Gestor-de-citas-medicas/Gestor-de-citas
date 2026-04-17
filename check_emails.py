"""
Script to verify email configuration and registered users.
"""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.core.mail import send_mail
from django.conf import settings
from accounts.models import User

print("EMAIL CONFIGURATION CHECK")
print("=" * 50)

# 1. Check configuration
print("\n1️⃣  EMAIL SETTINGS:")
print(f"   Backend:  {settings.EMAIL_BACKEND}")
print(f"   Host:     {settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
print(f"   User:     {settings.EMAIL_HOST_USER}")

# 2. List users
print("\n2️⃣  REGISTERED USERS:")
users = User.objects.all()
role_labels = {
    "PATIENT": "👤 Patient",
    "DOCTOR":  "👨‍⚕️  Doctor",
    "ADMIN":   "⚙️  Admin",
}
for i, user in enumerate(users):
    email_status = "✓ Has email" if user.email else "❌ NO EMAIL"
    print(f"   [{i}] {user.username} ({role_labels.get(user.role, user.role)}) — {email_status}")

# 3. Send test email
print("\n3️⃣  SEND TEST EMAIL:")
choice = input("\n   Enter user number (or 'exit'): ").strip()
if choice != "exit":
    try:
        user = users[int(choice)]
        if user.email:
            print(f"\n📧 Sending test email to {user.email}...")
            send_mail(
                subject="Test Email — Medical Appointment Manager",
                message="This is a test email to verify the email system is working correctly.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            print(f"✓ Email sent successfully to {user.email}")
        else:
            print("❌ This user has no email address.")
    except Exception as e:
        print(f"❌ Error: {e}")

print("\nVERIFICATION COMPLETE")
