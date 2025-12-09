#include <Arduino.h>

// Pin Definitions
#define RX_PIN 26
#define TX_PIN 27
#define PWR_PIN 4

void setup() {
  Serial
      .begin(115200) // ERROR: Missing semicolon here!
      Serial1.begin(115200, SERIAL_8N1, RX_PIN, TX_PIN);

  pinMode(PWR_PIN, OUTPUT);
  digitalWrite(PWR_PIN, HIGH);
  delay(300);
  digitalWrite(PWR_PIN, LOW);

  Serial.println("\n--- Live Monitor Test ---");
  Serial.println("I will send a message every 2 seconds.");
}

void loop() {
  // 1. Heartbeat - Shows the agent is "watching"
  static unsigned long lastPrint = 0;
  if (millis() - lastPrint > 2000) {
    lastPrint = millis();
    Serial.print("[Heartbeat] System Uptime: ");
    Serial.print(millis() / 1000);
    Serial.println(" seconds");
  }

  // 2. Passthrough - Allows seeing modem response
  if (Serial1.available())
    Serial.write(Serial1.read());
  if (Serial.available())
    Serial1.write(Serial.read());
}
