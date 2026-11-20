from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import RedirectResponse
from database import get_db_cursor
from schemas import TemperaturePoint, LatestSensorResponse, SystemSummary

app = FastAPI(
    title="API de Telemetria de Temperatura",
    description="API REST para consulta de séries temporais de temperatura armazenadas no TimescaleDB.",
    version="1.0.0"
)

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")

@app.get("/health", tags=["Diagnóstico"])
def health_check():
    try:
        with get_db_cursor() as cur:
            cur.execute("SELECT 1 as ping;")
            res = cur.fetchone()
            db_ok = res and res["ping"] == 1
    except Exception as e:
        return {"status": "degraded", "database": str(e), "timestamp": datetime.now()}

    return {
        "status": "healthy" if db_ok else "degraded",
        "database": "ok" if db_ok else "error",
        "timestamp": datetime.now()
    }

@app.get("/api/sensors", response_model=List[str], tags=["Sensores"])
def list_sensors():
    """Lista todos os IDs de sensores registrados no banco."""
    with get_db_cursor() as cur:
        cur.execute("SELECT DISTINCT sensor_id FROM temperature_data ORDER BY sensor_id ASC;")
        return [row["sensor_id"] for row in cur.fetchall()]

@app.get("/api/sensors/{sensor_id}/data", response_model=List[TemperaturePoint], tags=["Sensores"])
def get_sensor_data(
    sensor_id: str,
    limit: int = Query(default=100, ge=1, le=5000, description="Quantidade máxima de registros"),
    start: Optional[datetime] = Query(default=None, description="Data/hora inicial (ISO 8601)"),
    end: Optional[datetime] = Query(default=None, description="Data/hora final (ISO 8601)"),
    order: str = Query(default="desc", pattern="^(asc|desc)$", description="Ordenação cronológica")
):
    """Consulta o histórico de temperaturas de um sensor específico."""
    query = "SELECT time, sensor_id, temperature FROM temperature_data WHERE sensor_id = %s"
    params = [sensor_id]

    if start:
        query += " AND time >= %s"
        params.append(start)
    if end:
        query += " AND time <= %s"
        params.append(end)

    direcao = "ASC" if order.lower() == "asc" else "DESC"
    query += f" ORDER BY time {direcao} LIMIT %s"
    params.append(limit)

    with get_db_cursor() as cur:
        cur.execute(query, tuple(params))
        return cur.fetchall()

@app.get("/api/sensors/{sensor_id}/latest", response_model=LatestSensorResponse, tags=["Sensores"])
def get_sensor_latest(sensor_id: str):
    """Retorna a última leitura de temperatura e o total de registros de um sensor."""
    with get_db_cursor() as cur:
        cur.execute(
            "SELECT time, temperature FROM temperature_data WHERE sensor_id = %s ORDER BY time DESC LIMIT 1;",
            (sensor_id,)
        )
        latest = cur.fetchone()

        cur.execute("SELECT COUNT(*) as total FROM temperature_data WHERE sensor_id = %s;", (sensor_id,))
        total = cur.fetchone()["total"]

        if not latest:
            raise HTTPException(status_code=404, detail=f"Sensor '{sensor_id}' não encontrado.")

        return LatestSensorResponse(
            sensor_id=sensor_id,
            latest_time=latest["time"],
            latest_temperature=latest["temperature"],
            total_records=total
        )

@app.get("/api/summary", response_model=SystemSummary, tags=["Resumo"])
def get_summary():
    """Retorna um resumo consolidado de todos os sensores com suas últimas temperaturas."""
    with get_db_cursor() as cur:
        cur.execute(
            """
            SELECT DISTINCT ON (sensor_id)
                sensor_id,
                time AS latest_time,
                temperature AS latest_temperature
            FROM temperature_data
            ORDER BY sensor_id, time DESC;
            """
        )
        ultimos = cur.fetchall()

        cur.execute("SELECT sensor_id, COUNT(*) AS total FROM temperature_data GROUP BY sensor_id;")
        contagens = {row["sensor_id"]: row["total"] for row in cur.fetchall()}

        lista_sensores = [
            LatestSensorResponse(
                sensor_id=s["sensor_id"],
                latest_time=s["latest_time"],
                latest_temperature=s["latest_temperature"],
                total_records=contagens.get(s["sensor_id"], 0)
            )
            for s in ultimos
        ]

        return SystemSummary(total_sensors=len(lista_sensores), sensors=lista_sensores)