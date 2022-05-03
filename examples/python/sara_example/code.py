import json
import time
import board
import adafruit_bme680
import busio
from countio import Counter, Edge
from digitalio import DigitalInOut, Direction, Pull
from analogio import AnalogIn
from weather_station import weather_station

from expresslink import ExpressLink

time.sleep(2)
print("WeatherStation Startup")

def celsius2fahrenheit(celsius:float)->float:
    return ((celsius * 9.0)/5.0) + 32.0

def GetVoltage(pin):
    return (pin.value * 3.3) / 65536

# Resistor table
resistorTable = ((0,33000), (22.5,6570), (45,8200), (67.5,891), (90,1000), (112.5,688), (135,2200),(157.5,1410),(180,3900),(202.5,3140),(225,16000),(247.5, 14120),(270,120000),(292.5,42120),(315,64900), (337.5, 21880))

# Compute correct Resistance
# Top resistor 10k
# Supply voltage is 3.3v
# R = (v * 10000)/(3.3-v)

def getDirection(pin)->float:
    v = GetVoltage(pin)
    r = (v * 10000.0) / (3.3 - v)
    smallestValue = 10000000
    direction = 0.0
    for entry in resistorTable:
        distance = abs(r - entry[1])
        if distance < smallestValue:
            direction = entry[0]
            smallestValue = distance
    return direction

lastTime = time.time()
def getSpeed(pin:Counter)->float:
    global lastTime
    thisTime = time.time()
    deltaTime = thisTime - lastTime
    windSpeed = pin.count / deltaTime
    pin.reset()
    lastTime = thisTime
    windSpeed *= 1.492
    return windSpeed # return wind speed in mph

# todo: fix rain reset for 24 hours.  use absolute time from expreslink
lastTip = time.time()
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
    return ( tips * 0.2794 ) / 25.4 # depth in in

ws = weather_station()

windDirection = AnalogIn(board.A0)

uart = busio.UART(board.UART_TX1, board.UART_RX1, baudrate=115200, timeout=30)
el = ExpressLink(uart, DigitalInOut(board.G5), DigitalInOut(board.G2), DigitalInOut(board.G6) )

el.begin()

print("ExpressLink Started")

led = DigitalInOut(board.G10)
led.direction = Direction.OUTPUT


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

reportCounter = 60
while True:
    led.value = True
    reportCounter -= 1

    ws.addWind(getSpeed(wind), getDirection(windDirection))

    if reportCounter == 0:
        if el.connect() and reportCounter == 0:
            reportCounter = 60
            report = {}
            report["tempf"] = celsius2fahrenheit( bme680.temperature+temperature_offset )
            report["humidity"] = bme680.relative_humidity
            report["pressure"] = bme680.pressure
            report["winddir"] = ws.windDirection
            report["windspeedmph"] = ws.windSpeed
            report["windgustmph"] = ws.windGust1minSpeed
            report["windgustdir"] = ws.windGust1minDirection
            report["windspdmph_avg2m"] = ws.wind2MinAverageMPH
            report["winddir_avg2m"] = ws.wind2MinAverageDirection
            report["windgustmph_10m"] = ws.wind10MinGustMPH
            report["windgustdir_10m"] = ws.wind10MinGustDirection
            report["dailyrainin"] = getRainDepth(rain)
            data = json.dumps(report)
            print("Reporting : " + data)
            el.sendCommand("AT+SEND1 " + data)
        else:
            reportCounter = 2 # try again in 2 seconds
            print("No connection")

    # ensure the LED blink is noticable
    time.sleep(.5)
    led.value = False
    time.sleep(.5)