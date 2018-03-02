import RPi.GPIO as GPIO
import time

class LPD8806:
    """
    Params: number of LEDs on strip to control, pin number of dataOut, pin number of Clk
    """
    def __init__(self, count, dataPin, clkPin):
        self.d = dataPin
        self.c = clkPin
        self.count = count
        self.pixels = [0] * count * 3
        GPIO.setmode(GPIO.BCM)

    """
    Setup the GPIOs for ouput
    """
    def begin(self):
        GPIO.setup(self.c, GPIO.OUT)
        GPIO.setup(self.d, GPIO.OUT)

    """
    Returns: the number of LEDs on the strip
    """
    def numPixels(self):
        return self.count

    def set_num_pixels(self, num):
        self.count = num
        self.pixels = [0] * self.count * 3

    """ 
    Params: 3 ints between 0-255 to set the colour of a pixel
    Return: 24-bit colour instruction
    """
    def colour(self, r, g, b):
        # Take the lowest 7 bits of each value and append them end to end
        # We have the top bit set high (its a 'parity-like' bit in the protocol
        # and must be set!)

        x = g | 0x80
        x <<= 8
        x |= r | 0x80
        x <<= 8
        x |= b | 0x80
        x <<= 8

        return x

    """ 
    Mimic an SPI out signal.
    Generate a clock signal by switching between high/low very quickly (SOFTWARE DEPENDANT, SO MAY INTRODUCE TIMING ISSUES)
    Write the data to the dataPin by shifting it out 8 bits at a time

    Params: 24-bit color 
    """
    def write8(self, d):
        # Basic, push SPI data out
        for i in range(8):
            GPIO.output(self.c, True)
            GPIO.output(self.d, (d & (0x80 >> i)) != 0)
            GPIO.output(self.c, False)

    # This is how data is pushed to the strip. 
    # Unfortunately, the company that makes the chip didn't release the 
    # protocol document or you need to sign an NDA or something stupid
    # like that, but we reverse engineered this from a strip
    # controller and it seems to work very nicely!
    def show(self):
        # get the strip's attention, send 32-bit low signal
        self.write8(0)
        self.write8(0)
        self.write8(0)
        self.write8(0)

        # write 24 bits per pixel, 72 bits in total
        for i in range(self.count):
            self.write8(self.pixels[i*3])
            self.write8(self.pixels[i*3+1])
            self.write8(self.pixels[i*3+2])
  
        # to 'latch' the data, we send just zeros
        # latching allows the LEDs to 'hold' their color 
        for i in range(self.count * 2):
            self.write8(0)
            self.write8(0)
            self.write8(0)

        # we need to have a delay here, 10ms seems to do the job
        # shorter may be OK as well - need to experiment :(
        time.sleep(0.5)

    # store the rgb component in our array
    def setPixelRGB(self, n, r, g, b):
        if n >= self.count: return

        self.pixels[n*3] =   r | 0x80
        self.pixels[n*3+1] = g | 0x80
        self.pixels[n*3+2] = b | 0x80

    def setPixelColour(self, n, c):
        if n >= self.count: return

        self.pixels[n*3+1] = (c >> 16) | 0x80    # g
        self.pixels[n*3] =   (c >> 8)  | 0x80    # r
        self.pixels[n*3+2] = (c)       | 0x80    # b
