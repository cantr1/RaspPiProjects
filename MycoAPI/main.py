import logging
import math
import os
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from uuid import UUID

import psycopg
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from psycopg.rows import dict_row
from pydantic import BaseModel
from lcd_control import LCD_Control

logger = logging.getLogger(__name__)
SENSOR_RETRY_INTERVAL_SECONDS = 0.25
SENSOR_TIMEOUT_SECONDS = 8


class Measurement(BaseModel):
    time_of_measure: datetime
    temperature_c: float
    humidity: float
    within_tolerance: bool


class SavedMeasurement(Measurement):
    id: UUID


@dataclass(frozen=True)
class Tolerance:
    temperature_min_c: float = 16
    temperature_max_c: float = 21
    humidity_min: float = 85
    humidity_max: float = 95

    def __post_init__(self):
        if not all(math.isfinite(value) for value in (
            self.temperature_min_c, self.temperature_max_c,
            self.humidity_min, self.humidity_max,
        )):
            raise ValueError('Tolerance limits must be finite numbers')
        if self.temperature_min_c > self.temperature_max_c:
            raise ValueError('Minimum temperature must not exceed maximum temperature')
        if not 0 <= self.humidity_min <= self.humidity_max <= 100:
            raise ValueError('Humidity limits must be ordered and between 0 and 100')

    def contains(self, temperature_c: float, humidity: float) -> bool:
        return (self.temperature_min_c <= temperature_c <= self.temperature_max_c
                and self.humidity_min <= humidity <= self.humidity_max)

    @classmethod
    def from_env(cls):
        defaults = cls()
        return cls(
            temperature_min_c=float(os.getenv('TEMPERATURE_MIN_C', defaults.temperature_min_c)),
            temperature_max_c=float(os.getenv('TEMPERATURE_MAX_C', defaults.temperature_max_c)),
            humidity_min=float(os.getenv('HUMIDITY_MIN', defaults.humidity_min)),
            humidity_max=float(os.getenv('HUMIDITY_MAX', defaults.humidity_max)),
        )


class MycoAPI:
    def __init__(self, tolerance: Tolerance):
        # Hardware imports happen only during startup on the Raspberry Pi.
        import RPi.GPIO as gpio
        import dht11

        self.tolerance = tolerance
        self.gpio = gpio
        gpio.setmode(gpio.BCM)
        self.dht = dht11.DHT11(pin=13)
        self.lock = Lock()
        self.next_read_at = 0.0

        # Setup LED
        self.red_pin = 18
        self.green_pin = 23
        self.blue_pin = 24
        gpio.setup(self.red_pin, gpio.OUT)
        gpio.setup(self.green_pin,gpio.OUT)
        gpio.setup(self.blue_pin,gpio.OUT)
        self.red_pwm = gpio.PWM(self.red_pin, 100)
        self.green_pwm = gpio.PWM(self.green_pin, 100)
        self.blue_pwm = gpio.PWM(self.blue_pin, 100)

        # Start each pin
        self.red_pwm.start(0)
        self.green_pwm.start(0)
        self.blue_pwm.start(0)
        self.lcd = LCD_Control()


    def show_result(self, within_tolerance: bool):
        """Called while holding the sensor lock, so LED patterns cannot overlap."""
        self.red_pwm.ChangeDutyCycle(0)
        self.green_pwm.ChangeDutyCycle(0)
        if within_tolerance:
            self.green_pwm.ChangeDutyCycle(100)
            time.sleep(1.25)
        else:
            for _ in range(3):
                self.red_pwm.ChangeDutyCycle(100)
                time.sleep(0.25)
                self.red_pwm.ChangeDutyCycle(0)
                time.sleep(0.25)

    def take_measurement(self) -> Measurement | None:
        """Use an eight-second sensor budget; LED feedback follows the reading."""
        deadline = time.monotonic() + SENSOR_TIMEOUT_SECONDS
        if not self.lock.acquire(timeout=3):
            return None
        try:
            self.red_pwm.ChangeDutyCycle(100)
            self.green_pwm.ChangeDutyCycle(100)
            while time.monotonic() < deadline:
                delay = self.next_read_at - time.monotonic()
                if delay > 0:
                    time.sleep(min(delay, max(0, deadline - time.monotonic())))
                if time.monotonic() >= deadline:
                    break
                result = self.dht.read()
                self.next_read_at = time.monotonic() + SENSOR_RETRY_INTERVAL_SECONDS
                if time.monotonic() >= deadline:
                    break
                if result.is_valid():
                    measurement = Measurement(
                        time_of_measure=datetime.now(timezone.utc),
                        temperature_c=result.temperature,
                        humidity=result.humidity,
                        within_tolerance=self.tolerance.contains(result.temperature, result.humidity),
                    )
                    self.lcd.show_measurement(measurement.temperature_c, measurement.humidity)
                    self.show_result(measurement.within_tolerance)
                    return measurement
                logger.warning('Invalid DHT11 reading: error_code=%s', result.error_code)
            self.lcd.show('Read failed', 'No valid reading')
            self.green_pwm.ChangeDutyCycle(0)
            time.sleep(1.25)
            return None
        except Exception:
            self.lcd.show('Read failed', 'Sensor error')
            raise
        finally:
            try:
                self.red_pwm.ChangeDutyCycle(0)
                self.green_pwm.ChangeDutyCycle(0)
            finally:
                self.lock.release()

    def close(self):
        try:
            self.red_pwm.stop()
            self.green_pwm.stop()
            self.blue_pwm.stop()
        finally:
            try:
                self.lcd.close()
            finally:
                self.gpio.cleanup()


def save_measurement(db_url: str, measurement: Measurement) -> dict:
    with psycopg.connect(db_url, row_factory=dict_row, connect_timeout=5) as conn:
        row = conn.execute(
            """INSERT INTO measurements (time_of_measure, temperature_c, humidity, within_tolerance)
               VALUES (%s, %s, %s, %s)
               RETURNING id, time_of_measure, temperature_c, humidity, within_tolerance""",
            (measurement.time_of_measure, measurement.temperature_c, measurement.humidity,
             measurement.within_tolerance),
        ).fetchone()
    # The context commits before success is returned to the caller.
    return row


def latest_measurements(db_url: str) -> list[dict]:
    with psycopg.connect(db_url, row_factory=dict_row, connect_timeout=5) as conn:
        return conn.execute(
            """SELECT id, time_of_measure, temperature_c, humidity, within_tolerance
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
    sensor = MycoAPI(Tolerance.from_env())
    app.state.sensor = sensor
    try:
        yield
    finally:
        sensor.close()


app = FastAPI(title='MycoAPI', lifespan=lifespan)


@app.get('/api/health')
def health():
    """Liveness only: this does not read the sensor or query the database."""
    return {'status': 'healthy'}


@app.post('/api/measure', status_code=201, response_model=SavedMeasurement)
def measure(request: Request):
    try:
        measurement = request.app.state.sensor.take_measurement()
    except Exception:
        logger.exception('Sensor read failed')
        raise HTTPException(status_code=500, detail='Sensor read failed') from None
    if measurement is None:
        raise HTTPException(status_code=500, detail='Sensor busy or no valid measurement within eight seconds')
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
