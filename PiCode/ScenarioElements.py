import threading, time
import wiringpi2 as wiringpi

import RPi.GPIO as GPIO

class Motor:
    def __init__(self):
        # Setup GPIOs for motors
        self.A = 15
        self.B = 18
        self.en = 12

        self.led = 6

        self.on = False

        GPIO.setmode(GPIO.BCM)

        GPIO.setup(self.A, GPIO.OUT)
        GPIO.setup(self.B, GPIO.OUT)
        GPIO.setup(self.en , GPIO.OUT)
        GPIO.setup(self.led, GPIO.OUT)

    def update(self, request):
        self.on = request['motor_on']

        if self.on:
            GPIO.output(self.en, GPIO.HIGH)
            GPIO.output(self.A, GPIO.LOW)
            GPIO.output(self.B, GPIO.LOW)

            GPIO.output(self.led, GPIO.LOW)
        else:
            GPIO.output(self.en, GPIO.HIGH)
            GPIO.output(self.B, GPIO.HIGH)
            GPIO.output(self.A, GPIO.LOW)

            GPIO.output(self.led, GPIO.HIGH)

class TrafficLight(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)

        self.mode = 'red'

        self.ns_red = 67
        self.ns_yellow = 66
        self.ns_green = 65

        self.ew_red = 73
        self.ew_yellow = 74
        self.ew_green = 75

        wiringpi.pinMode(65, 1) # sets GPA0 to output
        wiringpi.pinMode(66, 1) # sets GPA0 to output
        wiringpi.pinMode(67, 1) # sets GPA0 to output
        wiringpi.pinMode(73, 1) # sets GPA0 to output
        wiringpi.pinMode(74, 1) # sets GPA0 to output
        wiringpi.pinMode(75, 1) # sets GPA0 to output

    def update(self, request):
        mode = request['traffic_light_mode']
        power = request['traffic_light_power']
        if power:
            if mode == True:
                self.mode = 'red'
            else:
                self.mode= 'cycle'
        else:
            self.mode = 'off'

    def run(self):
        while True:
            print('Running traffic light')
            if self.mode == 'off':
                # Turn off
                wiringpi.digitalWrite(self.ns_red, 1)        #North and South Red on (All intersections)
                wiringpi.digitalWrite(self.ew_red, 1)        #East and West Red on (All intersections)
                wiringpi.digitalWrite(self.ew_yellow, 1)        #East and West Red on (All intersections)
                wiringpi.digitalWrite(self.ew_green, 1)        #East and West Red on (All intersections)
                wiringpi.digitalWrite(self.ns_yellow, 1)        #East and West Red on (All intersections)
                wiringpi.digitalWrite(self.ns_green, 1)        #East and West Red on (All intersections)
                time.sleep(1)

            else:
                if self.mode == 'red':
                    wiringpi.digitalWrite(self.ns_red, 0)        #North and South Red on (All intersections)
                    wiringpi.digitalWrite(self.ew_red, 0)        #East and West Red on (All intersections)

                    wiringpi.digitalWrite(self.ew_yellow, 1)        #East and West Red on (All intersections)
                    wiringpi.digitalWrite(self.ew_green, 1)        #East and West Red on (All intersections)
                    wiringpi.digitalWrite(self.ns_yellow, 1)        #East and West Red on (All intersections)
                    wiringpi.digitalWrite(self.ns_green, 1)        #East and West Red on (All intersections)
                    time.sleep(1)
                elif self.mode == 'cycle':
                    wiringpi.digitalWrite(self.ns_red, 1)    #North and South Red Off (All Intersections)
                    wiringpi.digitalWrite(self.ns_yellow, 1)    #North and South Yellow Off (All Intersections)
                    wiringpi.digitalWrite(self.ns_green, 0)    #North and South Green On (All Intersections)
                    time.sleep(5)
                    wiringpi.digitalWrite(self.ns_green, 1)    #North and South Green Off (All Intersections)
                    wiringpi.digitalWrite(self.ns_yellow, 0)    #North and South Yellow On (All Intersections)
                    time.sleep(1)
                    wiringpi.digitalWrite(self.ns_yellow, 1)    #North and South Yellow Off (All Intersections)
                    wiringpi.digitalWrite(self.ns_red, 0)    #North and South Red On (All Intersections)
                    time.sleep(2)

                    wiringpi.digitalWrite(self.ew_red, 1)    #East and West Red Off (All Intersections)
                    wiringpi.digitalWrite(self.ew_yellow, 1)    #East and West Yellow Off (All Intersections)
                    wiringpi.digitalWrite(self.ew_green, 0)    #East and West Green On (All Intersections)
                    time.sleep(5)
                    wiringpi.digitalWrite(self.ew_green, 1)    #East and West Green Off (All Intersections)
                    wiringpi.digitalWrite(self.ew_yellow, 0)    #East and West Yellow On (All Intersections)
                    time.sleep(1)
                    wiringpi.digitalWrite(self.ew_yellow, 1)    #East and West Yellow Off (All Intersections)
                    wiringpi.digitalWrite(self.ew_red, 0)    #East and West Red Off (All Intersections)
                    time.sleep(2)

class StreetLight:

    def __init__(self):
        # Setup pins
        wiringpi.pinMode(68, 1) # sets GPA0 to output
        wiringpi.pinMode(69, 1) # sets GPA1 to output
        wiringpi.pinMode(70, 1) # sets GPA2 to output
        wiringpi.pinMode(71, 1) # sets GPA3 to output
        wiringpi.pinMode(72, 1) # sets GPA4 to output

        wiringpi.digitalWrite(68, 1)
        wiringpi.digitalWrite(69, 1)
        wiringpi.digitalWrite(70, 1)
        wiringpi.digitalWrite(71, 1)
        wiringpi.digitalWrite(72, 1)

    def update_light(self, index, request):
        on = request['street_light_on']
        if index == 0:
            if on:
                wiringpi.digitalWrite(68, 0)
            else:
                wiringpi.digitalWrite(68, 1)
        if index == 1:
            if on:
                wiringpi.digitalWrite(69, 0)
            else:
                wiringpi.digitalWrite(69, 1)

        if index == 2:
            if on:
                wiringpi.digitalWrite(70, 0)
            else:
                wiringpi.digitalWrite(70, 1)

        if index == 3:
            if on:
                wiringpi.digitalWrite(71, 0)
            else:
                wiringpi.digitalWrite(71, 1)

        if index == 4:
            if on:
                wiringpi.digitalWrite(72, 0)
            else:
                wiringpi.digitalWrite(72, 1)

class Building:

    def __init__(self, index, request):
        self.index = index
        self.min = request['building_led_min']
        self.max = request['building_led_max']
        self.mode = request['building_mode']
        self.blink_status = True

        self.red = request['building_red']
        self.green = request['building_green']
        self.blue = request['building_blue']

    def update_building(self, request):
        self.min = request['building_led_min']
        self.max = request['building_led_max']
        self.mode = request['building_mode']
        self.blink_status = True

        self.red = request['building_red']
        self.green = request['building_green']
        self.blue = request['building_blue']
