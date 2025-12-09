#include "esp_wifi.h"
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

// LwIP & NAT (ESP-IDF Native)
#include "lwip/err.h"
#include "lwip/ip_addr.h"
#include "lwip/napt.h"

// #include "esp_netif.h" // We will use this for PPP later

void setup() {
  SerialMon.begin(115200);
  delay(1000);
  SerialMon.println("Starting LILYGO Router V2...");

  // 1. Initialize Modem Pins
  pinMode(MODEM_PWRKEY, OUTPUT);
  digitalWrite(MODEM_PWRKEY, LOW);
  pinMode(MODEM_FLIGHT, OUTPUT);
  digitalWrite(MODEM_FLIGHT, HIGH);
  pinMode(MODEM_RST, OUTPUT);
  digitalWrite(MODEM_RST, HIGH);

  // 2. Power On Sequence
  SerialMon.println("Powering on modem...");
  digitalWrite(MODEM_PWRKEY, HIGH);
  delay(300);
  digitalWrite(MODEM_PWRKEY, LOW);

  // 3. Initialize Serial1 for Modem
  SerialAT.begin(115200, SERIAL_8N1, MODEM_RX, MODEM_TX);

  // 4. Setup Wi-Fi SoftAP
  SerialMon.println("Starting Wi-Fi SoftAP...");
  WiFi.softAP(ap_ssid, ap_pass);
  IPAddress myIP = WiFi.softAPIP();
  SerialMon.print("AP IP address: ");
  SerialMon.println(myIP);

  // 5. Enable NAT (Preliminary Check)
  // Just to verify if the symbols are linked correctly
  u32_t nat_ip = IPADDR4_INIT_BYTES(myIP[0], myIP[1], myIP[2], myIP[3]);
  ip_napt_enable(nat_ip, 1);
  SerialMon.println("NAT Enabled on SoftAP Subnet (Waiting for WAN...)");

  SerialMon.println("--- Entering Passthrough Mode ---");
  SerialMon.println("You can now type AT commands here.");
}

void loop() {
  // Simple Serial Bridge
  if (SerialAT.available()) {
    SerialMon.write(SerialAT.read());
  }
  if (SerialMon.available()) {
    SerialAT.write(SerialMon.read());
  }
}
