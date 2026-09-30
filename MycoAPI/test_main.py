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
    monkeypatch.setattr(main, 'MycoAPI', lambda tolerance: sensor)
    monkeypatch.setenv('DB_URL', 'postgresql://test/test')
    for name, value in [('TEMPERATURE_MIN_C', '20'), ('TEMPERATURE_MAX_C', '26'),
                        ('HUMIDITY_MIN', '60'), ('HUMIDITY_MAX', '80')]:
        monkeypatch.setenv(name, value)
    with TestClient(main.app) as client:
        yield client, sensor
    sensor.close.assert_called_once()


def reading():
    return main.Measurement(time_of_measure=datetime.now(timezone.utc),
                            temperature_c=23, humidity=65, within_tolerance=True)


def test_health_does_not_read_sensor_or_database(client, monkeypatch):
    http, sensor = client
    connect = MagicMock()
    monkeypatch.setattr(main.psycopg, 'connect', connect)
    response = http.get('/api/health')
    assert response.status_code == 200
    assert response.json() == {'status': 'healthy'}
    sensor.take_measurement.assert_not_called()
    connect.assert_not_called()


def test_close_stops_pwm_before_cleaning_all_gpio():
    sensor = main.MycoAPI.__new__(main.MycoAPI)
    hardware = MagicMock()
    sensor.red_pwm = hardware.red
    sensor.green_pwm = hardware.green
    sensor.blue_pwm = hardware.blue
    sensor.gpio = hardware.gpio
    sensor.lcd = hardware.lcd
    sensor.close()
    from unittest.mock import call
    assert hardware.mock_calls == [call.red.stop(), call.green.stop(),
                                   call.blue.stop(), call.lcd.close(), call.gpio.cleanup()]


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
    sensor.tolerance = main.Tolerance(20, 26, 60, 80)
    sensor.red_pwm = MagicMock()
    sensor.green_pwm = MagicMock()
    sensor.blue_pwm = MagicMock()
    sensor.show_result = MagicMock()
    sensor.dht = MagicMock()
    sensor.lcd = MagicMock()
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
    assert clock.now == 9.25
    assert sensor.dht.read.call_count == 16


def test_invalid_readings_exhaust_eight_seconds(timed_sensor):
    sensor, clock = timed_sensor
    sensor.dht.read.return_value = result(False)
    assert sensor.take_measurement() is None
    assert clock.now == 9.25
    assert sensor.dht.read.call_count == 32
    assert not sensor.lock.locked()


def test_late_valid_reading_is_rejected(timed_sensor):
    sensor, clock = timed_sensor
    def slow_read():
        clock.now += 8.1
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


@pytest.mark.parametrize('temperature,humidity,expected', [
    (16, 85, True), (21, 95, True), (18, 90, True),
    (15.9, 90, False), (21.1, 90, False),
    (18, 84.9, False), (18, 95.1, False),
])
def test_default_tolerance_boundaries(temperature, humidity, expected):
    assert main.Tolerance().contains(temperature, humidity) is expected


@pytest.mark.parametrize('limits', [
    (22, 16, 85, 95), (16, 21, 96, 85), (16, 21, -1, 95),
    (16, 21, 85, 101), (float('nan'), 21, 85, 95),
])
def test_invalid_tolerance_configuration(limits):
    with pytest.raises(ValueError):
        main.Tolerance(*limits)


def test_env_overrides_tolerance(monkeypatch):
    for name, value in [('TEMPERATURE_MIN_C', '20'), ('TEMPERATURE_MAX_C', '25'),
                        ('HUMIDITY_MIN', '70'), ('HUMIDITY_MAX', '90')]:
        monkeypatch.setenv(name, value)
    assert main.Tolerance.from_env() == main.Tolerance(20, 25, 70, 90)


