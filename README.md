# MAMP — Medical Appointment Management Platform

A web-based appointment management system built with Django. MAMP allows patients to search for doctors and book medical appointments, while doctors can manage their schedules and track their consultations. An integrated AI chatbot (powered by Groq / OpenAI / Gemini) helps users navigate the platform.

---

## ✨ Features

| Feature | Description |
|---|---|
| Role-based access | Separate dashboards for Patients, Doctors, and Admins |
| Doctor search | Browse by specialty and check real-time availability |
| Appointment booking | Select doctor, date, and available time slot |
| Lifecycle management | Statuses: Pending → Confirmed → Completed / Cancelled |
| Email notifications | Automated Gmail SMTP emails on every status change |
| Schedule management | Doctors configure weekly availability and block dates |
| Post-appointment reviews | Patients can rate and review completed appointments |
| AI Chatbot | Embedded assistant powered by Groq / OpenAI / Gemini |
| Profile management | All users can update or delete their personal information |

---

## 🖥️ Running Locally (Development)

### Prerequisites
- Python 3.10 or higher
- pip

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/Gestor-de-citas-medicas/Gestor-de-citas.git
cd Gestor-de-citas

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate          # macOS / Linux
# venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env from the template and fill in your values
cp .env.example .env
# → Edit .env with your SECRET_KEY, email credentials and AI API key

# 5. Apply migrations
python manage.py migrate

# 6. (Optional) Seed the database with sample data
python seed_english_db.py

# 7. Create an admin superuser
python manage.py createsuperuser

# 8. Run the development server
python manage.py runserver
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.

---

## ☁️ Deploying to AWS EC2 (Production)

### Step 1 — Launch an EC2 Instance

1. Go to **AWS Console → EC2 → Launch Instance**.
2. Choose **Ubuntu Server 22.04 LTS** (Free Tier eligible).
3. Select instance type: **t2.micro** (or larger).
4. Configure Security Group — open these ports:
   - **22** (SSH)
   - **80** (HTTP)
   - **8000** (Gunicorn — optional, can use Nginx on 80 instead)
5. Create / select a key pair and download the `.pem` file.
6. Launch the instance and note the **Public IPv4 address**.

---

### Step 2 — Connect to the Instance

```bash
# From your local machine (replace path and IP)
chmod 400 your-key.pem
ssh -i your-key.pem ubuntu@<EC2_PUBLIC_IP>
```

---

### Step 3 — Install System Dependencies

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3 python3-pip python3-venv git -y
```

---

### Step 4 — Clone the Repository

```bash
cd ~
git clone https://github.com/Gestor-de-citas-medicas/Gestor-de-citas.git
cd Gestor-de-citas
```

---

### Step 5 — Set Up Python Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

### Step 6 — Configure Environment Variables

```bash
cp .env.example .env
nano .env
```

Fill in **all** required values:

```ini
DJANGO_SECRET_KEY=<generate a secure key — see command below>
DEBUG=False
ALLOWED_HOSTS=<EC2_PUBLIC_IP>,<your-domain.com>

EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password

AI_PROVIDER=groq
AI_API_KEY=<your-groq-api-key>
AI_MODEL=llama-3.1-8b-instant

CSRF_TRUSTED_ORIGINS=http://<EC2_PUBLIC_IP>
```

> **Generate a SECRET_KEY:**
> ```bash
> python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
> ```

---

### Step 7 — Prepare the Application

```bash
# Collect static files (CSS, JS, images)
python manage.py collectstatic --noinput

# Apply database migrations
python manage.py migrate

# (Optional) Seed initial data
python seed_english_db.py

# Create admin superuser
python manage.py createsuperuser
```

---

### Step 8 — Run with Gunicorn

```bash
# Test Gunicorn works correctly
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3
```

Access the app at `http://<EC2_PUBLIC_IP>:8000`.

---

### Step 9 — Run as a Background Service (systemd)

Create a service file so the app starts automatically and restarts on failure:

```bash
sudo nano /etc/systemd/system/mamp.service
```

Paste this content (replace `ubuntu` if your user is different):

```ini
[Unit]
Description=MAMP Gunicorn Daemon
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/Gestor-de-citas
ExecStart=/home/ubuntu/Gestor-de-citas/venv/bin/gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3
EnvironmentFile=/home/ubuntu/Gestor-de-citas/.env
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable mamp
sudo systemctl start mamp
sudo systemctl status mamp   # Should show "active (running)"
```

---

### Step 10 — (Optional) Set Up Nginx as Reverse Proxy

Using Nginx on port 80 is cleaner than exposing port 8000 directly.

```bash
sudo apt install nginx -y

sudo nano /etc/nginx/sites-available/mamp
```

Paste:

```nginx
server {
    listen 80;
    server_name <EC2_PUBLIC_IP>;

    location /static/ {
        alias /home/ubuntu/Gestor-de-citas/staticfiles/;
    }

    location /media/ {
        alias /home/ubuntu/Gestor-de-citas/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/mamp /etc/nginx/sites-enabled/
sudo nginx -t        # Verify config
sudo systemctl restart nginx
```

The app is now available at `http://<EC2_PUBLIC_IP>` (port 80).

---

## 🗂️ Project Structure

```
Gestor-de-citas/
├── accounts/           # User model, roles, doctor profiles, schedule
├── appointments/       # Booking, status flow, reviews, email notifications
├── busqueda/           # Doctor search and availability display
├── chatbot/            # AI chatbot integration (Groq / OpenAI / Gemini)
├── config/             # Django settings, URLs, WSGI/ASGI
├── templates/          # Global base template and shared layouts
├── staticfiles/        # Collected static files (generated — do not edit)
├── manage.py
├── requirements.txt
├── Procfile            # Gunicorn start command
├── .env.example        # Environment variable template
└── README.md
```

---

## 📧 Email Configuration

The project uses **Gmail SMTP**. Set these in your `.env` file:

```ini
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password   # NOT your regular Gmail password
```

> Get a Gmail App Password at: [https://myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)

---

## 🤖 AI Chatbot Configuration

| Provider | `AI_PROVIDER` | Example `AI_MODEL` |
|---|---|---|
| Groq (free tier, fast) | `groq` | `llama-3.1-8b-instant` |
| OpenAI | `openai` | `gpt-4o-mini` |
| Google Gemini | `gemini` | `gemini-2.0-flash` |

---

## 👥 User Roles

| Role | Capabilities |
|---|---|
| Patient | Search doctors, book, cancel, leave reviews, edit profile |
| Doctor | View appointments, confirm/complete/cancel, manage schedule |
| Admin | Full access to all appointments and users |

---

## 📋 Quick Deployment Checklist

- [ ] EC2 instance running (Ubuntu 22.04)
- [ ] Ports 22, 80, 8000 open in Security Group
- [ ] Repository cloned
- [ ] Virtual environment created and dependencies installed
- [ ] `.env` file configured (never commit this file!)
- [ ] `python manage.py collectstatic` run
- [ ] `python manage.py migrate` run
- [ ] Superuser created
- [ ] Gunicorn service running (`sudo systemctl status mamp`)
- [ ] (Optional) Nginx configured and running

---

## 📄 License

This project was developed for academic purposes.
