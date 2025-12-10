"""
Script calculates the distance an object is from the
transmitter
"""
import RPi.GPIO as GPIO
import time
GPIO.setmode(GPIO.BCM)

"""
Function to determine the distance from the measured value
Returns distance to target in inches
1 in = 154
"""
def calc_distance(measured_val) -> int:
    return round(measured_val / 154,3)

# Set vars for pins
trigPin=23
echoPin=24
ledPin=21

# Setup pins
GPIO.setup(trigPin,GPIO.OUT)
GPIO.setup(echoPin,GPIO.IN)
GPIO.setup(ledPin,GPIO.OUT)

try:
    while True:
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
        distance = calc_distance(pingTime)

        if distance > 1.5:
            GPIO.output(ledPin,0)

        # If distance within 6in. print current distance
        if distance <= 6.0:
            print(f"Distance to target = {distance}in.\n")
            if distance <= 1.5:
                GPIO.output(ledPin,1)
    
        time.sleep(.2)

except KeyboardInterrupt:
    GPIO.cleanup()
    print("\nGPIO Released...")