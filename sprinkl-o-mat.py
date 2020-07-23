#!/usr/bin/python
import mysql.connector as DB
from mysql.connector import Error
import RPi.GPIO as GPIO
import time
import spidev
from datetime import date, datetime
import logging

logging.basicConfig(filename='errors.log', format='%(asctime)s - %(message)s')

# Customizing the settings of the irrigation system
VARS = {
        "MOISTURE_THRESHOLD": 480,
        "MOISTURE_CHANNEL": 0,
        "WATER_PUMP_GPIO": 17,
        "WATERING_TIME_IN_S": 1
        }

# List of all moisture sensores in use
MOISTURESENSORS = {
        "DEFAULT": 1
        }

# Read data to connect to the DB
f = open("pass", "r")
host = f.readline().rstrip("\n")
db = f.readline().rstrip("\n")
user = f.readline().rstrip("\n")
dbPass = f.readline().rstrip("\n")
f.close()

roundTo = 2

spi = spidev.SpiDev()
spi.open(0,0)
spi.max_speed_hz=1000000

def readSpi(channel):
  val = spi.xfer2([1,(8+channel)<<4,0])
  data = ((val[1]&3) << 8) + val[2]
  return data

# Dry:   >430
# Wet:   430-350
# Water: <350
def needWater():
    moisture_level = readSpi(VARS["MOISTURE_CHANNEL"])
    logToDB(MOISTURESENSORS["DEFAULT"], moisture_level)
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

def logToDB(moistureSensorId, moisture): 
    connection = None
    
    try:
        connection = DB.connect(
                host=host,
                database=db,
                user=user,
                password=dbPass
                )

        if connection.is_connected():
          cursor = connection.cursor()
          query = "INSERT INTO irrigationsys (moistureSensorId, timedate, moisture) VALUES (%s, %s, %s)"
          data = (moistureSensorId, datetime.now(), moisture)
          cursor.execute(query, data)
          connection.commit()
              
    except Error as e:
        logging.error(e)

    finally:
        if (connection != None and connection.is_connected()):
          connection.close()
          print("MySQL connection is closed")


waterPlants()
