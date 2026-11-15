import json
import os
import re
import time
import uuid
import dateutil.parser
import paho.mqtt.client as mqtt
import psycopg2

# Configurações do Broker MQTT via .env
BROKER_HOST = os.getenv("MQTT_BROKER_HOST", "broker.hivemq.com")
BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT", "8883"))
MQTT_USERNAME = os.getenv("MQTT_USERNAME", "").strip()
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "").strip()
USE_TLS = os.getenv("MQTT_USE_TLS", "true").lower() in ("true", "1", "yes")
TOPIC_PREFIX = os.getenv("MQTT_TOPIC_PREFIX", "projeto_integrado").strip("/")

# Configurações do Banco de Dados via .env
DB_HOST = os.getenv("DB_HOST", "timescaledb")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "iotdb")
DB_USER = os.getenv("DB_USER", "iot_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "iot_password")

# Expressão regular para capturar o ID do sensor no tópico: .../sensores/{sensor_id}/data
TOPIC_REGEX = re.compile(r"/sensores/([^/]+)/data$")

db_conn = None

def conectar_banco():
    global db_conn
    while True:
        try:
            if db_conn is not None and not db_conn.closed:
                return db_conn
            print(f"Conectando ao TimescaleDB em {DB_HOST}:{DB_PORT}/{DB_NAME}...")
            db_conn = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD
            )
            print("Conectado ao banco de dados com sucesso!")
            return db_conn
        except Exception as e:
            print(f"Erro ao conectar no banco: {e}. Tentando novamente em 5s...")
            time.sleep(5)

def salvar_temperatura(sensor_id: str, dt, temperature: float):
    conn = conectar_banco()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO temperature_data (time, sensor_id, temperature)
                VALUES (%s, %s, %s);
                """,
                (dt, sensor_id, temperature)
            )
        conn.commit()
        print(f"[DB] Gravado -> sensor={sensor_id} | temp={temperature}°C | time={dt.isoformat()}")
    except Exception as e:
        print(f"[ERRO DB] Falha ao inserir registro: {e}")
        conn.rollback()

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("Conectado ao broker MQTT!")
        topico_inscricao = f"/{TOPIC_PREFIX}/sensores/+/data"
        client.subscribe(topico_inscricao, qos=1)
        print(f"Inscrito no tópico: {topico_inscricao}")
    else:
        print(f"Falha na conexão MQTT. Código: {rc}")

def on_message(client, userdata, msg):
    try:
        topico = msg.topic
        payload_str = msg.payload.decode("utf-8")
        
        # Extrai o sensor_id a partir do tópico
        match = TOPIC_REGEX.search(topico)
        if not match:
            print(f"[AVISO] Tópico ignorado (fora do padrão): {topico}")
            return
        
        sensor_id = match.group(1)
        dados = json.loads(payload_str)
        
        if "temperature" not in dados or "datetime" not in dados:
            print(f"[AVISO] Payload incompleto recebido de {sensor_id}: {payload_str}")
            return
            
        dt = dateutil.parser.parse(dados["datetime"])
        temperatura = float(dados["temperature"])
        
        salvar_temperatura(sensor_id, dt, temperatura)
        
    except json.JSONDecodeError:
        print(f"[ERRO] Mensagem recebida não é um JSON válido: {msg.payload}")
    except Exception as e:
        print(f"[ERRO] Falha ao processar mensagem: {e}")

def main():
    conectar_banco()
    
    client_id = "data_consumer"
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id)
    
    if USE_TLS:
        client.tls_set()
        
    if MQTT_USERNAME:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        
    client.on_connect = on_connect
    client.on_message = on_message
    
    print(f"Conectando ao broker {BROKER_HOST}:{BROKER_PORT}...")
    client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
    client.loop_forever()

if __name__ == "__main__":
    main()