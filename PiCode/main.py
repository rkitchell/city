#!/usr/bin/python3

import RPi.GPIO as GPIO
import time
import threading
import urllib.request as urllib2
import json
import glob
import wiringpi

import gaugette.ssd1351
import gaugette.platform

from LPD8806 import LPD8806 as LPD
from ScenarioElements import Building, Motor, TrafficLight, StreetLight

class OledGPIO():
    def __init__(self):
        # S0 is LSB
        self.s0 = 22
        self.s1 = 27
        self.s2 = 17
        self.s3 = 4

        self.outputs =  {
                                6:  [GPIO.LOW,  GPIO.HIGH, GPIO.HIGH, GPIO.LOW] ,
                                7:  [GPIO.LOW,  GPIO.HIGH, GPIO.HIGH, GPIO.HIGH],
                                8:  [GPIO.HIGH, GPIO.LOW,  GPIO.LOW,  GPIO.LOW] ,
                                9:  [GPIO.HIGH, GPIO.LOW,  GPIO.LOW,  GPIO.HIGH],
                                10: [GPIO.HIGH, GPIO.LOW,  GPIO.HIGH, GPIO.LOW] ,
                                11: [GPIO.HIGH, GPIO.LOW,  GPIO.HIGH, GPIO.HIGH],
                                12: [GPIO.HIGH, GPIO.HIGH, GPIO.LOW,  GPIO.LOW] ,
                                13: [GPIO.HIGH, GPIO.HIGH, GPIO.LOW,  GPIO.HIGH],
                                14: [GPIO.HIGH, GPIO.HIGH, GPIO.HIGH, GPIO.LOW] ,
                                15: [GPIO.HIGH, GPIO.HIGH, GPIO.HIGH, GPIO.HIGH],
                        }

    def kill(self):
        GPIO.cleanup()

    def setup(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.s0, GPIO.OUT) 
        GPIO.setup(self.s1, GPIO.OUT) 
        GPIO.setup(self.s2, GPIO.OUT) 
        GPIO.setup(self.s3, GPIO.OUT)

    def select_output(self, pin_out):
        pin_set = self.outputs[pin_out]

        GPIO.output(self.s3, pin_set[0])
        GPIO.output(self.s2, pin_set[1])
        GPIO.output(self.s1, pin_set[2])
        GPIO.output(self.s0, pin_set[3])

class StripGPIO:
    def __init__(self):
        self.s0 = 26 
        self.s1 = 19
        self.s2 = 13
        self.demux_signal= {
                                0: [GPIO.LOW, GPIO.LOW, GPIO.LOW], 
                                1: [GPIO.LOW, GPIO.LOW, GPIO.HIGH],
                                2: [GPIO.LOW, GPIO.HIGH, GPIO.LOW],
                                3: [GPIO.LOW, GPIO.HIGH, GPIO.HIGH],
                                4: [GPIO.HIGH, GPIO.LOW, GPIO.LOW],
                                5: [GPIO.HIGH, GPIO.LOW, GPIO.HIGH],
                                6: [GPIO.HIGH, GPIO.HIGH, GPIO.LOW],
                                7: [GPIO.HIGH, GPIO.HIGH, GPIO.HIGH],
                            }

        # Mapping the strips to the demux outputs
        self.gpio_mapping = {0: 0, 1: 1, 2: 2, 3: 3, 4: 7}

    def setup(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.s0, GPIO.OUT)
        GPIO.setup(self.s1, GPIO.OUT)
        GPIO.setup(self.s2, GPIO.OUT)

    def gpio_write(self, index):
        # Activate demux
        GPIO.output(self.s2, self.demux_signal[self.gpio_mapping[index]][0])
        GPIO.output(self.s1, self.demux_signal[self.gpio_mapping[index]][1])
        GPIO.output(self.s0, self.demux_signal[self.gpio_mapping[index]][2])

