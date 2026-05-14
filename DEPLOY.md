# 🚀 MAMP — Guía de Despliegue en AWS EC2

> **Documento dirigido a:** compañero de equipo encargado del despliegue.
> Sigue los pasos **en orden**. No te saltes ninguno.

---

## ✅ Checklist rápido (marca cada ítem al completarlo)

- [ ] Instancia EC2 lanzada (Ubuntu 22.04)
- [ ] Puertos 22, 80 y 8000 abiertos en el Security Group
- [ ] Conectado por SSH a la instancia
- [ ] Dependencias del sistema instaladas
- [ ] Repositorio clonado
- [ ] Entorno virtual creado y activado
- [ ] Dependencias Python instaladas (`pip install -r requirements.txt`)
- [ ] Archivo `.env` creado y configurado
- [ ] `collectstatic` ejecutado
- [ ] `migrate` ejecutado
- [ ] Superusuario creado
- [ ] Gunicorn corriendo correctamente
- [ ] Servicio systemd activo y habilitado
- [ ] (Opcional) Nginx configurado como proxy reverso
- [ ] App accesible desde el navegador 🎉

---

## PASO 0 — Qué necesitas antes de empezar

| Elemento | Dónde conseguirlo |
|---|---|
| Clave `.pem` de la instancia EC2 | Archivo descargado al crear la instancia en AWS |
| IP pública de la instancia | AWS Console → EC2 → Instances → Public IPv4 address |
| API Key del chatbot (Groq) | [console.groq.com](https://console.groq.com) → API Keys |
| Contraseña de App de Gmail | [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords) |

---

## PASO 1 — Crear y configurar la instancia EC2

1. Ve a **AWS Console → EC2 → Launch Instance**.
2. Configura:
   - **Nombre:** `mamp-server`
   - **AMI:** Ubuntu Server 22.04 LTS (Free Tier eligible)
   - **Instance type:** `t2.micro` (gratis) o `t2.small`
   - **Key pair:** Crea uno nuevo o selecciona uno existente. **Descarga el `.pem`**
3. En **Network settings → Security Group**, agrega estas reglas:

   | Type | Protocol | Port | Source |
   |---|---|---|---|
   | SSH | TCP | 22 | My IP |
   | HTTP | TCP | 80 | Anywhere (0.0.0.0/0) |
   | Custom TCP | TCP | 8000 | Anywhere (0.0.0.0/0) |

4. Haz clic en **Launch Instance** y espera ~1 minuto.
5. Anota la **IPv4 pública** de la instancia.

---

## PASO 2 — Conectarte a la instancia por SSH

Desde tu terminal local (macOS/Linux) o PowerShell/Git Bash (Windows):

```bash
# Dale permisos al archivo .pem (solo macOS/Linux)
chmod 400 tu-clave.pem

# Conéctate (reemplaza la ruta y la IP)
ssh -i tu-clave.pem ubuntu@<IP_PUBLICA_EC2>
```

> 💡 En Windows puedes usar **Git Bash** o **PuTTY** si SSH no funciona en PowerShell.

---

## PASO 3 — Instalar dependencias del sistema

Una vez dentro de la instancia EC2:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3 python3-pip python3-venv git -y
```

---

## PASO 4 — Clonar el repositorio

```bash
cd ~
git clone https://github.com/Gestor-de-citas-medicas/Gestor-de-citas.git
cd Gestor-de-citas
```

---

## PASO 5 — Crear entorno virtual e instalar dependencias

```bash
python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

> ⏳ Este paso tarda 1-2 minutos. Espera a que termine completamente.

---

## PASO 6 — Configurar las variables de entorno (`.env`)

```bash
cp .env.example .env
nano .env
```

Rellena **todos** los valores. El archivo debe quedar así:

```ini
# ── Django Core ─────────────────────────────────────────────────
DJANGO_SECRET_KEY=<pega aquí la clave generada abajo>
DEBUG=False
ALLOWED_HOSTS=<IP_PUBLICA_EC2>

# ── Email ────────────────────────────────────────────────────────
EMAIL_HOST_USER=mamp.medico@gmail.com
EMAIL_HOST_PASSWORD=<contraseña de app de Gmail>

# ── AI Chatbot ───────────────────────────────────────────────────
AI_PROVIDER=groq
AI_API_KEY=<tu API Key de Groq>
AI_MODEL=llama-3.1-8b-instant

# ── CSRF ─────────────────────────────────────────────────────────
CSRF_TRUSTED_ORIGINS=http://<IP_PUBLICA_EC2>
```

### Generar el SECRET_KEY

```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copia la clave que imprime y pégala en `DJANGO_SECRET_KEY=`.

Guarda el archivo: **Ctrl+O → Enter → Ctrl+X**

---

## PASO 7 — Preparar la aplicación

```bash
# Colectar archivos estáticos (CSS, JS, imágenes)
python manage.py collectstatic --noinput

# Aplicar migraciones de base de datos
python manage.py migrate

# Crear superusuario administrador
python manage.py createsuperuser
```

---

## PASO 8 — Probar con Gunicorn (verificación)

```bash
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3
```

Abre en tu navegador: `http://<IP_PUBLICA_EC2>:8000`

Deberías ver la aplicación corriendo. Presiona **Ctrl+C** para detenerla.

---

## PASO 9 — Configurar servicio systemd (arranque automático)

Esto hace que la app se inicie sola al reiniciar el servidor y se recupere si falla.

```bash
sudo nano /etc/systemd/system/mamp.service
```

Pega este contenido **exactamente** (no cambies nada salvo que tu usuario no sea `ubuntu`):

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

Guarda: **Ctrl+O → Enter → Ctrl+X**

Activa el servicio:

```bash
sudo systemctl daemon-reload
sudo systemctl enable mamp
sudo systemctl start mamp

# Verifica que esté corriendo (debe decir "active (running)")
sudo systemctl status mamp
```

---

## PASO 10 — (Opcional pero recomendado) Nginx como proxy reverso

Nginx permite acceder a la app por el puerto 80 (HTTP estándar) sin especificar `:8000`.

```bash
sudo apt install nginx -y

sudo nano /etc/nginx/sites-available/mamp
```

Pega:

```nginx
server {
    listen 80;
    server_name <IP_PUBLICA_EC2>;

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
sudo nginx -t           # Debe decir "syntax is ok"
sudo systemctl restart nginx
sudo systemctl enable nginx
```

La app ahora es accesible en `http://<IP_PUBLICA_EC2>` (sin necesidad de escribir `:8000`).

---

## 🔄 Cómo actualizar la app después de un nuevo commit

Cuando haya cambios en el repositorio:

```bash
cd ~/Gestor-de-citas
source venv/bin/activate

git pull origin Master

pip install -r requirements.txt      # Solo si cambiaron las dependencias
python manage.py migrate             # Solo si hay nuevas migraciones
python manage.py collectstatic --noinput

sudo systemctl restart mamp
```

---

## 🐛 Solución de problemas comunes

| Problema | Causa probable | Solución |
|---|---|---|
| `502 Bad Gateway` (Nginx) | Gunicorn no está corriendo | `sudo systemctl restart mamp` |
| `DisallowedHost` | IP no está en `ALLOWED_HOSTS` | Editar `.env` y reiniciar el servicio |
| Página sin estilos (sin CSS) | No se ejecutó `collectstatic` | `python manage.py collectstatic --noinput` |
| Error de base de datos | Migraciones pendientes | `python manage.py migrate` |
| `CSRF verification failed` | Falta `CSRF_TRUSTED_ORIGINS` | Agregar `http://<IP>` al `.env` |
| App no arranca tras reboot | Servicio no habilitado | `sudo systemctl enable mamp` |

---

## 📁 Comandos de diagnóstico útiles

```bash
# Ver logs de la app en tiempo real
sudo journalctl -u mamp -f

# Ver logs de Nginx
sudo tail -f /var/log/nginx/error.log

# Verificar estado de servicios
sudo systemctl status mamp
sudo systemctl status nginx

# Entrar al shell de Django
source ~/Gestor-de-citas/venv/bin/activate
cd ~/Gestor-de-citas
python manage.py shell
```

---

## 🔐 Credenciales de prueba (para verificar el despliegue)

Después de ejecutar el seed de datos de prueba:

```bash
python seed_english_db.py
```

Puedes usar estas cuentas de ejemplo (si el seed las genera). Si no, crea usuarios desde el panel admin en `http://<IP>/admin/`.

---

## 📞 Contacto

Si algo falla, contacta a tu compañero de equipo o revisa los logs con `journalctl -u mamp -f`.

---

*Guía generada para el despliegue académico de MAMP — Medical Appointment Management Platform.*
