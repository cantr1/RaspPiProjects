import RPi.GPIO as gpio
import ADC0834 as adc
from time import sleep

gpio.setmode(gpio.BCM)
adc.setup()

# Setup gpio Pin for LEDs
rPin=16
gpio.setup(rPin,gpio.OUT)
rPWM=gpio.PWM(rPin,100)

gPin=20
gpio.setup(gPin,gpio.OUT)
gPWM=gpio.PWM(gPin,100)

bPin=21
gpio.setup(bPin,gpio.OUT)
bPWM=gpio.PWM(bPin,100)

# Starting Cycle - Set's default brightness and value to be modified
brightness = 0
rPWM.start(brightness)
gPWM.start(brightness)
bPWM.start(brightness)

try:
    while True:
        rVal=adc.getResult(0)
        gVal=adc.getResult(1)
        bVal=adc.getResult(2)
        #print(analogVal)
        sleep(.1)
        rPWM.ChangeDutyCycle((rVal * (100/255)))
        gPWM.ChangeDutyCycle((gVal * (100/255)))
        bPWM.ChangeDutyCycle((bVal * (100/255)))
except KeyboardInterrupt:
    gpio.cleanup()
    print("\ngpio exited cleanly...")