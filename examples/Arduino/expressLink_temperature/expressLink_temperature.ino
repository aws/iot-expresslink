#include <Wire.h>
#include <SparkFunTMP102.h>

TMP102 sensor0;

#define HIGH_TEMPERATURE 27.0
#define LOW_TEMPERATURE 26.0

// Helpers for ExpressLink command processing

typedef enum response_codes
{
  EL_OK, EL_OVERFLOW, EL_PARSE_ERROR, EL_COMMAND_NOT_FOUND, EL_PARAMETER_ERROR,
  EL_INVALID_ESCAPE, EL_NO_CONNECTION, EL_TOPIC_OUT_OF_RANGE, EL_TOPIC_UNDEFINED,
  EL_INVALID_KEY_LENGTH, EL_INVALID_KEY_NAME, EL_UNKNOWN_KEY, EL_KEY_READONLY,
  EL_KEY_WRITEONLY, EL_UNABLE_TO_CONNECT, EL_TIME_NOT_AVAILABLE, EL_LOCATION_NOT_AVAILABLE,
  EL_MODE_NOT_AVAILABLE, EL_ACTIVE_CONNECTION, EL_HOST_IMAGE_NOT_AVAILABLE, EL_INVALID_ADDRESS,
  EL_INVALID_OTA_UPDATE, EL_INVALID_QUERY, EL_INVALID_SIGNATURE
}response_codes_t;

#define expresslink_com Serial1

// Send a command and retrieve the response
String SendCommand(String command)
{
  expresslink_com.print(command+"\n");
  String response = expresslink_com.readString();
  return response;
}

// Get the response code from the begining of an ExpressLink response
response_codes_t checkResponse(String response)
{
  if(response.indexOf("OK")!= -1) return EL_OK;
  int errPosition = response.indexOf("ERR");
  response_codes_t errCode =  (response_codes_t) response.substring(3).toInt();
  return errCode;
}

// break out message after the OK/ERR# response
String getPayload(String response)
{
  
}

void expressLinkConnect()
{
  String response;
  bool finished = false;

  response = SendCommand("AT+CONNECT?");
  if(response.indexOf("OK 1")==-1)
  {
    SerialUSB.println("Connecting ExpressLink");
    do{
      response = SendCommand("AT+CONNECT");
      if(checkResponse(response) == EL_OK)
      {
        finished = true;
      }
      else
      {
        SerialUSB.println(response);
      }
    }while(!finished);
    SerialUSB.println("Connected to ExpressLink");
  }
}

// application

void setup() {
  delay(500);
  SerialUSB.begin(115200);
  while (!SerialUSB);
  
  Wire.begin();

  SerialUSB.println("checking the connection");
  
  if(!sensor0.begin())
  {
    SerialUSB.println("Cannot connect to TMP102.");
    SerialUSB.println("Check your connections.");
    while(1);
  }

  SerialUSB.println("Connected to TMP102!");

  expresslink_com.begin(115200);

  SendCommand("AT+CONF TopicRoot=ExpressLink_2021");
  SendCommand("AT+CONF Topic1=temperature");
  SendCommand("AT+CONF Topic2=alarm");

  expressLinkConnect();  

}

void loop() {

  static int lastSampleTime_ms = 0;
  static bool alert_pv = false;
  const int SamplePeriod_ms = 5000;
  int now = millis();

  if( (now - SamplePeriod_ms) >= lastSampleTime_ms)
  {
    lastSampleTime_ms = now;
    expressLinkConnect(); // ensure we are still connected to the cloud

    sensor0.wakeup();
    float temperature = sensor0.readTempC();
    sensor0.sleep();

    SerialUSB.print("Temperature : ");
    SerialUSB.print(temperature);
    SendCommand("AT+SEND1 "+String(temperature));
    if(temperature > HIGH_TEMPERATURE)
    {
      SerialUSB.println("  high alarm");
      alert_pv = true;
      SendCommand("AT+SEND2 {\"alarm\":\"HIGH\"}");
    }
    else if(temperature < LOW_TEMPERATURE)
    {
      SerialUSB.println("  low alarm");
      alert_pv = true;
      SendCommand("AT+SEND2 {\"alarm\":\"LOW\"}");
    }
    else
    {
      if(alert_pv)
      {
        SerialUSB.println("  alarm OK");
        SendCommand("AT+SEND2 {\"alarm\":\"OK\"}");
        alert_pv = false;
      }
      else
      {
        SerialUSB.println("");
      }
    }
  }
}
