/***************************************************
                ArcEyes USB Serial
****************************************************/

//settings:
const float referenceVolts = 5.5; //set the refrence multiplyer for the volt meter
unsigned long previousBattCheck = 10000;
const int send_delay = 100; //delay between sending packets

//#define DEBUG 1
#define DEBUG

#ifdef DEBUG
   #include <Wire.h>
   #include <LCD.h>
   #include <LiquidCrystal_I2C.h>

    //int LCD pins on I2C bus
    #define I2C_ADDR 0x27
    #define BACKLIGHT_PIN 3
    #define En_pin  2
    #define Rw_pin  1
    #define Rs_pin  0
    #define D4_pin  4
    #define D5_pin  5
    #define D6_pin  6
    #define D7_pin  7
    LiquidCrystal_I2C lcd(I2C_ADDR,En_pin,Rw_pin,Rs_pin,D4_pin,D5_pin,D6_pin,D7_pin);
#endif

//const
const int potPin1 = A0;
const int potPin2 = A1;
const int potPin3 = A2;
const int rlyPin1 = 6; // Relay Pin for break
const int rlyPin2 = 7; // Relay Pin for break
const int rlyPin3 = 8; // Relay Pin for break
const int motorPinSpeed1 = 3;
const int motorPinSpeed2 = 10;
const int motorPinSpeed3 = 11;
const int motorPinDir1 = 2;
const int motorPinDir2 = 4;
const int motorPinDir3 = 5;
const int batteryPin = A3;
const int lowBattLED = 13;

//var
boolean direct1 = LOW; // Stores what direction the motor should run in
boolean direct2 = LOW; // Stores what direction the motor should run in
boolean direct3 = LOW; // Stores what direction the motor should run in
float speedControl1 = 0; //store the current speed
float speedControl2 = 0; //store the current speed
float speedControl3 = 0; //store the current speed
long previousMillis = 0;  // store the time LCD was last updated
long interval = 50; // time between lcd updates
int lowBattCon = 0; //

struct Status {
  int yaw_pos;
  int pitch_pos;
  int lid_pos;
};

// 0..255
struct Command {
  int yaw_pwm;
  boolean yaw_direction;
  boolean yaw_brake;
  int pitch_pwm;
  boolean pitch_direction;
  boolean pitch_brake;
  int lid_pwm;
  boolean lid_direction;
  boolean lid_brake;

};

Status stat = { 0, 0, 0 };
Command cmd = { 0, true, 0, true, 0, true, LOW };

//struct Joint {
//  String name;
//  int pos;
//  int command;
//  boolean brake;
//}
//
//Joint yaw = { "Yaw", 0, 0, LOW };
//Joint pitch = { "Pitch", 0, 0, LOW };
//Joint lid = { "Lid", 0, 0, LOW };

//serial
String inputString = "";         // a string to hold incoming data
boolean stringComplete = false;  // whether the string is complete
String statusString = "";        // a string to hold the output

void setup(){
#ifdef DEBUG
 Wire.begin(); //start I2C bus
 delay(100); //wait for bus to stabalise
 lcd.begin (16,2); // 2 rows x 16 char
 // Switch on the backlight
 lcd.setBacklightPin(BACKLIGHT_PIN,POSITIVE);
 lcd.setBacklight(HIGH);
 lcd.clear();
 lcd.setCursor(0,0);
 lcd.print("ArcEyes MD03 I2C");
 lcd.setCursor(0,1);
 lcd.print("SandBox");
 delay(30);
#endif

  pinMode(rlyPin1,OUTPUT); // Setup pins
  pinMode(rlyPin2,OUTPUT); // Setup pins
  pinMode(rlyPin3,OUTPUT); // Setup pins
  pinMode(motorPinDir1,OUTPUT); // Setup pins
  pinMode(motorPinDir2,OUTPUT); // Setup pins
  pinMode(motorPinDir3,OUTPUT); // Setup pins
  
  //serial
  Serial.begin(115200);
  // reserve 200 bytes for the inputString:
  inputString.reserve(200);
  statusString.reserve(200);
}

void loop(){
  static unsigned long send_time = millis();
  lowBattCheck(); // check and respond to low battery
  read_status();
  
  // read commands when we get a full line
  if (stringComplete) {
    read_command();
#ifdef DEBUG
    lcd_command();
#endif
    do_command();
  }

  //direct1 = manualSpeedControl(motorPinSpeed1, potPin1, rlyPin1, motorPinDir1, direct1, speedControl1);
  //direct2 = manualSpeedControl(motorPinSpeed2, potPin2, rlyPin2, motorPinDir2, direct2, speedControl2);
  //direct3 = manualSpeedControl(motorPinSpeed3, potPin3, rlyPin3, motorPinDir3, direct3, speedControl3);
  
  if (millis() - send_time >= send_delay) {
    send_time = millis();
    send_status();
  }
}

