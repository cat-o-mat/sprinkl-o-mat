#!/usr/bin/python

import RPi.GPIO as GPIO
import time
import spidev
import os
import time

VARS = {
        "MOISTURE_THRESHOLD": 430,
        "MOISTURE_CHANNEL": 0,
        "WATER_PUMP_GPIO": 17,
        "WATERING_TIME_IN_S": 1
        }

roundTo = 2

spi = spidev.SpiDev()
spi.open(0,0)
spi.max_speed_hz=1000000

def readSpi(channel):
  val = spi.xfer2([1,(8+channel)<<4,0])
  data = ((val[1]&3) << 8) + val[2]
  return data

def getVolts(data):
  volts = (data * 3.3) / float(1023)
  volts = round(volts,roundTo)
  return volts

# Dry:   >430
# Wet:   430-350
# Water: <350
def needWater():

    moisture_level = readSpi(VARS["MOISTURE_CHANNEL"])
    moisture_volts = getVolts(moisture_level)

    print("Moisture: Raw: {}, Volt: {}".format(moisture_level,moisture_volts))
    
    return (moisture_level >= VARS["MOISTURE_THRESHOLD"])

def waterPlants():
    if needWater():
      GPIO.setmode(GPIO.BCM)
      GPIO.setup(VARS["WATER_PUMP_GPIO"], GPIO.OUT)
      GPIO.output(VARS["WATER_PUMP_GPIO"], GPIO.LOW)
      time.sleep(VARS["WATERING_TIME_IN_S"])
      GPIO.output(VARS["WATER_PUMP_GPIO"], GPIO.HIGH)
      print("Watering finished.")
      GPIO.setup(VARS["WATER_PUMP_GPIO"], GPIO.IN)
    else:
        print("No need to water plants.")

waterPlants()
