import psutil
from flask import Flask, jsonify, render_template
import os
import datetime
import logging
import smtplib
import subprocess
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)

# --- 1. CONFIGURACIÓN DE LOGS ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("ejecucion_agente.log"),
        logging.StreamHandler()
    ]
)

# --- 2. VARIABLES DE CONFIGURACIÓN ---
LOG_FILE = "/var/log/syslog" 
KEYWORDS = ["ERROR", "FAILED", "CRITICAL", "PANIC", "DENIED"]
SERVICES = ["ssh", "docker", "nginx", "mysql"] # Asegúrate de que existan en tu sistema
BACKUP_PATH = "/home/mike/backups"

# --- 3. LÓGICA DE MONITOREO ---

def get_system_errors():
    errors = []
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r") as f:
                lines = f.readlines()[-50:]
                for line in lines:
                    if any(key in line.upper() for key in KEYWORDS):
                        errors.append(line.strip())
        except Exception as e:
            logging.error(f"Error syslog: {e}")
    return errors

def check_services():
    logging.info("Verificando servicios críticos...")
    status = {}
    for service in SERVICES:
        try:
            # Ejecutamos el comando con un timeout para que no se congele
            cmd = subprocess.run(['systemctl', 'is-active', service], capture_output=True, text=True, timeout=5)
            status[service] = cmd.stdout.strip()
        except FileNotFoundError:
            status[service] = "systemctl no instalado"
        except Exception as e:
            logging.error(f"Error al chequear {service}: {e}")
            status[service] = "Error"
    return status

def get_security_info():
    failed_logins = 0
    auth_log = "/var/log/auth.log"
    if os.path.exists(auth_log):
        # Contamos líneas con "Failed password"
        cmd = subprocess.run(f"grep -c 'Failed password' {auth_log}", shell=True, capture_output=True, text=True)
        failed_logins = cmd.stdout.strip() or "0"

    try:
        # Simulación de parches pendientes
        cmd = subprocess.run(['apt', 'list', '--upgradable'], capture_output=True, text=True)
        patches = len(cmd.stdout.strip().split('\n')) - 1
    except:
        patches = "N/A"

    return {"failed_logins": failed_logins, "pending_patches": max(0, int(patches) if isinstance(patches, int) else 0)}

def verify_backups():
    today = datetime.datetime.now().strftime("%Y%m%d")
    if os.path.exists(BACKUP_PATH):
        files = os.listdir(BACKUP_PATH)
        exists = any(today in f for f in files)
        return "OK" if exists else "FALTA BACKUP HOY"
    return "RUTA NO ENCONTRADA"

def get_all_metrics():
    """Consolida TODA la información para el reporte"""
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory().percent
    
    # Discos
    disks = []
    for part in psutil.disk_partitions():
        if 'loop' not in part.device and 'tmpfs' not in part.fstype:
            try:
                usage = psutil.disk_usage(part.mountpoint)
                disks.append({
                    "mountpoint": part.mountpoint,
                    "used_percent": usage.percent,
                    "total_gb": round(usage.total / (1024**3), 2)
                })
            except: continue

    return {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "OK" if cpu < 80 else "WARNING",
        "metrics": {"cpu": cpu, "ram": ram},
        "storage": disks,
        "services": check_services(),
        "security": get_security_info(),
        "backups": verify_backups(),
        "recent_errors": get_system_errors()
    }

# --- 4. REPORTE Y CORREO ---

def save_report_to_file(data):
    with app.app_context():
        report_html = render_template('report.html', data=data)
        if not os.path.exists('reportes'): os.makedirs('reportes')
        filename = f"reportes/reporte_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        with open(filename, "w") as f:
            f.write(report_html)
        return report_html, filename

def send_email_report(html_content):
    # NOTA: En os.getenv va el nombre de la VARIABLE, no el valor directamente.
    # Para pruebas rápidas, puedes hardcodearlos así:
    SENDER_EMAIL = "naesaman1@gmail.com"
    SENDER_PASSWORD = "erylectxxculzhgh" # Usa 'Contraseña de Aplicación', no tu clave normal
    RECEIVER_EMAIL = "naesman1@hotmail.com"

    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL
    msg['Subject'] = f"🚀 SysAdmin Report - {datetime.datetime.now().strftime('%d/%m/%Y')}"
    msg.attach(MIMEText(html_content, 'html'))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        server.quit()
        logging.info("Correo enviado.")
    except Exception as e:
        logging.error(f"Error enviando correo: {e}")

# --- 5. RUTAS ---

@app.route('/')
def index():
    return render_template('report.html', data=get_all_metrics())

@app.route('/generate-report')
def generate_now():
    data = get_all_metrics()
    html, path = save_report_to_file(data)
    send_email_report(html) 
    return f"Reporte generado y enviado. Guardado en: {path}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)