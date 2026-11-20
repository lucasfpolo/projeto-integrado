from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

class TemperaturePoint(BaseModel):
    time: datetime = Field(..., description="Timestamp da leitura")
    sensor_id: str = Field(..., description="Identificador do sensor")
    temperature: float = Field(..., description="Temperatura registrada em °C")

class LatestSensorResponse(BaseModel):
    sensor_id: str
    latest_time: Optional[datetime] = None
    latest_temperature: Optional[float] = None
    total_records: int

class SystemSummary(BaseModel):
    total_sensors: int
    sensors: List[LatestSensorResponse]