void read_status() {
  stat.pitch_pos = analogRead(potPin1);
  stat.yaw_pos = analogRead(potPin2);
  stat.lid_pos = analogRead(potPin3);  
}

void read_command() {
  String  message = inputString; // holds text not yet split
  int     delimPosition;  // the position of the next delim in the string
  inputString = "";
  stringComplete = false;
  int i = 0;
  do
  {
      String value;
      delimPosition = message.indexOf(',');
      if(delimPosition != -1)
      {
          value = message.substring(0,delimPosition);
          message = message.substring(delimPosition+1, message.length());
      }
      else
      {  // here after the last comma is found
         if(message.length() > 0)
           value = message;  // if there is text after the last comma
      }
      switch (i) {
        case 0:
          cmd.yaw_pwm = value.toInt();
          break;
        case 1:
          cmd.yaw_direction = (value == "1" ? HIGH : LOW);
          break;
        case 2:
          cmd.yaw_brake = (value == "1" ? HIGH : LOW);
          break;
        case 3:
          cmd.pitch_pwm = value.toInt();
          break;
        case 4:
          cmd.pitch_direction = (value == "1" ? HIGH : LOW);
          break;
        case 5:
          cmd.pitch_brake = (value == "1" ? HIGH : LOW);
          break;
        case 6:
          cmd.lid_pwm = value.toInt();
          break;
        case 7:
          cmd.lid_direction = (value == "1" ? HIGH : LOW);
          break;
        case 8:
          cmd.lid_brake = (value == "1" ? HIGH : LOW);
          break;
        default:
          break;
      }
      i++;
   }
   while(delimPosition >=0);
}

#ifdef DEBUG
// Debug: Show current commands on lcd
void lcd_command() {
   lcd.clear();
   lcd.setCursor(0,0);
   lcd.print(
           "Y"+String(cmd.yaw_pwm)+" "+String(cmd.yaw_direction)
           +" L"+String(cmd.lid_pwm)+" "+String(cmd.lid_direction)
           );
} 
#endif

// Send command to the motors
void do_command() {
  analogWrite(motorPinSpeed1, cmd.pitch_pwm);
  digitalWrite(motorPinDir1, cmd.pitch_direction);
  analogWrite(motorPinSpeed2, cmd.yaw_pwm);
  digitalWrite(motorPinDir2, cmd.yaw_direction);
  analogWrite(motorPinSpeed3, cmd.lid_pwm);
  digitalWrite(motorPinDir3, cmd.lid_direction);

  // Brakes
  digitalWrite(rlyPin2, cmd.yaw_brake);
  digitalWrite(rlyPin1, cmd.pitch_brake);
  digitalWrite(rlyPin3, cmd.lid_brake);
}

void send_status() {
  statusString = "";
  statusString += String(stat.yaw_pos);
  statusString += "," + String(stat.pitch_pos);
  statusString += "," + String(stat.lid_pos);
  Serial.println(statusString);
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
#ifdef DEBUG
    lcd.clear();
    lcd.setCursor(0,0);
    lcd.print(inChar);
#endif

    // add it to the inputString:
    inputString += inChar;
    // if the incoming character is a newline, set a flag
    // so the main loop can do something about it:
    if (inChar == '\n') {
      stringComplete = true;
    } 
  }

#ifdef DEBUG
  lcd.clear();
  lcd.setCursor(0,0);
  lcd.print(inputString);
#endif
}

int battVolt() {
  int val = analogRead(batteryPin); // read the value from the sensor
  float volts = (10 * val * referenceVolts/1023.0) + 1.2 ; // calculate the ratio. add on the voltage drop due to the diode.
  return volts;
  }

void lowBattCheck(){
  unsigned long currentMillis = millis();
  if(currentMillis - previousBattCheck > 10000) {
    int battReading = battVolt();
    switch (battReading) {
      case  18: overBattStatus();                   break;
      case  17: overBattStatus();                   break;
      case  16: overBattStatus();                   break;
      case  15: overBattStatus();                   break;
      case  14: normBattStatus();                   break;
      case  13: normBattStatus();                   break;
      case  12: normBattStatus();                   break;
      case  11: underBattStatus();                  break;
      case  10: underBattStatus();                  break;
      case   9: underBattStatus();                  break;
      case   8: underBattStatus();                  break;
      case   7: underBattStatus();                  break;
      case   6: underBattStatus();                  break;
      default: break;
    }
  }
}

void overBattStatus() {
  //
  digitalWrite(lowBattLED, HIGH);
  lowBattCon = 1;
}

void normBattStatus() {
//
   digitalWrite(lowBattLED, LOW);
  lowBattCon = 0;
}

void underBattStatus() {
//
   digitalWrite(lowBattLED, HIGH);
   lowBattCon = 1;
}
