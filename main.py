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

@app.route('/') # Cambiamos la raíz para que muestre el reporte visual
def index():
    # Obtenemos los datos (puedes mover la lógica de health a una función aparte)
    data = get_all_metrics() 
    return render_template('report.html', data=data)

@app.route('/api/health') # Dejamos la API JSON para scripts o K8s
def api_health():
    return jsonify(get_all_metrics())

def get_all_metrics():
    # Aquí mueves toda la lógica que ya tenías para generar el diccionario
    # (CPU, RAM, Discos, Logs...)
    # ...
    return { "status": "OK", "metrics": {...}, ... }
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