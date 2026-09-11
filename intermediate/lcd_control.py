#!/usr/bin/python3
"""
This program controls the display of an LCD1602 screen.

deps:
raspi-config
i2c-tools
libi2c-dev
smbus2 (pip package)

LCD must be connected to 3.3V, SDA and SCL pins.

I2C is enabled with 'sudo raspi-config' - if not present on 
rpi install with apt.

Once wired, run 'sudo i2cdetect -y 1' to get the address
"""
import LCD1602 as lcd
import time

def main() -> None:
    hex_address=0x27
    lcd.init(hex_address, 1)

    try:
        while True:
            lcd.write(0,0, "Hello, World!")
            lcd.write(0, 1, "LCD!")
    except KeyboardInterrupt:
        print("\n")
    finally:
        time.sleep(0.5)
        lcd.clear()
        print("lcd cleared of input")


if __name__ == "__main__":
    main()