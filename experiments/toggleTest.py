import datetime
import os
from time import sleep
from Adafruit_IO import Client, RequestError

ADAFRUIT_IO_KEY = 'b25c2c664f0545a799b273029bfee3ce'
ADAFRUIT_IO_USERNAME = 'eeknud'

aio = Client(ADAFRUIT_IO_USERNAME, ADAFRUIT_IO_KEY) 

try:
    motorControlFeed = aio.feeds('motor-control')
except RequestError:
    print("feed error")

# Check the motor control forever
while True:
    motorState = aio.receive(motorControlFeed.key)
    print("Motor State : %s" % (motorState.value) )
    sleep(1)

