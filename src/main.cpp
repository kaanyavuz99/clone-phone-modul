#include <Arduino.h>

// Pin Definitions (Passed from platformio.ini)
#define RX_PIN MODEM_RX
#define TX_PIN MODEM_TX
#define PWR_PIN MODEM_PWRKEY

void setup() {
    // 1. Initialize USB Serial for Logs
    Serial.begin(115200);
    while (!Serial);
    Serial.println("\n--- T-SIM7600E connectivity test start ---");
    
    // 2. Initialize Modem Serial
    Serial1.begin(115200, SERIAL_8N1, RX_PIN, TX_PIN);
    
    // 3. Power On Sequence
    Serial.println("Powering on modem...");
    pinMode(PWR_PIN, OUTPUT);
    digitalWrite(PWR_PIN, HIGH);
    delay(300); // Pulse
    digitalWrite(PWR_PIN, LOW);
    
    Serial.println("Waiting for modem to boot (10s)...");
    delay(10000); 

    // 4. Basic Test
    Serial.println("Sending AT...");
    Serial1.println("AT");
}

void loop() {
    // Forward Modem -> USB
    if (Serial1.available()) {
        Serial.write(Serial1.read());
    }
    // Forward USB -> Modem (for interactive testing)
    if (Serial.available()) {
        Serial1.write(Serial.read());
    }
}
