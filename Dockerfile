FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Instalamos python, pip y SYSTEMD (para tener el binario systemctl)
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    systemd \ 
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt
COPY . .

EXPOSE 5000

CMD ["python3", "main.py"]