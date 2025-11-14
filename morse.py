import paho.mqtt.client as mqtt
from gpiozero import LED
from time import sleep
import string

LED_PIN = 17
UNIT = 0.2  # base time unit in seconds; tweak to speed up/slow down
TOPIC = "morse"
BROKER = "192.168.1.103"

led = LED(LED_PIN)

MORSE = {
    'a': ".-",    'b': "-...",  'c': "-.-.",  'd': "-..",   'e': ".",
    'f': "..-.",  'g': "--.",   'h': "....",  'i': "..",    'j': ".---",
    'k': "-.-",   'l': ".-..",  'm': "--",    'n': "-.",    'o': "---",
    'p': ".--.",  'q': "--.-",  'r': ".-.",   's': "...",   't': "-",
    'u': "..-",   'v': "...-",  'w': ".--",   'x': "-..-",  'y': "-.--",
    'z': "--..",
    '0': "-----", '1': ".----", '2': "..---", '3': "...--", '4': "....-",
    '5': ".....", '6': "-....", '7': "--...", '8': "---..", '9': "----."
}

def _blink(symbol: str) -> None:
    # dot
    if symbol == '.':
        led.on();  sleep(UNIT)
        led.off(); sleep(UNIT)    # intra-symbol gap
    # dash
    elif symbol == '-':
        led.on();  sleep(3*UNIT)
        led.off(); sleep(UNIT)    # intra-symbol gap

def convert_char(ch: str) -> None:
    code = MORSE.get(ch)
    if not code:
        return  # ignore unknowns (punctuation removed earlier)
    for i, sym in enumerate(code):
        _blink(sym)
    # after last symbol we already waited 1u; add 2u more to make 3u letter gap
    sleep(2*UNIT)

def convert_to_morse(message: str) -> None:
    for i, ch in enumerate(message):
        if ch == ' ':
            # word gap should be 7u total; we've already had 1u after last symbol -> add 6u
            sleep(6*UNIT)
            continue
        convert_char(ch)

def on_message(client, userdata, msg):
    payload = msg.payload.decode().lower()
    translator = str.maketrans('', '', string.punctuation)
    processed = payload.translate(translator)
    processed = " ".join(processed.split())  # collapse whitespace
    convert_to_morse(processed)

client = mqtt.Client()
client.on_message = on_message
client.connect(BROKER)
client.subscribe(TOPIC)
client.loop_forever()
