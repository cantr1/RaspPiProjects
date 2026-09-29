import logging
import os
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from uuid import UUID

import psycopg
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from psycopg.rows import dict_row
from pydantic import BaseModel

logger = logging.getLogger(__name__)
SENSOR_RETRY_INTERVAL_SECONDS = 0.25


class Measurement(BaseModel):
    time_of_measure: datetime
    temperature_c: float
    humidity: float


class SavedMeasurement(Measurement):
    id: UUID


class MycoAPI:
    def __init__(self):
        # Hardware imports happen only during startup on the Raspberry Pi.
        import RPi.GPIO as gpio
        import dht11

        self.gpio = gpio
        gpio.setmode(gpio.BCM)
        self.dht = dht11.DHT11(pin=13)
        self.lock = Lock()
        self.next_read_at = 0.0

    def take_measurement(self) -> Measurement | None:
        """Allow three seconds, including waiting for another sensor request."""
        deadline = time.monotonic() + 8
        if not self.lock.acquire(timeout=3):
            return None
        try:
            while time.monotonic() < deadline:
                # Space reads across requests as well as retries.
                delay = self.next_read_at - time.monotonic()
                if delay > 0:
                    time.sleep(min(delay, max(0, deadline - time.monotonic())))
                if time.monotonic() >= deadline:
                    return None
                result = self.dht.read()
                self.next_read_at = time.monotonic() + SENSOR_RETRY_INTERVAL_SECONDS
                if time.monotonic() >= deadline:
                    return None
                if result.is_valid():
                    return Measurement(
                        time_of_measure=datetime.now(timezone.utc),
                        temperature_c=result.temperature,
                        humidity=result.humidity,
                    )
                logger.warning('Invalid DHT11 reading: error_code=%s', result.error_code)
            return None
        finally:
            self.lock.release()

    def close(self):
        self.gpio.cleanup(13)


def save_measurement(db_url: str, measurement: Measurement) -> dict:
    with psycopg.connect(db_url, row_factory=dict_row, connect_timeout=5) as conn:
        row = conn.execute(
            """INSERT INTO measurements (time_of_measure, temperature_c, humidity)
               VALUES (%s, %s, %s)
               RETURNING id, time_of_measure, temperature_c, humidity""",
            (measurement.time_of_measure, measurement.temperature_c, measurement.humidity),
        ).fetchone()
    # The context commits before success is returned to the caller.
    return row


def latest_measurements(db_url: str) -> list[dict]:
    with psycopg.connect(db_url, row_factory=dict_row, connect_timeout=5) as conn:
        return conn.execute(
            """SELECT id, time_of_measure, temperature_c, humidity
               FROM measurements
               ORDER BY time_of_measure DESC, id DESC
               LIMIT 10"""
        ).fetchall()


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_dotenv(Path(__file__).resolve().with_name('.env'))
    db_url = os.environ.get('DB_URL')
    if not db_url or not db_url.strip():
        raise RuntimeError('Set DB_URL in MycoAPI/.env before starting the API')
    app.state.db_url = db_url
    sensor = MycoAPI()
    app.state.sensor = sensor
    try:
        yield
    finally:
        sensor.close()


app = FastAPI(title='MycoAPI', lifespan=lifespan)


@app.post('/api/measure', status_code=201, response_model=SavedMeasurement)
def measure(request: Request):
    try:
        measurement = request.app.state.sensor.take_measurement()
    except Exception:
        logger.exception('Sensor read failed')
        raise HTTPException(status_code=500, detail='Sensor read failed') from None
    if measurement is None:
        raise HTTPException(status_code=500, detail='No valid measurement within three seconds')
    try:
        return save_measurement(request.app.state.db_url, measurement)
    except psycopg.Error:
        logger.exception('Saving measurement failed')
        raise HTTPException(status_code=500, detail='Could not save measurement') from None


@app.get('/api/latest', response_model=list[SavedMeasurement])
def latest(request: Request):
    try:
        return latest_measurements(request.app.state.db_url)
    except psycopg.Error:
        logger.exception('Fetching measurements failed')
        raise HTTPException(status_code=500, detail='Could not fetch measurements') from None
