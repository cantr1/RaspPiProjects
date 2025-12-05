import RPi.GPIO as GPIO
import ADC0834
from time import sleep
GPIO.setmode(GPIO.BCM)

ADC0834.setup()

pwmPin=23
GPIO.setup(pwmPin,GPIO.OUT)
pwm=GPIO.PWM(pwmPin,50)
pwm.start(0)

try:
    while True:
        analogVal=ADC0834.getResult(0)
        convertedVal = analogVal * 0.0447
        pwm.ChangeDutyCycle(convertedVal)
        sleep(0.05)
except KeyboardInterrupt:
    GPIO.cleanup()
    print("\nGPIO Released...")