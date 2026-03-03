#ifndef SOLENOID_H
#define SOLENOID_H

#include <Arduino.h>

class solenoid {
  private:
    int _pin;

  public:
    solenoid(int pin);

    void begin();
    void open();
    void close();
};

#endif