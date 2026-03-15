#ifndef CD4051BE_H
#define CD4051BE_H

#include <Arduino.h>

class CD4051BE {
  private:
    int _pinA;
    int _pinB;
    int _pinC;

  public:
    CD4051BE(int pinA, int pinB, int pinC);

    void begin();
    void selectChannel(int channel);
    void channelReset();
};

#endif