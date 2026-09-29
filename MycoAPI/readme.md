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
`within_tolerance` is omitted until tolerance rules are defined.

Set `DB_URL` in `.env` using `.env.example` as a reference. Keep your existing
`.env` if it already has the correct connection string. Percent-encode special
characters in URL credentials. An existing environment variable takes precedence.

```sh
python -m uvicorn main:app --host 0.0.0.0 --port 8080 --workers 1
```

Use one worker and avoid reload mode when using the sensor: its lock coordinates
threads within one process. GPIO is initialized at startup and cleaned up at shutdown.

```sh
curl -i -X POST http://localhost:8080/api/measure
curl -i http://localhost:8080/api/latest
```

POST returns 201 with the saved record only after commit. Sensor timeout/read
failure and database failure return 500 with a JSON error. GET returns 200 with
the latest ten records in descending measurement-time order, or an empty array.
Records contain `id`, `time_of_measure` (UTC), `temperature_c`, and `humidity`.
Interactive API documentation is at http://localhost:8080/docs.

The three-second sensor budget includes waiting for the sensor lock. Reads are
followed by a 250 ms pause before the next attempt; readings finishing after the deadline are
discarded. This does not interrupt a blocked hardware driver call, and database
work happens after the sensor budget. It is not a strict HTTP response deadline.
This faster retry interval is experimental and exceeds the DHT11's documented
sampling rate. Adjust `SENSOR_RETRY_INTERVAL_SECONDS` in `main.py` if needed;
invalid readings log the driver's error code for diagnosis.

For tests on a development computer, install `requirements.txt` and
`requirements-dev.txt`, then run `python -m pytest` from this directory. Tests use
fake sensor/database objects; hardware imports occur only during real startup.
On macOS without libpq, install `psycopg[binary]` for the test environment.
