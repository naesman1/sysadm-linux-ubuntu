SysHealth Agent: Ubuntu/Linux Monitoring & Security Tool
Este proyecto es un agente de monitoreo proactivo diseñado para Administradores de Sistemas y SREs. Automatiza la recolección de métricas críticas, el análisis de seguridad y la generación de reportes visuales, permitiendo una gestión eficiente de servidores Linux mediante contenedores Docker.

🚀 Características Principales
Monitoreo de Hardware: Seguimiento en tiempo real de CPU, memoria RAM y uso de sistemas de archivos (Filesystems).

Estado de Servicios: Verificación proactiva de servicios críticos (nginx, docker, ssh, mysql, kubelet) mediante comunicación con el bus de sistema del host.

Análisis de Seguridad: * Detección de intentos de inicio de sesión fallidos en /var/log/auth.log.

Escaneo de errores críticos en syslog.

Conteo de parches de seguridad pendientes.

Reportes Automatizados: * Dashboard Web: Interfaz visual limpia construida con Flask y Jinja2.

API JSON: Endpoint /api/health para integración con herramientas de terceros.

Email Reports: Generación y envío automático de reportes HTML vía Gmail (SMTP).

Persistencia de Datos: Los reportes generados se almacenan físicamente en el host mediante volúmenes de Docker.

🛠️ Stack Tecnológico
Lenguaje: Python 3.10+

Framework Web: Flask

Librerías: psutil (Métricas), smtplib (Email), subprocess (Comandos de sistema).

Contenerización: Docker (Imagen basada en Ubuntu 22.04).

📦 Instalación y Despliegue
Requisitos Previos
Docker instalado en el host.

Gmail App Password: Si deseas habilitar los reportes por correo, genera una contraseña de aplicación en tu cuenta de Google.

Despliegue con Docker (Recomendado)
Para que el agente pueda monitorear el host real desde el contenedor, ejecutamos con privilegios y mapeo de sockets:

Bash

docker build -t sysadm-agent .

docker run -d \
  --name mi-agente-sys \
  -p 5000:5000 \
  -v /var/log:/var/log:ro \
  -v $(pwd)/reportes:/app/reportes \
  -v /var/run/dbus/system_bus_socket:/var/run/dbus/system_bus_socket \
  --privileged \
  sysadm-agent
Endpoints Disponibles
http://localhost:5000/ - Dashboard Visual.

http://localhost:5000/api/health - Datos en formato JSON.

http://localhost:5000/generate-report - Genera reporte físico y envía email.

⚙️ Configuración de Variables de Entorno
Para el envío de correos, asegúrate de configurar las siguientes variables en el script o mediante el flag -e en Docker:

SENDER_EMAIL: Tu cuenta de Gmail.

SENDER_PASSWORD: Tu contraseña de aplicación de 16 caracteres.

RECEIVER_EMAIL: Destinatario del reporte.