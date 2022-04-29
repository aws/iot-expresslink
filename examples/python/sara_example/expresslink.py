import busio
import time
from digitalio import DigitalInOut, Direction, Pull

class ExpressLink:
    event_pin:DigitalInOut # change to be an input pin with a callback
    powerOn_pin:DigitalInOut
    powerCheck_pin:DigitalInOut
    _connected:bool
    port:serial

    def __init__(self, port, event, powerOn, powerCheck):
        self.port = port
        self.event_pin = event
        self.powerOn_pin = powerOn
        self.powerCheck_pin = powerCheck
        self.event_pin.direction = Direction.INPUT
        self.powerCheck_pin.direction = Direction.INPUT
        self.powerOn_pin.direction = Direction.OUTPUT
        self.powerOn_pin.value = False

    # This function relies upon the SARA_ON signal to work
    def _powerOn(self)->bool:
        while self.powerCheck_pin.value == True:
            self.powerOn_pin.value = True
            time.sleep(.50)
        self.powerOn_pin.value = False
        time.sleep(.1)
        print("ExpressLink Powered")
        return True

    def _comCheck(self)->bool:
        print("Checking Communications")
        response = ""
        while response.find("OK") != 0:
            time.sleep(.5)
            response = self.sendCommand("AT")
        return True

    def begin(self):
        self._connected = False
        self._powerOn()
        self._comCheck()
        print("ExpressLink Up")

    def connect(self)->bool:
        response = self.sendCommand("AT+CONNECT?")
        print("connect_check : " + response)
        code = response.find("OK 1")
        if code == -1:
            self._connected = False
            response = self.sendCommand("AT+CONNECT")
            print("connect:"+response)
            if self.checkResponse(response) == 0:
                self._connected = True
        else:
            self._connected = True
        return self._connected

    def sendCommand(self, command:str)->str:
        command += '\n'
        self.port.write(command.encode("utf-8"))
        time.sleep(1)
        response = self.port.readline()
        if response != None:
            return response.decode("utf-8")
        else:
            return ""

    def checkResponse(self, response:str)->int:
        if response.find("OK") == 0:
            return 0
        else:
            if response.find("ERR") == 0:
                return int(response[3:])
            else:
                return -1
        
        