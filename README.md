# Raspberry Pi Projects

A collection of Python exercises for learning Raspberry Pi GPIO and basic electronics. The examples progress from blinking LEDs and reading buttons to PWM, analog input, motion sensing, servos, MQTT Morse code, and ultrasonic distance measurement.

## Project layout

- `beginner/` — LED, button, and binary counter exercises
- `novice/` — PWM, RGB LEDs, ADC0834 input, servo control, and MQTT Morse code
- `intermediate/` — PIR motion and ultrasonic sensor projects
- `Resources/` — shared ADC0834 driver

## Requirements

- A Raspberry Pi with Python 3
- The components required by the example you want to run
- [`RPi.GPIO`](https://pypi.org/project/RPi.GPIO/)
- [`gpiozero`](https://gpiozero.readthedocs.io/) and [`paho-mqtt`](https://pypi.org/project/paho-mqtt/) for `novice/morse.py`

Check each script before wiring: some examples use BCM pin numbering while others use physical BOARD pin numbering.

## Running an example

From the repository root, run a script with Python 3:

```bash
python3 beginner/blink.py
```

ADC0834 examples also need the shared driver on Python's module path:

```bash
PYTHONPATH=Resources python3 novice/analog_input.py
```

Most examples run until you press `Ctrl+C`, then release the GPIO pins. Run them directly on a Raspberry Pi and verify your wiring and resistor values before applying power.
