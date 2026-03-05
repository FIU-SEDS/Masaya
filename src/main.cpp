#include <Arduino.h>
#include <servoValve.h>

#define sv1Pin PA5

servoValve sv1(PA5);

void setup() {
  sv1.begin();
}

void loop() {
  sv1.open();
  delay(600);
  sv1.close();
  delay(600);
}

