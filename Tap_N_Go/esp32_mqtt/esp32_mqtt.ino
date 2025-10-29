#include <WiFi.h>
#include <PubSubClient.h>

// WiFi credentials
const char* ssid = "BPIT-Winnovation";
const char* password = "emerging";

// MQTT broker
const char* mqtt_broker = "192.168.41.145";
const int mqtt_port = 1883;
const char* request_topic = "rfid/request";
const char* response_topic = "rfid/response";

// Clients
WiFiClient espClient;
PubSubClient client(espClient);

void setup() {
  // Serial for debugging & input
  Serial.begin(115200);
  delay(1000); // Prevent watchdog reset

  Serial.println("🔌 Starting...");

  // Connect to WiFi
  WiFi.begin(ssid, password);
  Serial.print("🌐 Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\n✅ WiFi connected");
  Serial.println("IP address: " + WiFi.localIP().toString());

  // MQTT setup
  client.setServer(mqtt_broker, mqtt_port);
  client.setCallback(callback);

  // Connect to MQTT broker
  while (!client.connected()) {
    String client_id = "esp32-client-";
    client_id += String(WiFi.macAddress());
    Serial.printf("🔗 Connecting to MQTT as %s\n", client_id.c_str());
    if (client.connect(client_id.c_str())) {
      Serial.println("✅ MQTT connected");
    } else {
      Serial.print("❌ MQTT connect failed, state: ");
      Serial.println(client.state()); 
      delay(2000);
    }
  }

  // Subscribe to the response topic
  client.subscribe(response_topic);
  Serial.println("📡 Subscribed to: rfid/response");
  Serial.println("📥 Type RFID card number to send:");
}

// MQTT callback function
void callback(char* topic, byte* payload, unsigned int length) {
  String message = "";
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }

  Serial.println("\n📨 Response received:");
  Serial.print("Topic: ");
  Serial.println(topic);
  Serial.print("Payload: ");
  Serial.println(message);
  Serial.println("--------------------------");
}

void loop() {
  client.loop();

  // Check for user input
  if (Serial.available()) {
    String card = Serial.readStringUntil('\n');
    card.trim(); // Remove whitespace     

    if (card.length() > 0) {
      Serial.print("📤 Sending card: ");
      Serial.println(card);
      client.publish(request_topic, card.c_str());
    }
  }
}