def test_outside_tolerance_flashes_red_three_times(timed_sensor):
    from unittest.mock import call
    sensor, clock = timed_sensor
    sensor.tolerance = main.Tolerance()
    # Existing test reading is 23 C / 65%: outside the default fruiting profile.
    sensor.dht.read.return_value = result(True)
    sensor.show_result = main.MycoAPI.show_result.__get__(sensor)
    measurement = sensor.take_measurement()
    assert measurement.within_tolerance is False
    assert clock.now == 1.5
    assert sensor.red_pwm.ChangeDutyCycle.call_args_list == [
        call(100), call(0),  # Measuring, then clear yellow before the alert.
        call(100), call(0), call(100), call(0), call(100), call(0),
        call(0),  # Final cleanup before releasing the lock.
    ]
    assert not sensor.lock.locked()


def test_busy_request_does_not_change_leds(timed_sensor):
    sensor, _ = timed_sensor
    sensor.lock = MagicMock()
    sensor.lock.acquire.return_value = False
    assert sensor.take_measurement() is None
    sensor.red_pwm.ChangeDutyCycle.assert_not_called()
    sensor.green_pwm.ChangeDutyCycle.assert_not_called()


def test_out_of_range_reading_is_saved_with_false(client, monkeypatch):
    http, sensor = client
    measurement = reading().model_copy(update={'within_tolerance': False})
    sensor.take_measurement.return_value = measurement
    connection = MagicMock()
    connection.__enter__.return_value = connection
    connection.execute.return_value.fetchone.return_value = {
        'id': uuid4(), **measurement.model_dump(),
    }
    monkeypatch.setattr(main.psycopg, 'connect', lambda *a, **k: connection)
    response = http.post('/api/measure')
    assert response.status_code == 201
    assert response.json()['within_tolerance'] is False
    assert connection.execute.call_args.args[1][-1] is False


def test_valid_reading_updates_lcd_while_locked(timed_sensor):
    sensor, _ = timed_sensor
    sensor.dht.read.return_value = result(True)
    def display(temperature, humidity):
        assert sensor.lock.locked()
        assert (temperature, humidity) == (23, 65)
    sensor.lcd.show_measurement.side_effect = display
    assert sensor.take_measurement() is not None
    sensor.lcd.show_measurement.assert_called_once_with(23, 65)


def test_failed_reading_replaces_old_lcd_result(timed_sensor):
    sensor, _ = timed_sensor
    sensor.dht.read.return_value = result(False)
    assert sensor.take_measurement() is None
    sensor.lcd.show.assert_called_once_with('Read failed', 'No valid reading')
    sensor.lcd.show_measurement.assert_not_called()


def test_lcd_formats_and_pads_both_rows():
    from lcd_control import LCD_Control
    from unittest.mock import call
    display = LCD_Control.__new__(LCD_Control)
    display.lcd = MagicMock()
    display.show_measurement(18.5, 90)
    assert display.lcd.write.call_args_list == [
        call(0, 0, 'Temp: 18.5C'.ljust(16)),
        call(0, 1, 'Humidity: 90.0%'.ljust(16)),
    ]


def test_lcd_failure_does_not_discard_reading(timed_sensor):
    from lcd_control import LCD_Control
    sensor, _ = timed_sensor
    display = LCD_Control.__new__(LCD_Control)
    display.lcd = MagicMock()
    display.lcd.write.side_effect = OSError('I2C disconnected')
    sensor.lcd = display
    sensor.dht.read.return_value = result(True)
    assert sensor.take_measurement().temperature_c == 23
    assert not sensor.lock.locked()


def test_lcd_initialization_failure_closes_driver(monkeypatch):
    import sys
    from lcd_control import LCD_Control
    driver = MagicMock()
    driver.init.return_value = False
    monkeypatch.setitem(sys.modules, 'LCD1602', driver)
    display = LCD_Control()
    driver.init.assert_called_once_with(0x27, 1)
    driver.close.assert_called_once()
    assert display.lcd is None
    display.show_measurement(18, 90)
    driver.write.assert_not_called()
