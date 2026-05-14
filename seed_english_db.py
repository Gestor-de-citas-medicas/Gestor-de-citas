import os
import sys
import django
from datetime import time
import random

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.hashers import make_password
from accounts.models import User, DoctorProfile, DoctorSchedule
from appointments.models import Appointment

def run_seed():
    print("Starting English dummy data seed (50 doctors)...")

    # Clear previous doctors
    print("Cleaning up previous doctors...")
    User.objects.filter(role=User.Roles.DOCTOR).delete()

    first_names = [
        "James", "John", "Robert", "Michael", "William", "David", "Richard", "Joseph", "Thomas", "Charles",
        "Mary", "Patricia", "Jennifer", "Linda", "Elizabeth", "Barbara", "Susan", "Jessica", "Sarah", "Karen",
        "Christopher", "Daniel", "Paul", "Mark", "Donald", "George", "Kenneth", "Steven", "Edward", "Brian",
        "Nancy", "Lisa", "Betty", "Margaret", "Sandra", "Ashley", "Kimberly", "Emily", "Donna", "Michelle",
        "Ronald", "Timothy", "Jason", "Jeffrey", "Ryan", "Jacob", "Gary", "Nicholas", "Eric", "Jonathan"
    ]
    
    last_names = [
        "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
        "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
        "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson",
        "Walker", "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores",
        "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell", "Carter", "Roberts"
    ]

    specialties = [choice[0] for choice in DoctorProfile.Specialty.choices]
    
    bios_by_specialty = {
        'CARDIOLOGY': "Board-certified Cardiologist with extensive experience in diagnosing and treating heart conditions, including coronary artery disease and heart rhythm disorders. Passionate about preventative heart care.",
        'DERMATOLOGY': "Expert Dermatologist specializing in medical and cosmetic skin treatments. Highly experienced in skin cancer screenings, acne management, and anti-aging therapies.",
        'ENDOCRINOLOGY': "Dedicated Endocrinologist focusing on hormonal imbalances, diabetes management, and thyroid disorders. Committed to providing comprehensive patient-centered care.",
        'GENERAL': "Compassionate General Practitioner with a holistic approach to primary care. Experienced in treating acute illnesses, managing chronic diseases, and promoting overall wellness.",
        'GYNECOLOGY': "Experienced Gynecologist providing comprehensive women's health services, from routine screenings and family planning to managing complex reproductive health issues.",
        'NEUROLOGY': "Specialized Neurologist dealing with disorders of the nervous system. Expertise in treating migraines, epilepsy, and neurodegenerative diseases with advanced therapeutic approaches.",
        'OPHTHALMOLOGY': "Skilled Ophthalmologist offering comprehensive eye care, including cataract surgery, glaucoma management, and routine vision correction procedures.",
        'ORTHOPEDICS': "Orthopedic Surgeon with expertise in sports medicine and joint replacement. Focused on helping patients regain mobility and live pain-free lives.",
        'OTOLARYNGOLOGY': "ENT Specialist treating conditions of the ear, nose, and throat. Experienced in managing sinus issues, hearing loss, and vocal cord disorders.",
        'PEDIATRICS': "Caring Pediatrician dedicated to the health and well-being of infants, children, and adolescents. Experienced in developmental monitoring and childhood immunizations.",
        'PSYCHIATRY': "Empathetic Psychiatrist providing comprehensive mental health care. Specializes in treating anxiety, depression, and mood disorders through a combination of therapy and medication management.",
        'UROLOGY': "Expert Urologist treating conditions of the male and female urinary tract, as well as the male reproductive system. Skilled in minimally invasive surgical techniques.",
        'OTHER': "Specialized medical professional dedicated to providing high-quality, patient-focused healthcare with years of clinical experience."
    }

    password = make_password("doctor1234")
    
    created_count = 0

    for i in range(50):
        fname = random.choice(first_names)
        lname = random.choice(last_names)
        full_name = f"{fname} {lname}"
        username = f"dr_{fname.lower()}_{lname.lower()}_{i}"
        email = f"{username}@mamp.com"
        specialty = random.choice(specialties)
        bio = bios_by_specialty.get(specialty, bios_by_specialty['OTHER'])
        license_num = f"MED-{specialty[:3].upper()}-{random.randint(1000, 9999)}"
        phone = f"+1 555 {random.randint(100, 999)} {random.randint(1000, 9999)}"

        # Create user
        user = User.objects.create(
            username=username,
            email=email,
            password=password,
            role=User.Roles.DOCTOR,
            first_name=fname,
            last_name=lname
        )
        
        # Create profile
        DoctorProfile.objects.create(
            user=user,
            full_name=full_name,
            specialty=specialty,
            license_number=license_num,
            bio=bio,
            phone=phone
        )

        # Create schedules
        for day in range(1, 6):
            # Morning
            DoctorSchedule.objects.create(
                doctor=user,
                day_number=day,
                start_time=time(8, 0),
                end_time=time(12, 0)
            )
            # Afternoon
            DoctorSchedule.objects.create(
                doctor=user,
                day_number=day,
                start_time=time(14, 0),
                end_time=time(18, 0)
            )
            
        created_count += 1
        if created_count % 10 == 0:
            print(f"Created {created_count} doctors...")

    print(f"\n[OK] Successfully created {created_count} English dummy doctors.")

if __name__ == "__main__":
    run_seed()
