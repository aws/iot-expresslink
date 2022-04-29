import json
import time
import board
import adafruit_bme680
import busio
from countio import Counter, Edge
from digitalio import DigitalInOut, Direction, Pull
from analogio import AnalogIn

from expresslink import ExpressLink

time.sleep(2)
print("WeatherStation Startup")

def GetVoltage(pin):
    return (pin.value * 3.3) / 65536

# Resistor table
resistorTable = (('N',33000), ('NNE',6570), ('NE',8200), ('ENE',891), ('E',1000), ('ESE',688), ('SE',2200),('SSE',1410),('S',3900),('SSW',3140),('SW',16000),('WSW', 14120),('W',120000),('WNW',42120),('NW',64900), ('NNW', 21880))

# Compute correct Resistance
# Top resistor 10k
# Supply voltage is 3.3v
# R = (v * 10000)/(3.3-v)

def getDirection(pin)->str:
    v = GetVoltage(pin)
    r = (v * 10000.0) / (3.3 - v)
    smallestValue = 10000000
    direction = ""
    for entry in resistorTable:
        distance = abs(r - entry[1])
        if distance < smallestValue:
            direction = entry[0]
            smallestValue = distance
    return direction

lastTime = 0
oldSpeed = 0
def getSpeed(pin:Counter)->float:
    global lastTime, oldSpeed
    thisTime = time.time()
    deltaTime = thisTime - lastTime
    if deltaTime > 10:
        windCount = pin.count
        pin.reset()
        lastTime = thisTime
        hz = windCount / deltaTime
        oldSpeed = 2.4 * hz # km/hr
    return oldSpeed

lastTip = 0
previousTipCount = 0
def getRainDepth(pin:Counter)->float:
    global lastTip, previousTipCount
    now = time.time()
    tips = pin.count
    if previousTipCount != tips:
        lastTip = now
        previousTipCount = tips
    else:
        if now - lastTip > (24*3600): # if there are no tips for 24 hours,
            pin.reset()                # reset the count
            previousTipCount = 0
            tips = 0
    return tips * 0.2794 # depth in mm


windDirection = AnalogIn(board.A0)

uart = busio.UART(board.UART_TX1, board.UART_RX1, baudrate=115200, timeout=30)
el = ExpressLink(uart, DigitalInOut(board.G5), DigitalInOut(board.G2), DigitalInOut(board.G6) )

el.begin()

print("ExpressLink Started")

i2c = board.I2C()
bme680 = adafruit_bme680.Adafruit_BME680_I2C(i2c,debug=False)

temperature_offset=-5

rain = Counter(board.D1, edge=Edge.FALL, pull=Pull.UP)
rain.reset()
wind = Counter(board.PWM0, edge=Edge.FALL, pull=Pull.UP)
wind.reset()

response = el.sendCommand('AT+CONF? ThingName')
thingName = response[3:]
response = el.sendCommand("AT+CONF Topic1=/weather/sensor/" + thingName)

while True:

    if el.connect():
        report = {}
        report["temperature"] = bme680.temperature+temperature_offset
        report["gas"] = bme680.gas
        report["humidity"] = bme680.relative_humidity
        report["pressure"] = bme680.pressure
        report["wind direction"] = getDirection(windDirection) 
        report["wind speed"] = getSpeed(wind)
        report["rain"] = getRainDepth(rain)
        data = json.dumps(report)
        print("Reporting : " + data)
        el.sendCommand("AT+SEND1 " + data)
    else:
        print("No connection")
        el.begin()
    
    time.sleep(1)