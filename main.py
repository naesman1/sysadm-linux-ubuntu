import psutil
from flask import Flask, jsonify, render_template
import os
import datetime
import logging
import smtplib
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

# --- 3. FUNCIONES DE LÓGICA DE SISTEMA ---

def get_system_errors():
    logging.info("Escaneando syslog...")
    errors = []
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r") as f:
                lines = f.readlines()[-50:]
                for line in lines:
                    if any(key in line.upper() for key in KEYWORDS):
                        errors.append(line.strip())
        except Exception as e:
            logging.error(f"Error al leer syslog: {e}")
            return [f"Error de lectura: {e}"]
    else:
        return ["Syslog no encontrado."]
    return errors

def get_all_metrics():
    logging.info("Recolectando métricas generales...")
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory().percent
    
    disks = []
    for part in psutil.disk_partitions():
        if 'loop' not in part.device and 'tmpfs' not in part.fstype:
            try:
                usage = psutil.disk_usage(part.mountpoint)
                disks.append({
                    "mountpoint": part.mountpoint,
                    "total_gb": round(usage.total / (1024**3), 2),
                    "used_percent": usage.percent
                })
            except Exception:
                continue

    return {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "OK" if cpu < 80 else "CRITICAL",
        "metrics": {"cpu_usage_percent": cpu, "ram_usage_percent": ram},
        "storage": disks,
        "recent_errors": get_system_errors()
    }

# --- 4. FUNCIONES DE REPORTE Y ENVÍO ---

def save_report_to_file(data):
    """Genera el HTML y lo guarda en la carpeta 'reportes'"""
    with app.app_context():
        report_html = render_template('report.html', data=data)
        if not os.path.exists('reportes'):
            os.makedirs('reportes')
        
        filename = f"reportes/reporte_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        with open(filename, "w") as f:
            f.write(report_html)
        
        logging.info(f"Reporte guardado en: {filename}")
        return report_html, filename

def send_email_report(html_content):
    """Envía el reporte por correo usando variables de entorno"""
    SENDER_EMAIL = os.getenv("SENDER_EMAIL")
    SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
    RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")

    if not all([SENDER_EMAIL, SENDER_PASSWORD, RECEIVER_EMAIL]):
        logging.warning("Correo no enviado: Faltan credenciales (Variables de entorno).")
        return

    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL
    msg['Subject'] = f"🚀 SysHealth Report - {datetime.datetime.now().strftime('%d/%m/%Y')}"
    msg.attach(MIMEText(html_content, 'html'))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        server.quit()
        logging.info("Correo enviado exitosamente.")
    except Exception as e:
        logging.error(f"Error SMTP: {e}")

# --- 5. RUTAS DE FLASK ---

@app.route('/')
def index():
    return render_template('report.html', data=get_all_metrics())

@app.route('/api/health')
def api_health():
    return jsonify(get_all_metrics())

@app.route('/generate-report')
def generate_now():
    data = get_all_metrics()
    html, path = save_report_to_file(data)
    # send_email_report(html) # Descomentar cuando tengas las variables de entorno
    return f"Reporte generado exitosamente en: {path}"

# --- 6. EJECUCIÓN ---

if __name__ == '__main__':
    logging.info("Iniciando Agente SysAdmin en puerto 5000...")
    app.run(host='0.0.0.0', port=5000, debug=True)