from django.shortcuts import render
from django.views.generic import View
from django.http import HttpResponse
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from models import Strip, Building, TrafficLight, Motor, Oled, OledImage
from forms import ImageUploadForm
from StripControl.settings import BASE_DIR

import json, glob

@method_decorator(csrf_exempt, name='dispatch')
class ApiView(View):
    def get(self, request, *args, **kwargs):
        response = {'motor': {}, 'strips': {}, 'traffic_light': {}, 'oleds': {}}

        strips = Strip.objects.all()
        for strip in strips:
            response['strips'][strip.strip_id] = {'buildings': {}, 'street_light': {}}

            buildings = strip.building_set.all()
            for building in buildings:
                response['strips'][strip.strip_id]['buildings'][building.building_id] = {}

                response['strips'][strip.strip_id]['buildings'][building.building_id]['building_led_max'] = building.building_led_max
                response['strips'][strip.strip_id]['buildings'][building.building_id]['building_led_min'] = building.building_led_min

                response['strips'][strip.strip_id]['buildings'][building.building_id]['building_red'] = building.building_red
                response['strips'][strip.strip_id]['buildings'][building.building_id]['building_green'] = building.building_green
                response['strips'][strip.strip_id]['buildings'][building.building_id]['building_blue'] = building.building_blue

                response['strips'][strip.strip_id]['buildings'][building.building_id]['building_mode'] = building.building_mode
                response['strips'][strip.strip_id]['buildings'][building.building_id]['building_type'] = building.building_type

            street_light = strip.streetlight_set.get(street_light_id=0)
            response['strips'][strip.strip_id]['street_light']['street_light_on'] = street_light.street_light_on

        motor = Motor.objects.get(motor_id=0)
        response['motor']['motor_on'] = motor.motor_on

        traffic_light = TrafficLight.objects.get(traffic_light_id=0)
        response['traffic_light']['traffic_light_mode'] = traffic_light.traffic_light_mode
        response['traffic_light']['traffic_light_power'] = traffic_light.traffic_light_power

        oleds = Oled.objects.all()
        for oled in oleds:
            response['oleds'][oled.oled_id] = {}
            response['oleds'][oled.oled_id]['images'] = []

            images = oled.oledimage_set.all()
            for image in images:
                response['oleds'][oled.oled_id]['images'].append(BASE_DIR + image.image_image.url)

        return HttpResponse(json.dumps(response))

    def post(self, request, *args, **kwargs):
        post = json.loads(request.body)

        if post.get('data', '') == 'building':
            strip_id = int(post.get('strip_id', ''))
            strip = Strip.objects.get(strip_id=strip_id)

            building = strip.building_set.get(building_id=post.get('building_id', ''))
            if 'building_red' in post.keys():
                building.building_red = int(post.get('building_red', ''))
            if 'building_green' in post.keys():
                building.building_green = int(post.get('building_green', ''))
            if 'building_blue' in post.keys():
                building.building_blue = int(post.get('building_blue', ''))

            if 'building_led_max' in post.keys():
                building.building_led_max = int(post.get('building_led_max', ''))
            if 'building_led_min' in post.keys():
                building.building_led_min = int(post.get('building_led_min', ''))

            building.save()

        if post.get('data', '') == 'motor':
            strip_id = int(post.get('strip_id', ''))
            strip = Strip.objects.get(strip_id=strip_id)
            
            if 'motor_on' in post.keys():
                motor = strip.motor_set.get(motor_id=0)
                if 'motor_on' in post.keys():
                    motor.motor_on = bool(post.get('motor_on', ''))
                    motor.save()
                else:
                    print('No changes detected')

        if post.get('data', '') == 'street_light':
            strip_id = int(post.get('strip_id', ''))
            strip = Strip.objects.get(strip_id=strip_id)

            if 'street_light_on' in post.keys():
                street_light = strip.streetlight_set.get(street_light_id=0)
                street_light.street_light_on = post.get('street_light_on', '') 
                street_light.save()
            else:
                print('No changes detected')

        if post.get('data', '') == 'traffic_light':
            traffic_light = TrafficLight.objects.get(traffic_light_id=0)

            if 'traffic_light_mode' in post.keys():
                traffic_light.traffic_light_mode = post.get('traffic_light_mode', '')
                traffic_light.save()
            if 'traffic_light_power' in post.keys():
                traffic_light.traffic_light_power = post.get('traffic_light_power', '')
                traffic_light.save()

        return HttpResponse('Posted')

