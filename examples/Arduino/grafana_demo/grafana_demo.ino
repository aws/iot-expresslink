/**
 * Report the temperature to the topic /dt/sensor/<thingname> so AWS timestream can catch the data.
 * Note, the topic is simply the one I specified for the timestream injest rule.
 * The JSON report includes the dimensions of 'device_id' and 'room' so that timestream queries can filter the data.
 * 
 * Special Note about using the Redboard Turbo (or any SAMD21 based arduino)  The main loop executes as follows:
 * while(1)
 * {
 *    loop();
 *    Update the USB Serial port()
 * }
 * So if you use an infinite loop or otherwise prevent loop from "looping" then the serial port will freeze and possibly be dropped from your PC.
 * 
 * 
 * Prerequisites:
 * Make sure your ExpressLink is registered in your account.  i.e. make a thing with the thingname/certificate from your expresslink and 
 * set the expresslink endpoint to match your account.  Follow the getting started guide from your ExpressLink to set this up.
 * 
 */
 
#include <Arduino_JSON.h>
#include <Wire.h> // Used to establied serial communication on the I2C bus
#include <SparkFunTMP102.h> // Used to send and recieve specific information from our sensor
#include <SparkFun_SGP30_Arduino_Library.h>
#include "expresslink.h"

TMP102 sensor0;
SGP30 sensor1;

#define Serial SerialUSB

#define REPORT_INTERVAL_MS 5000
#define AIR_QUALITY_MEASUREMENT_INTERVAL_MS 1000

String thingname = "no_thingname";

expresslink el(3,2,4, Serial1);

void setup() {
  Serial.begin(115200);
  Wire.begin();
  sensor0.begin();
  sensor1.begin();

  el.begin();
  String response = el.sendCommand("AT+CONF? ThingName");
  if(el.checkResponse(response) == 0)
  {
    thingname = response.substring(3);
    Serial.println("Found thingname : "+thingname);
    el.sendCommand("AT+CONF Topic1=/dt/sensor/" + thingname);
  }
  else
  {
    Serial.println("Reading the thingname failed");
  }
  sensor1.initAirQuality();
}

void loop()
{
  unsigned long now = millis();
  static unsigned long previousReport = 0;
  static unsigned long previousMeasurement = 0;

  if( ( now - previousMeasurement ) > AIR_QUALITY_MEASUREMENT_INTERVAL_MS )
  {
    previousMeasurement = now;
    sensor1.measureAirQuality(); // this function must be called every second
  }
  
  if( ( now - previousReport ) > REPORT_INTERVAL_MS )
  {
    previousReport = now;
    sensor0.wakeup();
    float temperature = sensor0.readTempC();
    sensor0.sleep();
     
    JSONVar dataReport;

    dataReport["room"] = "office";
    dataReport["owner"] = "joe";
    dataReport["device_id"] = thingname;
    dataReport["temperature"] = temperature;
    dataReport["voc"] = sensor1.TVOC;
    dataReport["co2"] = sensor1.CO2;

    if( el.connect() )
    {
      String command = "AT+SEND1 " + JSON.stringify(dataReport);
      String response = el.sendCommand(command);
      if(el.checkResponse(response) == 0)
      {
        Serial.println("reported : " + String(temperature,4));
      }
      else
      {
        Serial.println("Report Failed");
      }
    }
    else
    {
      Serial.println("No Connection");
    }
  }
}
