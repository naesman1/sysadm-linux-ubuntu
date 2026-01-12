import psutil
from flask import Flask, jsonify, render_template
import os
import datetime
import logging # 1. Importamos la librería de logging

app = Flask(__name__)

# 2. CONFIGURACIÓN DE LOGS
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("ejecucion_agente.log"), # Guarda en archivo
        logging.StreamHandler() # Muestra en consola (ideal para Docker)
    ]
)

LOG_FILE = "/var/log/syslog" 
KEYWORDS = ["ERROR", "FAILED", "CRITICAL", "PANIC", "DENIED"]

def get_system_errors():
    logging.info("Iniciando escaneo de logs del sistema...")
    errors = []
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r") as f:
                lines = f.readlines()[-50:]
                for line in lines:
                    if any(key in line.upper() for key in KEYWORDS):
                        errors.append(line.strip())
            logging.info(f"Escaneo completado. Se encontraron {len(errors)} errores.")
        except Exception as e:
            logging.error(f"Error al leer syslog: {str(e)}")
            return [f"No se pudo leer el log: {str(e)}"]
    else:
        logging.warning(f"Archivo {LOG_FILE} no encontrado en este sistema.")
        return ["Archivo syslog no encontrado."]
    return errors

def get_all_metrics():
    logging.info("Recolectando métricas de hardware...")
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory().percent
    
    # ... (el resto del código de discos igual)
    logging.info(f"Métricas obtenidas: CPU {cpu}%, RAM {ram}%")
    
    return {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "OK" if cpu < 80 else "CRITICAL",
        "metrics": {"cpu_usage_percent": cpu, "ram_usage_percent": ram},
        "storage": [], # Simplificado para el ejemplo
        "recent_errors": get_system_errors()
    }

@app.route('/')
def index():
    logging.info("Acceso a la ruta visual (HTML)")
    data = get_all_metrics()
    return render_template('report.html', data=data)

@app.route('/api/health')
def api_health():
    logging.info("Acceso a la ruta de API (JSON)")
    return jsonify(get_all_metrics())

if __name__ == '__main__':
    logging.info("Iniciando el Agente de SysAdmin en el puerto 5000...")
    app.run(host='0.0.0.0', port=5000)