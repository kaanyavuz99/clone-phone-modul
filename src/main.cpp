#include "esp_netif.h"
#include "esp_netif_ppp.h"
#include "lwip/dns.h"
#include "lwip/err.h"
#include "lwip/ip_addr.h"
#include "lwip/netif.h"
#include "netif/ppp/ppp.h"
#include "netif/ppp/pppos.h"
#include <Arduino.h>
#include <WiFi.h>

// --- Configuration ---
const char *ap_ssid = "LILYGO-4G-Router-Pro";
const char *ap_pass = "12345678";
#define UART_BAUD_RATE 460800 // High speed for LTE
#define MODEM_TX 27
#define MODEM_RX 26
#define MODEM_PWRKEY 4
#define MODEM_RST 5
#define LED_PIN 12

// --- LwIP & NAPT Headers ---
#include "lwip/dns.h"
#include "lwip/err.h"

// Forward Declaration for NAPT (Bypasses missing header in Arduino context)
#if !defined(ip_napt_enable)
extern "C" {
void ip_napt_enable(uint32_t addr, int enable);
}
#endif

// --- Global Objects ---
ppp_pcb *ppp = NULL;
struct netif ppp_netif;
bool ppp_connected = false;

// --- Forward Declarations ---
void modemInit();
u32_t ppp_output_callback(ppp_pcb *pcb, u8_t *data, u32_t len, void *ctx);
void ppp_status_cb(ppp_pcb *pcb, int err_code, void *ctx);

// --- Setup ---
void setup() {
  Serial.begin(115200); // Debug Console
  Serial1.begin(UART_BAUD_RATE, SERIAL_8N1, MODEM_RX, MODEM_TX); // Modem Port

  Serial.println("\n--- LILYGO T-SIM7600 NAT ROUTER STARTING ---");

  // 1. LED & Power
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, HIGH);

  // 2. Modem Hardware Init
  modemInit();

  // 3. Start Wi-Fi SoftAP
  Serial.println("Starting Wi-Fi SoftAP...");
  WiFi.softAP(ap_ssid, ap_pass);
  IPAddress myIP = WiFi.softAPIP();
  Serial.print("AP IP Address: ");
  Serial.println(myIP);

  // 4. Initialize PPPoS (Point-to-Point Protocol over Serial)
  Serial.println("Initializing PPPoS Stack...");

  // Create PPP interface
  ppp = pppos_create(&ppp_netif, ppp_output_callback, ppp_status_cb, NULL);
  if (!ppp) {
    Serial.println("Error: Could not create PPP interface!");
    return;
  }

  // Set interface as default
  ppp_set_default(ppp);

  // 5. Connect Phase
  Serial.println("Dialing Provider (ATD*99#)...");
  Serial1.println("ATD*99#"); // Dial Command

  // Connect PPP
  ppp_connect(ppp, 0);

  Serial.println("PPPoS Started. Waiting for IP...");
}

// --- Main Loop ---
void loop() {
  // Feed Serial Data to LwIP (The Bridge)
  while (Serial1.available()) {
    uint8_t buffer[128];
    int len = Serial1.readBytes(buffer, sizeof(buffer));
    if (len > 0 && ppp != NULL) {
      pppos_input(ppp, buffer, len);
    }
  }

  // Heartbeat
  static uint32_t lastTick = 0;
  if (millis() - lastTick > 1000) {
    lastTick = millis();
    digitalWrite(LED_PIN, !digitalRead(LED_PIN)); // Blink
    if (ppp_connected) {
      // Optional: Print status
    }
  }
}

// --- Callbacks ---

// Output Callback: LwIP wants to send data to Modem
u32_t ppp_output_callback(ppp_pcb *pcb, u8_t *data, u32_t len, void *ctx) {
  return Serial1.write(data, len);
}

// Status Callback: Connection State Changes
void ppp_status_cb(ppp_pcb *pcb, int err_code, void *ctx) {
  struct netif *pppif = ppp_netif(pcb);

  switch (err_code) {
  case PPPERR_NONE: {
    Serial.println("PPP: Connected!");
    Serial.print("   IP: ");
    Serial.println(ip4addr_ntoa(netif_ip4_addr(pppif)));
    Serial.print("   GW: ");
    Serial.println(ip4addr_ntoa(netif_ip4_gw(pppif)));
    Serial.print("   MS: ");
    Serial.println(ip4addr_ntoa(netif_ip4_netmask(pppif)));

    // --- CRITICAL: ENABLE NAT HERE ---
    // NAPT allows Wi-Fi clients (192.168.4.x) to masquerade as PPP IP
    ip_napt_enable(pppif->ip_addr.u_addr.ip4.addr, 1);
    Serial.println(">> NAT ENABLED (Architecture: PPPoS -> SoftAP) <<");

    ppp_connected = true;
    break;
  }
  default: {
    Serial.print("PPP: Disconnected/Error: ");
    Serial.println(err_code);
    ppp_connected = false;
    break;
  }
  }
}

// --- Utilities ---
void modemInit() {
  Serial.println("Resetting Modem...");
  pinMode(MODEM_PWRKEY, OUTPUT);
  digitalWrite(MODEM_PWRKEY, LOW);
  delay(100);
  digitalWrite(MODEM_PWRKEY,
               HIGH); // Power Key is usually Active Low or High pulse,
                      // T-SIM7600 is Active HIGH pulse for ON
  delay(1000);        // 1s Pulse
  digitalWrite(MODEM_PWRKEY, LOW);

  Serial.println("Waiting for Modem Boot (5s)...");
  delay(5000);

  // Send AT Sync
  Serial1.println("AT");
  delay(100);
  Serial1.println("AT+CMEE=2"); // Verbose errors
  delay(100);
  // User Report says: flow control might be needed for high speeds,
  // but we start simple.
}
