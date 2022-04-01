#include "expresslink.h"

void expresslink::_doReset(void)
{
  digitalWrite(_reset,LOW);
  delay(10);
  digitalWrite(_reset,HIGH);
  delay(500);
}

void expresslink::begin(void)
{
  pinMode(_wake,OUTPUT);
  digitalWrite(_wake, LOW);
  pinMode(_reset, OUTPUT);
  digitalWrite(_reset, HIGH);
  pinMode(_event,INPUT);
  
  _port.begin(115200);
  _port.setTimeout(30000); // set the timeout longer than the longest command. (30 seconds in the spec)
  _connected = false;
  delay(100);
}

String expresslink::sendCommand(String command)
{
  _port.println(command);
  String response = _port.readStringUntil('\n');
  if(response.length() == 0)
  {
    _doReset();
  }
  return response;
}

int expresslink::checkResponse(String response)
{
  if(response.indexOf("OK")!= -1) return 0;
  return response.substring(3).toInt();
}

bool expresslink::connect()
{
  String response;

  response = sendCommand("AT+CONNECT?");
  int i = response.indexOf("OK 1");
  if(i==-1)
  {
    _connected = false;
    response = sendCommand("AT+CONNECT");
    if(checkResponse(response) == 0)
    {
      _connected = true;
    }
  }
  else
  {
    _connected = true;
  }
  return _connected;
}
