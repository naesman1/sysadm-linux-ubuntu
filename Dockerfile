FROM ubuntu:22.04

# Evitar prompts interactivos
ENV DEBIAN_FRONTEND=noninteractive

# Instalar dependencias de sistema
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar archivos
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt
COPY . .

# Exponer Flask
EXPOSE 5000

CMD ["python3", "main.py"]