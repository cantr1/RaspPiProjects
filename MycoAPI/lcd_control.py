"""Small adapter for the supplied 16x2 LCD driver."""
import logging

logger = logging.getLogger(__name__)


class LCD_Control:
    def __init__(self):
        self.lcd = None
        try:
            import LCD1602 as lcd

            self.lcd = lcd
            if not lcd.init(0x27, 1):
                raise OSError('LCD initialization failed at I2C address 0x27')
            self.show('MycoAPI ready', 'Waiting for read')
        except (OSError, ImportError):
            logger.exception('LCD unavailable; API will continue without the display')
            self.close()
            self.lcd = None

    def show(self, first_line: str, second_line: str):
        if self.lcd is None:
            return
        try:
            # Pad to erase old characters; truncate to avoid wrapping the display.
            self.lcd.write(0, 0, first_line[:16].ljust(16))
            self.lcd.write(0, 1, second_line[:16].ljust(16))
        except OSError:
            logger.exception('LCD update failed')

    def show_measurement(self, temperature_c: float, humidity: float):
        self.show(f'Temp: {temperature_c:.1f}C', f'Humidity: {humidity:.1f}%')

    def close(self):
        if self.lcd is not None:
            try:
                self.lcd.close()
            except OSError:
                logger.exception('LCD cleanup failed')
