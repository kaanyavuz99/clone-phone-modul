#include <Arduino.h>
#include <WiFi.h>

// Specific Board Pins for LILYGO T-SIM7600
#define MODEM_TX 27
#define MODEM_RX 26
#define MODEM_PWRKEY 4
#define MODEM_DTR 32
#define MODEM_RI 33
#define MODEM_FLIGHT 25
#define MODEM_RST 5

// Network Credentials
const char *ap_ssid = "LILYGO-4G-Router";
const char *ap_pass = "12345678";

// Log
#define SerialMon Serial
#define SerialAT Serial1

// LwIP & NAT
// #include "lwip/err.h"
// #include "lwip/ip_addr.h"
// #include "lwip/napt.h"

// LED Pin (Commonly GPIO 12 on LILYGO T-SIM series)
#define LED_PIN 12

void setup() {
  SerialMon.begin(115200);
  delay(1000);
  SerialMon.println("Starting LILYGO Router (Pure Arduino Mode)...");

  // 0. Setup LED
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, HIGH); // Turn on initially

  // 1. Initialize Modem Pins
  pinMode(MODEM_PWRKEY, OUTPUT);
  digitalWrite(MODEM_PWRKEY, LOW);
  pinMode(MODEM_FLIGHT, OUTPUT);
  digitalWrite(MODEM_FLIGHT, HIGH);
  pinMode(MODEM_RST, OUTPUT);
  digitalWrite(MODEM_RST, HIGH);

  // 2. Power On Sequence (Extended to 1s for reliability)
  SerialMon.println("Powering on modem (1s pulse)...");
  digitalWrite(MODEM_PWRKEY, HIGH);
  delay(1000); // Increased from 300ms to 1000ms
  digitalWrite(MODEM_PWRKEY, LOW);

  // 3. Initialize Serial1 for Modem
  SerialAT.begin(115200, SERIAL_8N1, MODEM_RX, MODEM_TX);

  // 4. Setup Wi-Fi SoftAP
  SerialMon.println("Starting Wi-Fi SoftAP...");
  WiFi.softAP(ap_ssid, ap_pass);
  IPAddress myIP = WiFi.softAPIP();
  SerialMon.print("AP IP address: ");
  SerialMon.println(myIP);

  // 5. Enable NAT (Disabled for now)
  // u32_t nat_ip = IPADDR4_INIT_BYTES(myIP[0], myIP[1], myIP[2], myIP[3]);
  // ip_napt_enable(nat_ip, 1);
  // SerialMon.println("NAT Enabled on SoftAP Subnet");

  SerialMon.println("--- Entering Passthrough Mode ---");
  SerialMon.println("You can now type AT commands here.");
}

void loop() {
  // Heartbeat LED (Blink every 1 second)
  static uint32_t lastBlink = 0;
  if (millis() - lastBlink > 1000) {
    lastBlink = millis();
    digitalWrite(LED_PIN, !digitalRead(LED_PIN));

    // Print verify message every 5 seconds
    if (millis() % 5000 < 100) {
      SerialMon.printf("ESP32 Alive! System Uptime: %lu s\n", millis() / 1000);
    }
  }

  // Simple Serial Bridge
  if (SerialAT.available()) {
    SerialMon.write(SerialAT.read());
  }
  if (SerialMon.available()) {
    SerialAT.write(SerialMon.read());
  }
}
