/***************************************************
  Simple serial server
****************************************************/

// Pin 13 has an LED connected on most Arduino boards.
int led_pin = 13;

//serial
String inputString = "";         // a string to hold incoming data
boolean stringComplete = false;  // whether the string is complete

void setup(){
  //delay(100); //wait for bus to stabalise
  // serial
  Serial.begin(9600);
  // reserve 200 bytes for the inputString:
  inputString.reserve(200);
}

void loop(){
  // print the string when a newline arrives:
  if (stringComplete) {
    flash(200);
    Serial.println(inputString);
    // clear the string:
    inputString = "";
    stringComplete = false;
  }
}

/*
 SerialEvent occurs whenever a new data comes in the
 hardware serial RX.  This routine is run between each
 time loop() runs, so using delay inside loop can delay
 response.  Multiple bytes of data may be available.
 */
void serialEvent() {
  while (Serial.available()) {
    // get the new byte:
    char inChar = (char)Serial.read();
    // add it to the inputString:
    inputString += inChar;
    // if the incoming character is a newline, set a flag
    // so the main loop can do something about it:
    if (inChar == '\n') {
      stringComplete = true;
    }
  }
}

// Flash the led for the given time (milliseconds)
void flash(int msecs){
    digitalWrite(led_pin, HIGH);
    delay(msecs);
    digitalWrite(led_pin, LOW);
}
