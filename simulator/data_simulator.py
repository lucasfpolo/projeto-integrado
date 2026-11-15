import os
import time

# Leitura das variáveis injetadas pelo Docker Compose a partir do .env
broker_host = os.getenv("MQTT_BROKER_HOST", "nao_definido")
broker_port = os.getenv("MQTT_BROKER_PORT", "nao_definido")
use_tls = os.getenv("MQTT_USE_TLS", "false")
topic_prefix = os.getenv("MQTT_TOPIC_PREFIX", "")
interval = float(os.getenv("PUBLISH_INTERVAL", "3"))

print("=== Iniciando Container Simulador ===")
print(f"Broker Host: {broker_host}")
print(f"Broker Port: {broker_port}")
print(f"Usar TLS:    {use_tls}")
print(f"Prefixo:     {topic_prefix}")
print(f"Intervalo:   {interval}s")
print("=====================================")

contador = 1
while True:
    print(f"[Ciclo {contador}] Simulador ativo e lendo configuracoes do .env...")
    contador += 1
    time.sleep(interval)