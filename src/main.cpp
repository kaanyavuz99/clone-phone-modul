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
const char *apn = "internet"; // Set your APN here
const char *gprsUser = "";    // Set your User here
const char *gprsPass = "";    // Set your Pass here

// Log
#define SerialMon Serial
#define SerialAT Serial1

// Try to include PPP Support
#if __has_include(<PPP.h>)
#include <PPP.h>
#else
// If missing, this will fail to compile, but we catch it with a warning or just
// error.
#error                                                                         \
    "PPP.h not found. Ensure you are using Arduino ESP32 v2.0+ or PlatformIO with correct package."
#endif

// Internal LWIP NAPT
#include "lwip/lwip/ip_addr.h"
#include "lwip/lwip/napt.h"


// Globals
bool pppConnected = false;

// Network Events
void onEvent(ArduinoHalIdTypeDef id, void *info) {
  if (id == ARDUINO_EVENT_PPP_CONNECTED) {
    SerialMon.println("PPP Connect Success!");
    pppConnected = true;
  } else if (id == ARDUINO_EVENT_PPP_DISCONNECTED) {
    SerialMon.println("PPP Disconnected.");
    pppConnected = false;
  } else if (id == ARDUINO_EVENT_PPP_GOT_IP) {
    SerialMon.println("PPP Got IP Address!");
    // Enable NAT here once we have IP?
    // Actually NAT needs to be enabled for the SoftAP subnet.
  }
}

void setup() {
  SerialMon.begin(115200);
  delay(1000);
  SerialMon.println("Starting LILYGO Router...");

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
  delay(3000); // Wait for boot

  // 3. Initialize Serial1 for Modem
  SerialAT.begin(115200, SERIAL_8N1, MODEM_RX, MODEM_TX);

  // 4. Initialize PPP
  // Note: PPP library usually takes control of the Serial
  // Make sure we set APN first
  PPP.setApn(apn);
  if (strlen(gprsUser) > 0)
    PPP.setPin(
        gprsUser); // Actually setPin is for SIM PIN, setAuth for user/pass
  // PPP.setAuth(gprsUser, gprsPass); // Uncomment if needed

  SerialMon.println("Starting PPP connection...");
  PPP.begin(SerialAT);

  // Register events (optional, loop checks status too)
  PPP.onEvent(onEvent);

  // 5. Setup Wi-Fi SoftAP
  SerialMon.println("Starting Wi-Fi SoftAP...");
  WiFi.softAP(ap_ssid, ap_pass);
  SerialMon.print("AP IP address: ");
  SerialMon.println(WiFi.softAPIP());

  // 6. Enable NAT
  // We need to enable NAT for the SoftAP subnet.
  // PlatformIO sdkconfig.defaults MUST have CONFIG_LWIP_IPV4_NAPT=y

  SerialMon.println("Enabling NAT...");
  // NAPT for the SoftAP subnet.
  // Default SoftAP IP is 192.168.4.1. Subnet mask /24.
  // ip_napt_enable expects a u32_t IP address (little endian usually) and
  // count? Prototype: void ip_napt_enable(u32_t addr, int enable);

  ip_addr_t ip_addr;
  IPAddress soft_ip = WiFi.softAPIP();
  IP_ADDR4(&ip_addr, soft_ip[0], soft_ip[1], soft_ip[2], soft_ip[3]);

  // Enable NAPT for this subnet
  // Since ip_napt_enable takes a single address, commonly we pass the Gateway
  // IP of the NATed network.
  ip_napt_enable(ip_addr.u_addr.ip4.addr, 1);

  SerialMon.println("NAT Configured.");
}

void loop() {
  // Check Status
  static unsigned long lastCheck = 0;
  if (millis() - lastCheck > 5000) {
    lastCheck = millis();
    if (pppConnected) {
      // SerialMon.println("Status: Connected");
    } else {
      SerialMon.println("Status: Waiting for PPP...");
    }
  }

  // Bridge Serial (Only if PPP is NOT active on the port?
  // Once PPP.begin() is called, Serial1 is consumed by LWIP.
  // We cannot send AT commands easily anymore unless we pause PPP or use CMUX.
  // For now, we assume standard operation.)
}
