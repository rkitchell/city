from __future__ import unicode_literals

from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import models

from PIL import Image
import StringIO

class Strip(models.Model):
    strip_id = models.IntegerField(default=0)
    
    def __str__(self):
        return str(self.strip_id)

class Building(models.Model):
    building_strip = models.ForeignKey(Strip, on_delete=models.CASCADE)

    building_id = models.IntegerField(default=0)

    building_type = models.TextField(default='', max_length=50)

    building_mode = models.TextField(default='fill')

    building_led_max = models.IntegerField(default=0)
    building_led_min = models.IntegerField(default=0)

    building_red   = models.IntegerField(default=0)
    building_green = models.IntegerField(default=0)
    building_blue  = models.IntegerField(default=0)

    def __str__(self):
        return str(self.building_type)

class Motor(models.Model):
    motor_id = models.IntegerField(primary_key=True, default=0)

    motor_on = models.BooleanField(default=False)

    def __str__(self):
        return str(self.motor_on)

class TrafficLight(models.Model):
    traffic_light_id = models.IntegerField(default=0)

    traffic_light_mode = models.BooleanField(default=True)
    traffic_light_power = models.BooleanField(default=False)

class StreetLight(models.Model):
    street_light_strip = models.ForeignKey(Strip, on_delete=models.CASCADE)

    street_light_id = models.IntegerField(default=0)

    street_light_on = models.BooleanField(default=False)

class Oled(models.Model):
    oled_id = models.IntegerField(default=0)

    oled_on = models.BooleanField(default=False)

    def __str__(self):
        return str(oled_id)

class OledImage(models.Model):
    image_oled = models.ForeignKey(Oled, on_delete=models.CASCADE)

    image_image = models.ImageField(upload_to='')
    image_thumbnail = models.ImageField(upload_to='')

    def save(self, *args, **kwargs):
        if self.image_image:
            image = Image.open(StringIO.StringIO(self.image_thumbnail.read()))
            image.thumbnail((200, 200), Image.ANTIALIAS)

            if image.mode == "RGBA":
                image.load()
                background = Image.new("RGB", image.size, (255, 255, 255))
                background.paste(image, mask=image.split()[3]) # 3 is the alpha channel
                image = background

            output = StringIO.StringIO()
            image.save(output, format='JPEG', quality=99)
            output.seek(0)
            self.image_thumbnail = InMemoryUploadedFile(output, 'ImageField', "%s_thumb.jpg" %self.image_thumbnail.name.split('.')[0], 'image/*', output.len, None)
        super(OledImage, self).save(*args, **kwargs)
