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
        user_input=input("Enter 1 to chop: ")
        if user_input == "1":
            pwm.ChangeDutyCycle(7.8)
            sleep(0.3)
            pwm.ChangeDutyCycle(2.0)
        else:
            pass
except KeyboardInterrupt:
    GPIO.cleanup()
    print("\nGPIO Released...")