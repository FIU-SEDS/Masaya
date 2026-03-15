#include "solenoid.h"

solenoid::solenoid(int pin) {
    _pin = pin;
}

void solenoid::begin() {
    pinMode(_pin, OUTPUT);

    digitalWrite(_pin, HIGH); //Start Closed
}

void solenoid::close(){
    digitalWrite(_pin, LOW);
}

void solenoid::open(){
    digitalWrite(_pin, HIGH);
}