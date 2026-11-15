import json
import os
import random
import time
from datetime import datetime, timezone
import paho.mqtt.client as mqtt

# Leitura das variáveis injetadas pelo Docker Compose a partir do .env
BROKER_HOST = os.getenv("MQTT_BROKER_HOST", "broker.hivemq.com")
BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT", "8883"))
MQTT_USERNAME = os.getenv("MQTT_USERNAME", "").strip()
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "").strip()
USE_TLS = os.getenv("MQTT_USE_TLS", "true").lower() in ("true", "1", "yes")
TOPIC_PREFIX = os.getenv("MQTT_TOPIC_PREFIX", "projeto_integrado").strip("/")
INTERVAL = float(os.getenv("PUBLISH_INTERVAL", "3.0"))
N_SENSORES = int(os.getenv("N_SENSORES", "3"))


print("=== Iniciando Container Simulador ===")
print(f"Broker Host: {BROKER_HOST}")
print(f"Broker Port: {BROKER_PORT}")
print(f"Usar TLS:    {USE_TLS}")
print(f"Prefixo:     {TOPIC_PREFIX}")
print(f"Intervalo:   {INTERVAL}s")
print(f"Username:    {MQTT_USERNAME}")
print(f"Sensores:    {N_SENSORES}")
print("=====================================")

client_id = f"simulador_id"
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id)

if USE_TLS:
    client.tls_set()

if MQTT_USERNAME:
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

print(f"Conectando ao broker {BROKER_HOST}:{BROKER_PORT} (TLS={USE_TLS})...")
client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
client.loop_start()

# Inicializa o valor atual com 22, 23 e 24°C
temperatura_atual = [float(22 + i) for i in range(N_SENSORES)]

try:
    while True:
        for i in range(N_SENSORES):
            # Simula uma variação na leitura de cada sensor
            temperatura_atual[i] = round(temperatura_atual[i] + random.uniform(-1.5, 1.5), 2)

            payload = {
                "datetime": datetime.now(timezone.utc).isoformat(),
                "temperature": temperatura_atual[i]
            }

            topico = f"/{TOPIC_PREFIX}/sensores/sensor_{i + 1:02d}/data"
            client.publish(topico, json.dumps(payload), qos=1)

            print(f"Publicado em [{topico}]: {payload}")
        time.sleep(INTERVAL)

except KeyboardInterrupt:
    print("Encerrando simulador...")
finally:
    client.loop_stop()
    client.disconnect()