class WebPoller(threading.Thread):

    def __init__(self, strips, oled, motor, street_light, traffic_light):
        threading.Thread.__init__(self)

        self.address = "http://127.0.0.1:8000/api/"
        self.request = {'motor': {}, 'strips': {}, 'traffic_light': {}}

        self.strips = strips
        self.oled = oled
        self.motor = motor
        self.street_light = street_light
        self.traffic_light = traffic_light

        self.init()

    def init(self):
        print('Initialising strips')
        request = self.get_request()
        for strip_key in request['strips'].keys():
            # Initialise strips
            self.request['strips'][strip_key] = {'buildings': {}, 'street_light': {}}
            # Add buildings
            for building_key in request['strips'][strip_key]['buildings'].keys():
                self.strips[int(strip_key)].add_building(int(building_key), request['strips'][strip_key]['buildings'][building_key])

    def get_request(self):
        try:
            request = json.loads(urllib2.urlopen(self.address).read().decode('utf-8'))
        except urllib2.URLError:
            print('Server not reached; is it online?')
        return request

    def run(self):
        while True:
            request = self.get_request()
            for strip_key in request['strips'].keys():
                if self.request['strips'][strip_key] != request['strips'][strip_key]:
                    # Check and update buildings
                    if request['strips'][strip_key]['buildings'] != self.request['strips'][strip_key]['buildings']:
                        self.request['strips'][strip_key]['buildings'] = request['strips'][strip_key]['buildings']
                        print("Updating buildings for strip: " + strip_key)
                        for building_key in request['strips'][strip_key]['buildings'].keys():
                            self.strips[int(strip_key)].buildings[int(building_key)].update_building(request['strips'][strip_key]['buildings'][building_key])
                            if self.strips[int(strip_key)].buildings[int(building_key)].mode == "blink":
                                self.strips[int(strip_key)].buildings[int(building_key)].blink_status = not self.strips[int(strip_key)].buildings[int(building_key)].blink_status
                        self.strips[int(strip_key)].update()

                    # Check and update street lights
                    if request['strips'][strip_key]['street_light'] != self.request['strips'][strip_key]['street_light']:
                        self.request['strips'][strip_key]['street_light'] = request['strips'][strip_key]['street_light']
                        self.street_light.update_light(int(strip_key), request['strips'][strip_key]['street_light'])
                        print('Updating street light for strip: ' + strip_key)

            # Check and update motors
            if request['motor'] != self.request['motor']:
                self.request['motor'] = request['motor']
                self.motor.update(request['motor'])
                print("Updating motors")

            # Check and update traffic lights
            if request['traffic_light'] != self.request['traffic_light']:
                self.request['traffic_light'] = request['traffic_light']
                self.traffic_light.update(request['traffic_light'])
                print('Updating traffic light')
            time.sleep(1)

class Strip:
    def __init__(self, index, gpio):
        self.index = index

        self.dataPin = 5
        self.clockPin = 21
        self.wait = 100

        self.len = 240

        self.gpio = gpio

        self.strip = LPD(self.len, self.dataPin, self.clockPin)
        self.strip.begin()
        self.fill(off=True)

        self.buildings = []
        self.motor = 0
        self.colour = []

    def update_num_leds(self, num):
        self.len = num
        self.strip.set_num_pixels(num)

    def add_building(self, index, request):
        if int(request['building_led_max']) > self.len:
            self.update_num_leds(int(request['building_led_max']))
        self.buildings.append(Building(index, request))

    def update(self):
        for i in range(self.strip.numPixels()):
            for building in self.buildings:
                if (i >= building.min or i <= building.max):
                    if building.mode == "fill":
                        self.colour.append(self.strip.colour(building.red, building.green, building.blue))
                    elif building.mode == "blink":
                        if building.blink_status == True:
                            self.colour.append(self.strip.colour(building.red, building.green, building.blue))
                        else:
                            self.colour.append(self.strip.colour(0, 0, 0))
                else:
                    self.colour.append(self.strip.colour(0, 0, 0))
        self.gpio.gpio_write(self.index)
        self.fill()

    def fill(self, off=False):
        self.gpio.gpio_write(self.index)
        time.sleep(0.1)
        print("Filling strip: " + str(self.index))
        if off:
            for i in range(self.strip.numPixels()):
                self.strip.setPixelColour(i, self.strip.colour(0, 0, 0))
        else:
            for i in range(self.strip.numPixels()):
                self.strip.setPixelColour(i, self.colour[i])
        self.colour = []
        self.strip.show()
        time.sleep(self.wait/8000.0)

