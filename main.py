import psutil
import flask
from flask import jsonify
import os
import datetime

app = flask.Flask(__name__)

# Configuración: Archivo de logs a monitorear en Ubuntu
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

@app.route('/health', methods=['GET'])
def health():
    # 1. Uso de CPU y Memoria
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory().percent
    
    # 2. Filesystems (Discos)
    disks = []
    for part in psutil.disk_partitions():
        if 'loop' not in part.device: # Ignorar snaps en Ubuntu
            usage = psutil.disk_usage(part.mountpoint)
            disks.append({
                "mountpoint": part.mountpoint,
                "total_gb": round(usage.total / (1024**3), 2),
                "used_percent": usage.percent
            })

    # 3. Reporte final
    return jsonify({
        "timestamp": datetime.datetime.now().isoformat(),
        "status": "OK" if cpu < 80 else "CRITICAL",
        "metrics": {
            "cpu_usage_percent": cpu,
            "ram_usage_percent": ram
        },
        "storage": disks,
        "recent_errors": get_system_errors()
    })

if __name__ == '__main__':
    # El puerto 5000 es el estándar de Flask
    app.run(host='0.0.0.0', port=5000)