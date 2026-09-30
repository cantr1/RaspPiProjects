# MycoAPI

FastAPI service for a DHT11 sensor on BCM pin 13. Requires a Raspberry Pi,
Python 3.10+, PostgreSQL 13+, and the system libpq library for Psycopg.

From this directory on the Pi:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Create the `mycoapi` database and a database user, then run `schema.sql` against
that database, for example `psql -d mycoapi -f schema.sql` using your administrator
connection. Ensure the API database user has SELECT and INSERT privileges on
`measurements` and USAGE on its schema.
The script creates the table and index; it does not create the database or user.
`within_tolerance` is a required boolean stored with each reading. Recreate the
table using the updated schema before running this version.

Set `DB_URL` in `.env` using `.env.example` as a reference. Keep your existing
`.env` if it already has the correct connection string. Percent-encode special
characters in URL credentials. An existing environment variable takes precedence.

```sh
python -m uvicorn main:app --host 0.0.0.0 --port 8080 --workers 1
```

Use one worker and avoid reload mode when using the sensor: its lock coordinates
threads within one process. GPIO is initialized at startup. Press Ctrl+C once for graceful shutdown: the
lifespan handler stops all three PWM channels and calls `gpio.cleanup()`.
Ctrl+X does not stop Uvicorn; a forced kill cannot run cleanup.

```sh
curl -i -X POST http://localhost:8080/api/measure
curl -i http://localhost:8080/api/latest
curl -i http://localhost:8080/api/health
```

POST returns 201 with the saved record only after commit. Sensor timeout/read
failure and database failure return 500 with a JSON error. GET returns 200 with
the latest ten records in descending measurement-time order, or an empty array.
Records contain `id`, `time_of_measure` (UTC), `temperature_c`, `humidity`, and `within_tolerance`.
`GET /api/health` returns `{"status": "healthy"}` as a liveness check only; it does
not verify the database or sensor.
Interactive API documentation is at http://localhost:8080/docs.

The eight-second sensor budget includes waiting up to three seconds for the sensor lock. Reads are
followed by a 250 ms pause before the next attempt; readings finishing after the deadline are
discarded. This does not interrupt a blocked hardware driver call, and database
work and LED feedback happen after the sensor budget. It is not a strict HTTP response deadline.
This faster retry interval is experimental and exceeds the DHT11's documented
sampling rate. Adjust `SENSOR_RETRY_INTERVAL_SECONDS` in `main.py` if needed;
invalid readings log the driver's error code for diagnosis.

For tests on a development computer, install `requirements.txt` and
`requirements-dev.txt`, then run `python -m pytest` from this directory. Tests use
fake sensor/database objects; hardware imports occur only during real startup.
On macOS without libpq, install `psycopg[binary]` for the test environment.

## Tolerance and LEDs

Defaults are 16–21°C and 85–95% RH, inclusive; both measurements must be within
range. These are starting alert limits for a fruiting room, chosen using
[Cornell's fruiting guidance](https://smallfarms.cornell.edu/resources/methods-of-commercial-mushroom-cultivation-in-the-northeastern-united-states/2-seven-stages-of-cultivation/).
They are not a universal profile for every species, strain, or incubation stage.
Override `TEMPERATURE_MIN_C`, `TEMPERATURE_MAX_C`, `HUMIDITY_MIN`, and
`HUMIDITY_MAX` in `.env`, then restart. Invalid limits fail startup.
Stored booleans reflect the limits at measurement time, not later changes.

The existing active-high RGB wiring uses BCM 18 (red), 23 (green), and 24 (blue).
Red and green are lit during measurement. A valid in-range reading shows green
for 1.25 seconds. An out-of-range reading flashes red three times (250 ms on,
250 ms off). A sensor timeout shows solid red for 1.25 seconds. LEDs are cleared
before releasing the lock, so requests cannot mix their LED patterns.
An out-of-range reading is still saved and returns 201; LED feedback describes
the sensor result, not database commit success.

## LCD

The supplied LCD1602 driver displays readings on the 16x2 I2C screen at address
`0x27` on bus 1. Enable I2C on the Pi and install the updated requirements
(including `smbus2`). The API user needs access to `/dev/i2c-1`.

The screen shows `Temp: 18.5C` and `Humidity: 90.0%`, retaining the last reading
until the next result. Sensor failures replace that result with `Read failed`.
Values describe the sensor reading, not database commit success. Updates occur
under the sensor lock. LCD errors are logged without discarding valid readings.
On graceful shutdown the screen is cleared, its backlight turned off, and the
I2C bus closed. The sample's temperature toggle switch is not used by the API.
