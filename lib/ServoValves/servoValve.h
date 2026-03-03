#ifndef SERVO_VALVE_H
#define SERVO_VALVE_H

#include <Arduino.h>
#include <Servo.h>

class servoValve {
  private:
    int _servoPin;
    Servo _servo;

  public:
    servoValve(int servoPin);
    void begin();
    void close();
    void open();
};

#endif