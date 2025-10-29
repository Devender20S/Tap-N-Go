#include <ArduinoJson.h>
#define allow 3
#define deny 2
#define buzzer 5
// #include <ArduinoJson.h>
void setup() {
  Serial.begin(9600);
  pinMode(allow, OUTPUT);
  pinMode(buzzer, OUTPUT);
  pinMode(deny, OUTPUT);
}

void loop() {
  if(Serial.available() > 0){
    String serial_data = Serial.readString();
    Serial.print(serial_data);
    StaticJsonDocument<200> doc;

  // Deserialize the JSON string
    DeserializationError error = deserializeJson(doc, serial_data);//serializer and deserialiizer are ibuilt function
    const char* convert_data = doc["status"];
    Serial.print("   Status: ");
    Serial.println(convert_data);
    Serial.print("   Status: ");
    Serial.println(convert_data);
    String data = String(convert_data);
    delay(500);

    if(data == "ok"){
      digitalWrite(allow, HIGH);
      digitalWrite(buzzer, HIGH);
      Serial.println("led on");
      delay(2000);
      digitalWrite(allow, LOW);
      digitalWrite(buzzer, LOW);
      Serial.println("led oFF");

    }
    else if(data == "not"){
      digitalWrite(deny, HIGH);
      digitalWrite(buzzer, HIGH);
      Serial.println("led not on");
      delay(2000);
      digitalWrite(deny, LOW);
      digitalWrite(buzzer, LOW);
      Serial.println("led not oFF");
    }
    else{

    }

  }
  

}
