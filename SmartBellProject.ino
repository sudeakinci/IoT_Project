#include "arduino_secrets.h"
#include "thingProperties.h"
#include <ESPAsyncWebServer.h>

const int thumbLedPin = 27;
const int indexLedPin = 26;
const int middleLedPin = 25;
const int buzzerPin = 33;

const int trigPin = 5;
const int echoPin = 18;

const char* ssid = "FiberHGW_TP22B4_2.4GHz";
const char* password = "LzX4deWP";

AsyncWebServer server(80);

void setup() {
  Serial.begin(115200);
  delay(1500);

  // connect to wi-fi
  WiFi.begin(ssid, password);
  Serial.println("Connecting to WiFi...");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  Serial.print("Connected. IP: ");
  Serial.println(WiFi.localIP());

  // synchron time (connected to wi-fi)
  configTime(0, 0, "pool.ntp.org", "time.nist.gov");

  struct tm timeinfo;
  if (!getLocalTime(&timeinfo)) {
    Serial.println("Zaman alınamadı!");
  } else {
    Serial.println("Zaman senkronize edildi:");
    Serial.println(&timeinfo, "%A, %B %d %Y %H:%M:%S");
  }


  pinMode(thumbLedPin, OUTPUT);
  pinMode(indexLedPin, OUTPUT);
  pinMode(middleLedPin, OUTPUT);
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);

  digitalWrite(thumbLedPin, LOW);
  digitalWrite(indexLedPin, LOW);
  digitalWrite(middleLedPin, LOW);
  
  pinMode(buzzerPin, OUTPUT);
  digitalWrite(buzzerPin, LOW);


  // Arduino IoT Cloud başlat
  initProperties();
  ArduinoCloud.begin(ArduinoIoTPreferredConnection);
  setDebugMessageLevel(2);
  ArduinoCloud.printDebugInfo();

  // Web sunucu tanımları
  server.on("/led/thumb/on", HTTP_GET, [](AsyncWebServerRequest *request){
    digitalWrite(thumbLedPin, HIGH);
    request->send(200, "text/plain", "Thumb ON");
  });

  server.on("/led/thumb/off", HTTP_GET, [](AsyncWebServerRequest *request){
    digitalWrite(thumbLedPin, LOW);
    request->send(200, "text/plain", "Thumb OFF");
  });

  server.on("/led/index/on", HTTP_GET, [](AsyncWebServerRequest *request){
    digitalWrite(indexLedPin, HIGH);
    request->send(200, "text/plain", "Index ON");
  });

  server.on("/led/index/off", HTTP_GET, [](AsyncWebServerRequest *request){
    digitalWrite(indexLedPin, LOW);
    request->send(200, "text/plain", "Index OFF");
  });

  server.on("/led/middle/on", HTTP_GET, [](AsyncWebServerRequest *request){
    digitalWrite(middleLedPin, HIGH);
    request->send(200, "text/plain", "Middle ON");
  });

  server.on("/led/middle/off", HTTP_GET, [](AsyncWebServerRequest *request){
    digitalWrite(middleLedPin, LOW);
    request->send(200, "text/plain", "Middle OFF");
  });

  server.on("/distance", HTTP_GET, [](AsyncWebServerRequest *request){
    long duration, distance;
    digitalWrite(trigPin, LOW);
    delayMicroseconds(2);
    digitalWrite(trigPin, HIGH);
    delayMicroseconds(10);
    digitalWrite(trigPin, LOW);

    duration = pulseIn(echoPin, HIGH, 30000);
    if (duration == 0) {
      request->send(200, "text/plain", "999");
      return;
    }

    distance = duration * 0.034 / 2;
    if (distance > 400) {
      request->send(200, "text/plain", "999");
      return;
    }

    request->send(200, "text/plain", String(distance));
  });

  server.on("/buzzer/on", HTTP_GET, [](AsyncWebServerRequest *request){
    digitalWrite(buzzerPin, HIGH); 
    request->send(200, "text/plain", "Buzzer On");
});

server.on("/buzzer/off", HTTP_GET, [](AsyncWebServerRequest *request){
    digitalWrite(buzzerPin, LOW);  
    request->send(200, "text/plain", "Buzzer Off");
});

  server.begin();
}

void loop() {
  ArduinoCloud.update();

}


// Bulut değişkenleri değiştiğinde çağrılan fonksiyonlar
void onUser1AccessChange() {
  digitalWrite(thumbLedPin, user1Access ? HIGH : LOW);
  if (user1Access) {
    user1EntryCount++;
    // buzzOnce
  }
}

void onUser2AccessChange() {
  digitalWrite(indexLedPin, user2Access ? HIGH : LOW);
  if (user2Access) {
    user2EntryCount++;
    // buzzOnce
  }
}

void onUser3AccessChange() {
  digitalWrite(middleLedPin, user3Access ? HIGH : LOW);
  if (user3Access) {
    user3EntryCount++;
    // buzzOnce
  }
}

/*
  Since SystemActive is READ_WRITE variable, onSystemActiveChange() is
  executed every time a new value is received from IoT Cloud.
*/
void onSystemActiveChange()  {
  Serial.print("Sistem aktif mi: ");
  Serial.println(systemActive ? "Evet" : "Hayır");
}
/*
  Since User1EntryCount is READ_WRITE variable, onUser1EntryCountChange() is
  executed every time a new value is received from IoT Cloud.
*/
void onUser1EntryCountChange()  {}
/*
  Since User2EntryCount is READ_WRITE variable, onUser2EntryCountChange() is
  executed every time a new value is received from IoT Cloud.
*/
void onUser2EntryCountChange()  {}
/*
  Since User3EntryCount is READ_WRITE variable, onUser3EntryCountChange() is
  executed every time a new value is received from IoT Cloud.
*/
void onUser3EntryCountChange()  {}