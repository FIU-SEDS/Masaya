#include <Arduino.h>
#include "CD4051BE.h" 

CD4051BE::CD4051BE(int pinA, int pinB, int pinC) {
    _pinA = pinA;
    _pinB = pinB;
    _pinC = pinC;
}

void CD4051BE::begin() {
    pinMode(_pinA, OUTPUT); 
    pinMode(_pinB, OUTPUT);
    pinMode(_pinC, OUTPUT);

    digitalWrite(_pinA, LOW);
    digitalWrite(_pinB, LOW);
    digitalWrite(_pinC, LOW);
}

void CD4051BE::channelReset(){
    digitalWrite(_pinA, LOW);
    digitalWrite(_pinB, LOW);
    digitalWrite(_pinC, LOW);
}

void CD4051BE::selectChannel(int channel){
    channelReset(); 
    
    digitalWrite(_pinA, (channel & 1)); 

    digitalWrite(_pinB, (channel & 2)); 

    digitalWrite(_pinC, (channel & 4)); 
}