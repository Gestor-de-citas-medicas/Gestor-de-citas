# MAMP — Medical Appointment Management Platform

A web-based appointment management system built with Django. MAMP allows patients to search for doctors and book medical appointments, while doctors can manage their schedules and track their consultations. The platform sends automated email notifications at every key step of the appointment lifecycle.

---

## Features

- **Role-based access** — separate dashboards and permissions for Patients, Doctors, and Admins
- **Doctor search** — patients can browse doctors by specialty and check availability
- **Appointment booking** — patients select a doctor, date, and available time slot
- **Appointment lifecycle management** — statuses: Pending → Confirmed → Completed / Cancelled
- **Email notifications** — automated emails on booking confirmation, status changes, and cancellations
- **Doctor schedule management** — doctors configure weekly availability and block specific dates
- **Post-appointment reviews** — patients can rate and review completed appointments
- **Profile management** — all users can update or delete their personal information

---

## Requirements

- Python 3.10 or higher
- pip

---

## Running the Project Locally

### 1. Clone or download the repository

```bash
git clone <repository-url>
cd Gestor-de-citas
```

Or extract the downloaded ZIP and open a terminal inside the `Gestor-de-citas` folder.

### 2. Create and activate a virtual environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Apply database migrations

```bash
python manage.py migrate
```

### 5. (Optional) Create a superuser for admin access

```bash
python manage.py createsuperuser
```

### 6. Start the development server

```bash
python manage.py runserver
```

Open your browser and navigate to [http://127.0.0.1:8000](http://127.0.0.1:8000).

---

## Project Structure

```
Gestor-de-citas/
├── accounts/          # User model, roles, doctor profiles, schedule management
├── appointments/      # Appointment booking, status flow, reviews, email notifications
├── busqueda/          # Doctor search and availability display
├── config/            # Django project settings, URLs, WSGI/ASGI
├── templates/         # Global base template and shared layout
├── manage.py
├── requirements.txt
└── README.md
```

---

## Email Configuration

The project uses Gmail SMTP to send notifications. Settings are located in `config/settings.py`:

```python
EMAIL_HOST      = "smtp.gmail.com"
EMAIL_PORT      = 587
EMAIL_USE_TLS   = True
EMAIL_HOST_USER = "your-email@gmail.com"
EMAIL_HOST_PASSWORD = "your-app-password"
```

> **Note:** Use a [Gmail App Password](https://support.google.com/accounts/answer/185833) — not your regular Gmail password.

---

## User Roles

| Role    | Capabilities |
|---------|-------------|
| Patient | Search doctors, book appointments, cancel, leave reviews, edit profile |
| Doctor  | View appointments, confirm/complete/cancel, manage schedule, edit profile |
| Admin   | Full access to all appointments and actions |

---

## License

This project was developed for academic purposes.
