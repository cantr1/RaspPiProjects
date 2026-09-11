#!/usr/bin/python3
import LCD1602 as lcd
import RPi.GPIO as gpio
import dht11
import time

def main() -> None:
    gpio.setmode(gpio.BCM)
    dht = dht11.DHT11(pin = 26)

    # setup lcd
    lcd_hex_address = 0x27
    lcd.init(lcd_hex_address, 1)

    # setup toggle switch
    temp_setting_switch = 12
    gpio.setup(temp_setting_switch, gpio.IN, pull_up_down=gpio.PUD_UP)

    try:
        # Debug, print to LCD
        lcd.write(0,0, "INITIALIZING")
        lcd.write(0,1, "Hello, Wife!")
        time.sleep(2.5)
        temp_in_f = True # farenheit to start
        while True:
            # read temp / humidity and display
            temp_result = dht.read()
            if temp_result.is_valid():
                if temp_in_f:
                    converted_temp = (temp_result.temperature * (9/5)) + 32
                    lcd.write(0,0, f"Temp: {converted_temp:.2f}F")
                    lcd.write(0,1, f"Humidity: {temp_result.humidity}")
                else:
                    lcd.write(0,0, f"Temp: {temp_result.temperature:.2f}C")
                    lcd.write(0,1, f"Humidity: {temp_result.humidity}")

            # check input switch, if pressed flip temp_in_f
            read_val = gpio.input(temp_setting_switch)
            if read_val == 0:
                if temp_in_f:
                    temp_in_f = False
                else:
                    temp_in_f = True
            time.sleep(0.2)
    except KeyboardInterrupt:
        print("\n")
    finally:
        gpio.cleanup()
        time.sleep(0.5) # sleep to allow lcd to finish current command
        lcd.clear()


if __name__ == "__main__":
    main()