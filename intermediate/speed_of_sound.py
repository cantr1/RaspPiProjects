"""
This script uses a ultrasonic sensor 6in away from a target
then converts the measured travel time of the ping to determine the speed of sound
"""
import RPi.GPIO as GPIO
import time
GPIO.setmode(GPIO.BCM)

# Set vars for pins
trigPin=23
echoPin=24
ledPin=21

# Setup pins
GPIO.setup(trigPin,GPIO.OUT)
GPIO.setup(echoPin,GPIO.IN)
GPIO.setup(ledPin,GPIO.OUT)

try:
    # Turn on led
    GPIO.output(ledPin, 1)
    # Send out a ping
    GPIO.output(trigPin, 0)
    time.sleep(2E-6) # wait 2ms
    GPIO.output(trigPin, 1)
    time.sleep(10E-6)
    GPIO.output(trigPin, 0)

    # Wait to recieve signal
    while GPIO.input(echoPin)==0:
        pass
        
    # Get system time once ping recieved
    echoStartTime=time.time()

    while GPIO.input(echoPin)==1:
        pass

    echoFinishTime=time.time()

    # Determine signal travel time
    pingTime = (echoFinishTime - echoStartTime) * 1E6 # convert to milliseconds

    # Get distance
    distance = 6 #inches
    distanceMi = 6 * 63360

    # Speed = distance / time
    speed = (distanceMi / pingTime) * 2 # since the ping has to travel to the target and back

    # Turn off led
    GPIO.output(ledPin, 0)

    print(f"Calculated speed of sound: {round(speed,2)}mph")

    GPIO.cleanup()
    print("\nGPIO Released...")

except KeyboardInterrupt:
    GPIO.cleanup()
    print("\nGPIO Released...")