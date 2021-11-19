/*
  SerialPassthrough for ExpressLink

  Based upon the buildin passthrough example
  https://www.arduino.cc/en/Tutorial/BuiltInExamples/SerialPassthrough
*/

#define SerialA SerialUSB
#define SerialB Serial1

void setup() {
  SerialA.begin(115200);
  SerialB.begin(115200);

  while(!SerialA && !SerialB);
}

void loop() {
  if (SerialA.available()) {      // If anything comes in Serial (USB),
    SerialB.write(SerialA.read());   // read it and send it out Serial1 (pins 0 & 1)
  }

  if (SerialB.available()) {     // If anything comes in Serial1 (pins 0 & 1)
    SerialA.write(SerialB.read());   // read it and send it out Serial (USB)
  }
}
