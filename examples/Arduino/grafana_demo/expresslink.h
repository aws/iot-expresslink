
#pragma once

class expresslink{
  HardwareSerial& _port;
  const int _wake;
  const int _event;
  const int _reset;
  bool _connected;

  void _doReset();

  public:
  expresslink(int wake, int event, int reset, HardwareSerial &port):_port(port), _wake(wake), _event(event), _reset(reset), _connected(false) {};
  ~expresslink(){};
  bool connect();
  void begin();
  String sendCommand(String);
  int checkResponse(String);
};
