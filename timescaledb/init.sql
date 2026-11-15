-- Habilita a extensão do TimescaleDB
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- Tabela para leituras de temperatura
CREATE TABLE IF NOT EXISTS temperature_data (
    time TIMESTAMPTZ NOT NULL,
    sensor_id VARCHAR(64) NOT NULL,
    temperature DOUBLE PRECISION NOT NULL
);

-- Converte a tabela em hypertable (particionamento automático por tempo)
SELECT create_hypertable('temperature_data', 'time', if_not_exists => TRUE);

-- Índice composto para acelerar buscas por sensor e ordenação recente
CREATE INDEX IF NOT EXISTS idx_temperature_sensor_time 
    ON temperature_data (sensor_id, time DESC);