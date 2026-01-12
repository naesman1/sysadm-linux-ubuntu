import psutil
from flask import Flask, jsonify, render_template
import os
import datetime

app = Flask(__name__)

# Configuración
LOG_FILE = "/var/log/syslog" 
KEYWORDS = ["ERROR", "FAILED", "CRITICAL", "PANIC", "DENIED"]

def get_system_errors():
    """Escanea las últimas 50 líneas del syslog buscando errores"""
    errors = []
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r") as f:
                lines = f.readlines()[-50:]
                for line in lines:
                    if any(key in line.upper() for key in KEYWORDS):
                        errors.append(line.strip())
        except Exception as e:
            return [f"No se pudo leer el log: {str(e)}"]
    else:
        return ["Archivo syslog no encontrado."]
    return errors

def get_all_metrics():
    """Reúne todas las métricas del sistema en un solo diccionario"""
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory().percent
    
    disks = []
    for part in psutil.disk_partitions():
        # Filtramos para ver solo discos reales, ignorando snaps y temporales
        if 'loop' not in part.device and 'tmpfs' not in part.fstype:
            try:
                usage = psutil.disk_usage(part.mountpoint)
                disks.append({
                    "mountpoint": part.mountpoint,
                    "total_gb": round(usage.total / (1024**3), 2),
                    "used_percent": usage.percent
                })
            except PermissionError:
                continue

    return {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "OK" if cpu < 80 else "CRITICAL",
        "metrics": {
            "cpu_usage_percent": cpu,
            "ram_usage_percent": ram
        },
        "storage": disks,
        "recent_errors": get_system_errors()
    }

@app.route('/')
def index():
    """Ruta principal: Muestra el reporte visual en HTML"""
    data = get_all_metrics()
    return render_template('report.html', data=data)

@app.route('/api/health')
def api_health():
    """Ruta API: Devuelve los datos en formato JSON para automatización"""
    return jsonify(get_all_metrics())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)