#include "servoValve.h"

servoValve::servoValve(int servoPin) {
    _servoPin = servoPin;
}

void servoValve::begin() {
    _servo.attach(_servoPin);
    close();
}

void servoValve::close() {
    _servo.write(0);
}

void servoValve::open() {
    _servo.write(180);
}