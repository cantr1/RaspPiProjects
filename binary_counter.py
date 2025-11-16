#!/usr/bin/python3
# Converts a number to binary, then flashes LED's connected to GPIO 
# to represent the binary
import RPi.GPIO as GPIO
from time import sleep

def convert_to_binary(x: int) -> str:
    binary_num = ["0","0","0","0","0"]
    if x >= 16:
        binary_num[0] = "1"
        x -= 16
    if x >= 8:
        binary_num[1] = "1"
        x -= 8
    if x >= 4:
        binary_num[2] = "1"
        x -= 4
    if x >= 2:
        binary_num[3] = "1"
        x -= 2
    if x >= 1:
        binary_num[4] = "1"
        x-= 1
    return "".join(binary_num)

def main() -> None:
    GPIO.setmode(GPIO.BOARD)

    # GPIO Pins = Left -> Right
    L5, L4, L3, L2, L1 = 37, 23, 19, 13, 10
    GPIO.setup(L5, GPIO.OUT)
    GPIO.setup(L4, GPIO.OUT)
    GPIO.setup(L3, GPIO.OUT)
    GPIO.setup(L2, GPIO.OUT)
    GPIO.setup(L1, GPIO.OUT)

    for num in range(1,32):
        b = convert_to_binary(num)
        print(f"Number: {num} --- Binary: {convert_to_binary(num)}")
        if b[0] == "1":
            GPIO.output(L5,1)
        if b[1] == "1":
            GPIO.output(L4,1)
        if b[2] == "1":
            GPIO.output(L3,1)
        if b[3] == "1":
            GPIO.output(L2,1)
        if b[4] == "1":
            GPIO.output(L1,1)
        sleep(1)
        for pin in [37, 23, 19, 13, 10]:
            GPIO.output(pin,0)
        sleep(1)
    
if __name__ == "__main__":
    try:
        main()
        GPIO.cleanup()
    except Exception:
        print("Exiting script and cleaning up...")
        for pin in [37, 23, 19, 13, 10]:
            GPIO.output(pin,0)
        GPIO.cleanup()