class OledControlView(View):
    def get(self, request, *args, **kwargs):
        response = {'thumbnails': {'image_dirs': [w.replace('media/', '') for w in glob.glob('media/*') if 'thumb' in w], 'len': len([w.replace('media/', '') for w in glob.glob('media/*') if 'thumb' in w]), }, 'oleds': {}}

        oleds = Oled.objects.all()

        for oled in oleds:
            response['oleds'][oled.oled_id] = {}

            response['oleds'][oled.oled_id]['oled_on'] = oled.oled_on
            response['oleds'][oled.oled_id]['images'] = []

            oled_images = oled.oledimage_set.all()
            for image in oled_images:
                response['oleds'][oled.oled_id]['images'].append(image.image_thumbnail)

        return render(request, 'oled_control.html', {'response': response, })

    def post(self, request, *args, **kwargs):
        post = request.POST
        oled_id = post.get('oled_id', '')
        image_form = ImageUploadForm(request.POST, request.FILES or None)
        if image_form.is_valid():
            oled = Oled.objects.get(oled_id=oled_id)
            oled.oledimage_set.create(image_image=request.FILES.get('file', ''), image_thumbnail=request.FILES.get('file', ''))
            return HttpResponse('Posted')

        print('fail')
        return HttpResponse('Failed')

class StripControlView(View):
    def get(self, request, *args, **kwargs):
        strips = Strip.objects.all()

        response = {'strips': {}, 'motor': {}, 'traffic_light': {}}

        for strip in strips:
            response['strips'][strip.strip_id] = {'buildings': {}, 'street_light': {}}

            buildings = strip.building_set.all()
            for building in buildings:
                response['strips'][strip.strip_id]['buildings'][building.building_id] = {}

                response['strips'][strip.strip_id]['buildings'][building.building_id]['building_led_max'] = building.building_led_max
                response['strips'][strip.strip_id]['buildings'][building.building_id]['building_led_min'] = building.building_led_min

                response['strips'][strip.strip_id]['buildings'][building.building_id]['building_red'] = building.building_red
                response['strips'][strip.strip_id]['buildings'][building.building_id]['building_green'] = building.building_green
                response['strips'][strip.strip_id]['buildings'][building.building_id]['building_blue'] = building.building_blue

                response['strips'][strip.strip_id]['buildings'][building.building_id]['building_mode'] = building.building_mode
                response['strips'][strip.strip_id]['buildings'][building.building_id]['building_type'] = building.building_type

            street_light = strip.streetlight_set.get(street_light_id=0)
            response['strips'][strip.strip_id]['street_light']['street_light_on'] = street_light.street_light_on

        traffic_light = TrafficLight.objects.get(traffic_light_id=0)
        response['traffic_light']['traffic_light_mode'] = traffic_light.traffic_light_mode
        response['traffic_light']['traffic_light_power'] = traffic_light.traffic_light_power

        motor = Motor.objects.get(motor_id=0)
        response['motor']['motor_on'] = motor.motor_on

        return render(request, 'strip_control.html', {'response': response})

    def post(self, request, *args, **kwargs):
        post = json.loads(request.body)

        if post.get('data', '') == 'building':
            strip_id = int(post.get('strip_id', ''))
            strip = Strip.objects.get(strip_id=strip_id)

            buildings = strip.building_set.all()
            for building in buildings:
                building.building_red = int(post.get('building_red', ''))
                building.building_green = int(post.get('building_green', ''))
                building.building_blue = int(post.get('building_blue', ''))

                building.building_led_max = int(post.get('building_led_max', ''))
                building.building_led_min = int(post.get('building_led_min', ''))

                building.save()

        if post.get('data', '') == 'strip':
            strip_id = int(post.get('strip_id', ''))
            strip = Strip.objects.get(strip_id=strip_id)
            
            street_light = strip.streetlight_set.get(street_light_id=0)
            street_light.street_light_on = post.get('street_light_on', '') 

            street_light.save()

        if post.get('data', '') == 'motor':
            motor = Motor.objects.get(motor_id=0)
            motor.motor_on = post.get('motor_on', '')

            motor.save()

        if post.get('data', '') == 'traffic_light':
            print('Traffic light post')
            traffic_light = TrafficLight.objects.get(traffic_light_id=0)
            traffic_light.traffic_light_mode = post.get('traffic_light_mode', '')
            traffic_light.traffic_light_power = post.get('traffic_light_power', '')

            traffic_light.save()

        return HttpResponse('Posted')