class OLED:
    def __init__(self, gpio):
        # Uses WiriPi layout and pin numbering
        # Pin 16 DC and 18 RESET now connected
        # self.dc = 15 # Pin 8
        # self.reset = 16 # Pin 10 
        self.dc = 4 # Pin 8
        self.reset = 5 # Pin 10 

        self.rows = 96
        self.cols = 128

        self.oled = gaugette.ssd1351.SSD1351(reset_pin=self.reset, dc_pin=self.dc, rows=self.rows, cols=self.cols)

        self.gpio = gpio

        self.initialised = False

    def setup(self, pin):
        self.gpio.select_output(pin)
        time.sleep(0.01)
        self.oled.begin(reset=(not self.initialised))
        if self.initialised:
            self.initialised = True

    def mreset(self):
        self.oled.reset()

    def clear_screen(self):
        self.oled.fillScreen(0)

    def kill(self):
        self.clear_screen()
        GPIO.cleanup()

    def update(self, pin, img):
        img = Image.open(img)
        img = img.convert("RGB")

        img = self.resize(img)
        img_width, img_height = img.size
        
        self.oled.select_output(pin)

        pixels = []
        for y in range(img_height):
            row = []
            for x in range(img_width):
                red, green, blue = img.getpixel((x, y))
                row.append(self.oled.encode_color(((red << 16) | (green << 8) | blue)))
            pixels.append(row)

        self.oled.drawBitmap(0, 0, pixels)

    def resize(self, img):
        # Set height
        img_width, img_height = img.size
        sizing = self.rows/img_height
        img_width = int(sizing*img_width)
        img_height = self.rows

        # Check if height adjustment is necessary
        img_width, img_height = img.size
        if img_width > self.cols or img_height > self.rows:
            sizing = self.cols/img_width
            img_height = int(sizing*img_height)
            img_width = self.cols

        return img.resize((img_width, img_height), Image.ANTIALIAS)

class Main:
    def __init__(self):
        self.num_strips = 5

        self.oled_gpio = OledGPIO()
        self.oled_gpio.setup()

        self.strip_gpio = StripGPIO()
        self.strip_gpio.setup()

        self.strips = []
        self.oleds = OLED(self.oled_gpio)

        self.motor = Motor()

        self.WiringPiSetup()
        self.street_light = StreetLight()
        self.traffic_light = TrafficLight()

        for i in range(self.num_strips):
            self.strips.append(Strip(i, self.strip_gpio))

        for i in range(6, 16):
            self.oleds.setup(i)

        self.web = WebPoller(self.strips, self.oleds, self.motor, self.street_light, self.traffic_light)

    def WiringPiSetup(self):
        self.pin_base = 65       # lowest available starting number is 65 
        self.i2c_addr = 0x20     # A0, A1, A2 pins all wired to GND

        # Initialise wiringpi
        wiringpi.wiringPiSetup()                    # initialise wiringpi 
        wiringpi.mcp23017Setup(self.pin_base, self.i2c_addr)   # set up the pins and i2c address

    def start_web(self):
        self.web.daemon = True
        self.web.start()

    def start_traffic_light(self):
        self.traffic_light.daemon = True
        self.traffic_light.start()

    def start(self):
        self.start_traffic_light()
        self.start_web()

if __name__ == '__main__':
    main = Main()
    main.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print('Keyboard interrupt')
    finally:
        main.motor.update({'motor_on': False})
        # GPIO.cleanup()
