#include "Arduino.h"
#include <stdlib.h>
#include <stdio.h>
#include <ctime>

#define SerialA SerialUSB
#define SerialB Serial1

typedef enum response_codes
{
  EL_OK, EL_OVERFLOW, EL_PARSE_ERROR, EL_COMMAND_NOT_FOUND, EL_PARAMETER_ERROR,
  EL_INVALID_ESCAPE, EL_NO_CONNECTION, EL_TOPIC_OUT_OF_RANGE, EL_TOPIC_UNDEFINED,
  EL_INVALID_KEY_LENGTH, EL_INVALID_KEY_NAME, EL_UNKNOWN_KEY, EL_KEY_READONLY,
  EL_KEY_WRITEONLY, EL_UNABLE_TO_CONNECT, EL_TIME_NOT_AVAILABLE, EL_LOCATION_NOT_AVAILABLE,
  EL_MODE_NOT_AVAILABLE, EL_ACTIVE_CONNECTION, EL_HOST_IMAGE_NOT_AVAILABLE, EL_INVALID_ADDRESS,
  EL_INVALID_OTA_UPDATE, EL_INVALID_QUERY, EL_INVALID_SIGNATURE
}response_codes_t;

String SendCommand(String command)
{
  SerialB.print(command+"\n");
  String response = SerialB.readString();
  return response;
}

response_codes_t checkResponse(String response)
{
  if(response.indexOf("OK")!= -1) return EL_OK;
  //int errPosition = response.indexOf("ERR");
  response_codes_t errCode =  (response_codes_t) response.substring(3).toInt();
  return errCode;
}

void expressLinkConnect()
{
  String response;
  bool finished = false;

  response = SendCommand("AT+CONNECT?");
  if(response.indexOf("OK 1")==-1)
  {
    SerialA.println("Connecting ExpressLink");
    do{
      response = SendCommand("AT+CONNECT");
      if(checkResponse(response) == EL_OK)
      {
        finished = true;
      }
      else
      {
        SerialA.println(response);
      }
    } while(!finished);
    SerialA.println("Connected to ExpressLink");
  }
}

void generateAndSendData(int index){
  // Payload components
/*
    Temperature         -> The measured temperature in degrees Fahrenheit.
    Humidity            -> The measured relative humidity.
    Pressure            -> The measured pressure in inches of Mercury or Hg.
    Solar_radiation/UV  -> The measured UV shown as UV index.
    Wind direction      -> The wind direction in degrees.
    Wind speed          -> The measured windspeed in Miles per Hour.
    Location            -> The state that the reporting station sends its data to.
  */


  // Random value for temperature (between 40 to 70 degrees Fahrenheit)
  int temp = (rand() % 31) + 40; 

  // Random value for pressure (between 29.6 to 30.2 inches Hg)
  float pressure = (float)(rand() % 61)/(float)100 + 29.6; 

  // Random value for relative humidity (between 30 to 90)
  int humidity = (rand() % 61) + 30; 

  // Random value for UV index (between 1 to 11)
  int UV = (rand() % 11) + 1;

  // Random value for wind speed (between 7 to 12)
  float windSpeed = (rand() % 6) + 7 + (float)(rand()%10)/(float)10; 

  // Random value for wind direction (between 7 to 12)
  int windDir = rand() % 360; 

  // Random value for location
  String states[] = {"Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut", "Delaware", "Florida", "Georgia", "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota", "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire", "New Jersey", "New Mexico", "New York", "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota", "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington", "West Virginia", "Wisconsin", "Wyoming"};
  String location = states[rand() % 50];

  // sending the json payload
  
  if (index == 1) 
    SerialB.print("AT+SEND1 {\"Temperature\":");
  else if (index == 2)
    SerialB.print("AT+SEND2 {\"Temperature\":");
  else if (index == 3)
    SerialB.print("AT+SEND3 {\"Temperature\":"); 
  else if (index == 4)
    SerialB.print("AT+SEND4 {\"Temperature\":");  
   
  SerialB.print(temp);
  SerialB.print(",\"Pressure\":");
  SerialB.print(pressure);
  SerialB.print(",\"Humidity\":");
  SerialB.print(humidity);
  SerialB.print(",\"UV\":");
  SerialB.print(UV);
  SerialB.print(",\"Wind_Speed\":");
  SerialB.print(windSpeed);
  SerialB.print(",\"Wind_Direction\":");
  SerialB.print(windDir);
  SerialB.print(",\"Location\":");
  SerialB.print("\""+String(location)+ "\"");
  SerialB.println("}");
}

void setup() {

  SerialA.begin(115200);
  SerialB.begin(115200);

  while(!SerialA && !SerialB);

  SendCommand("AT+CONF Topic1=Timestream_demo");
  SendCommand("AT+CONF Topic2=Opensearch_demo");
  SendCommand("AT+CONF Topic3=IoT_Analytics_demo");
  SendCommand("AT+CONF Topic4=Kinesis_demo");

  expressLinkConnect();
}

void loop() {

  // Uncomment the line below to send data under "Timestream" topic to test the Timestream template
  //generateAndSendData(1);

  // Uncomment the line below to send data under "OpenSearch" topic to test the OpenSearch template
  // generateAndSendData(2);

  // Uncomment the line below to send data under "IoT Analytics" topic to test the IoT Analytics template
  // generateAndSendData(3);

  // Uncomment the line below to send data under "Kinesis" topic to test the Kinesis template
  // generateAndSendData(4);

  // send data every minute
  delay(60000);
}

