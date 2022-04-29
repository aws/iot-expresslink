# U-Blox SARA R5 ExpressLink CircuitPython Demo

# ExpressLink Configuration
Execute manual steps in the expresslink getting started guide to get the Ublox ExpressLink connected to your AWS account.

# HW Configuration
The SARA R5 ExpressLink board must be configured to enable the power state feedback.  This signal is labeled SARA_ON on the schematic.
On the back of the board, you must apply a solder blob to the two pads labeled SARA_ON to connect that signal to G6 on the micromod.

The tipping bucket is connected to signal D1 on the right side of the expresslink board.
The wind speed is connected to signal PWM0 on the right side of the expresslink board.
The wind direction is connected to signal A1 on the right side of the expresslink board.
The wind direction is also connected to 3.3v via a 10k resistor.  I was able to bridge A1 to the QWICC 3v3 pin with a surface mount resistor and a bit of wire.

Attach the QWICC BME680 cable between the BME680 and the ExpressLink bkard.

# SW Configuration
Install the CircuitPython image from this location: https://circuitpython.org/board/sparkfun_micromod_rp2040/

Install the BME680 CircuitPython library from this location: https://github.com/adafruit/Adafruit_CircuitPython_BME680
The BME680 library can be simply copied into the LIB folder present on the CIRCUITPY filesystem after the CircuitPython image is installed.
Connect a USB cable to the board and open a terminal.  115200 8N1
copy expresslink.py and code.py into the CIRCUITPY filesystem and watch the data.

