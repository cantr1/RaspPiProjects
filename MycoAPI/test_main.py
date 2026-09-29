from datetime import datetime, timezone
from threading import Lock
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import psycopg
import pytest
from fastapi.testclient import TestClient

import main


@pytest.fixture
def client(monkeypatch):
    sensor = MagicMock()
    monkeypatch.setattr(main, 'MycoAPI', lambda: sensor)
    monkeypatch.setenv('DB_URL', 'postgresql://test/test')
    with TestClient(main.app) as client:
        yield client, sensor
    sensor.close.assert_called_once()


def reading():
    return main.Measurement(time_of_measure=datetime.now(timezone.utc),
                            temperature_c=23, humidity=65)


def test_measure_commits_before_201(client, monkeypatch):
    http, sensor = client
    sensor.take_measurement.return_value = reading()
    connection = MagicMock()
    connection.__enter__.return_value = connection
    row = {'id': uuid4(), **reading().model_dump()}
    connection.execute.return_value.fetchone.return_value = row
    monkeypatch.setattr(main.psycopg, 'connect', lambda *a, **k: connection)
    response = http.post('/api/measure')
    assert response.status_code == 201
    assert response.json()['id'] == str(row['id'])
    connection.__exit__.assert_called_once_with(None, None, None)


def test_commit_failure_returns_500(client, monkeypatch):
    http, sensor = client
    sensor.take_measurement.return_value = reading()
    connection = MagicMock()
    connection.__enter__.return_value = connection
    connection.__exit__.side_effect = psycopg.OperationalError('private details')
    monkeypatch.setattr(main.psycopg, 'connect', lambda *a, **k: connection)
    response = http.post('/api/measure')
    assert response.status_code == 500
    assert response.json() == {'detail': 'Could not save measurement'}


@pytest.mark.parametrize('failure', [None, RuntimeError('bad sensor')])
def test_sensor_failure_never_inserts(client, monkeypatch, failure):
    http, sensor = client
    sensor.take_measurement.return_value = None
    if failure:
        sensor.take_measurement.side_effect = failure
    save = MagicMock()
    monkeypatch.setattr(main, 'save_measurement', save)
    assert http.post('/api/measure').status_code == 500
    save.assert_not_called()


def test_latest_empty_and_populated(client, monkeypatch):
    http, _ = client
    fetch = MagicMock(return_value=[])
    monkeypatch.setattr(main, 'latest_measurements', fetch)
    assert http.get('/api/latest').json() == []
    fetch.return_value = [{'id': uuid4(), **reading().model_dump()}]
    response = http.get('/api/latest')
    assert response.status_code == 200
    assert response.json()[0]['temperature_c'] == 23
    fetch.side_effect = psycopg.OperationalError('private details')
    response = http.get('/api/latest')
    assert response.status_code == 500
    assert response.json() == {'detail': 'Could not fetch measurements'}


@pytest.fixture
def timed_sensor(monkeypatch):
    clock = SimpleNamespace(now=0.0)
    monkeypatch.setattr(main.time, 'monotonic', lambda: clock.now)
    monkeypatch.setattr(main.time, 'sleep', lambda delay: setattr(clock, 'now', clock.now + delay))
    sensor = main.MycoAPI.__new__(main.MycoAPI)
    sensor.lock = Lock()
    sensor.next_read_at = 0.0
    sensor.dht = MagicMock()
    return sensor, clock


def result(valid):
    return SimpleNamespace(is_valid=lambda: valid, temperature=23, humidity=65,
                           error_code=0 if valid else 1)


def test_retry_then_success_and_spacing_between_requests(timed_sensor):
    sensor, clock = timed_sensor
    sensor.dht.read.side_effect = [result(False), result(True), result(True)]
    assert sensor.take_measurement().humidity == 65
    assert clock.now == 0.25
    assert sensor.take_measurement().temperature_c == 23
    assert clock.now == 0.5
    assert not sensor.lock.locked()


def test_tenth_attempt_can_succeed_before_deadline(timed_sensor):
    sensor, clock = timed_sensor
    sensor.dht.read.side_effect = [result(False)] * 9 + [result(True)]
    assert sensor.take_measurement().humidity == 65
    assert sensor.dht.read.call_count == 10
    assert clock.now == 2.25
    assert not sensor.lock.locked()


def test_read_duration_counts_toward_deadline(timed_sensor):
    sensor, clock = timed_sensor
    def slow_invalid_read():
        clock.now += 0.25
        return result(False)
    sensor.dht.read.side_effect = slow_invalid_read
    assert sensor.take_measurement() is None
    assert clock.now == 3
    assert sensor.dht.read.call_count == 6


def test_invalid_readings_exhaust_three_seconds(timed_sensor):
    sensor, clock = timed_sensor
    sensor.dht.read.return_value = result(False)
    assert sensor.take_measurement() is None
    assert clock.now == 3
    assert sensor.dht.read.call_count == 12
    assert not sensor.lock.locked()


def test_late_valid_reading_is_rejected(timed_sensor):
    sensor, clock = timed_sensor
    def slow_read():
        clock.now += 3.1
        return result(True)
    sensor.dht.read.side_effect = slow_read
    assert sensor.take_measurement() is None
    assert not sensor.lock.locked()


def test_exception_releases_sensor_lock(timed_sensor):
    sensor, _ = timed_sensor
    sensor.dht.read.side_effect = RuntimeError('hardware failure')
    with pytest.raises(RuntimeError):
        sensor.take_measurement()
    assert not sensor.lock.locked()


def test_busy_sensor_does_not_read(timed_sensor):
    sensor, _ = timed_sensor
    sensor.lock = MagicMock()
    sensor.lock.acquire.return_value = False
    assert sensor.take_measurement() is None
    sensor.dht.read.assert_not_called()
    sensor.lock.release.assert_not_called()
