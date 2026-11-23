/*
  Renewable Energy Availability Prediction
  ESP32 + 2 x INA219 + BH1750 + DS18B20 + analog FSR

  INA219 #1 (0x40): PV panel output, before solar charge controller
  INA219 #2 (0x41): bidirectional battery system-bus current monitor
  BH1750: I2C 0x23
  DS18B20: GPIO4, 4.7k pull-up to 3V3
  FSR (if analog 2-wire type): 3V3 -> FSR -> GPIO34 -> 10k -> GND
  Optional conditioned piezo voltage monitor: GPIO35 through divider,
  ONLY after confirming the conditioned output never exceeds 15V DC.

  Battery: 3S Li-ion = 11.1V nominal, normally 12.6V full charge.
  Use a compatible 3S CC/CV charger and correctly wired 3S BMS.
  BMS is not a charger. Confirm the exact battery/BMS datasheets.

  SOC below is a rough voltage indicator only, not a real BMS SOC.
*/

#define BLYNK_TEMPLATE_ID   "YOUR_TEMPLATE_ID"
#define BLYNK_TEMPLATE_NAME "Renewable Energy Availability"
#define BLYNK_AUTH_TOKEN    "YOUR_DEVICE_AUTH_TOKEN"

#include <WiFi.h>
#include <BlynkSimpleEsp32.h>
#include <Wire.h>
#include <Adafruit_INA219.h>
#include <BH1750.h>
#include <OneWire.h>
#include <DallasTemperature.h>

char ssid[] = "YOUR_WIFI_NAME";
char pass[] = "YOUR_WIFI_PASSWORD";

static const int SDA_PIN = 21;
static const int SCL_PIN = 22;
static const int DS18B20_PIN = 4;
static const int FSR_PIN = 34;
static const int PIEZO_ADC_PIN = 35;

// INA219 address straps must be configured so the modules are unique.
Adafruit_INA219 inaPV(0x40);
Adafruit_INA219 inaBattery(0x41);
BH1750 lightMeter;
OneWire oneWire(DS18B20_PIN);
DallasTemperature tempSensor(&oneWire);
BlynkTimer timer;

bool pvSensorOK = false;
bool batterySensorOK = false;
bool lightSensorOK = false;
bool tempSensorOK = false;

// Voltage-only estimate; adjust only after battery-maker guidance/testing.
// Do not use this estimate for charging/discharging protection.
const float SOC_EMPTY_V = 9.6;   // example 3S pack lower display point, not cutoff setting
const float SOC_FULL_V  = 12.6;  // typical 3S Li-ion full voltage
const float FORCE_THRESHOLD = 900.0;

// Optional piezo divider: R_TOP=100k from conditioned output to ADC,
// R_BOTTOM=27k from ADC to GND. This only applies when conditioned DC
// output is guaranteed <=15V and has no damaging transients.
// Keep false until the output has been measured and verified.
const bool ENABLE_PIEZO_VOLTAGE_ADC = false;
const float PIEZO_DIVIDER_RATIO = (100.0 + 27.0) / 27.0;

float pvVoltage=0, pvCurrent=0, pvPower=0;
float busVoltage=0, batteryCurrent=0, batteryPower=0, socEstimate=0;
float luxValue=0, tempC=0, piezoVoltage=0;
int forceRaw=0, footstepActivity=0;
float pvEnergyWh=0;
unsigned long lastEnergyMs=0;

float clampValue(float x, float lo, float hi) {
  return (x < lo) ? lo : ((x > hi) ? hi : x);
}

float estimateSocFromVoltage(float v) {
  // Only a rough display indicator. Li-ion voltage/SOC is load-, rest-,
  // temperature- and chemistry-dependent.
  return clampValue((v - SOC_EMPTY_V) * 100.0 / (SOC_FULL_V - SOC_EMPTY_V), 0, 100);
}

void readSensors() {
  if (pvSensorOK) {
    // Bus voltage is measured at INA219 VIN-; add shunt drop for source-side voltage.
    pvVoltage = inaPV.getBusVoltage_V() + inaPV.getShuntVoltage_mV()/1000.0;
    pvCurrent = inaPV.getCurrent_mA()/1000.0;
    pvPower = pvVoltage * pvCurrent;
  }

  if (batterySensorOK) {
    // INA219 #2 is in series between BMS P+ and system positive bus.
    // Positive current is expected during battery discharge with wiring below;
    // charging current should have the opposite sign. Verify on the bench.
    busVoltage = inaBattery.getBusVoltage_V();
    batteryCurrent = inaBattery.getCurrent_mA()/1000.0;
    batteryPower = busVoltage * batteryCurrent;
    socEstimate = estimateSocFromVoltage(busVoltage);
  }

  if (lightSensorOK) {
    float l = lightMeter.readLightLevel();
    if (l >= 0) luxValue = l;
  }

  if (tempSensorOK) {
    tempSensor.requestTemperatures();
    float t = tempSensor.getTempCByIndex(0);
    if (t > -55 && t < 125) tempC = t;
  }

  forceRaw = analogRead(FSR_PIN);
  footstepActivity = (forceRaw > FORCE_THRESHOLD) ? 1 : 0;

  if (ENABLE_PIEZO_VOLTAGE_ADC) {
    // This is voltage only, not piezo current or power.
    // GPIO35 voltage is reconstructed from the external resistor divider.
    float adcV = (analogRead(PIEZO_ADC_PIN) / 4095.0) * 3.3;
    piezoVoltage = adcV * PIEZO_DIVIDER_RATIO;
  }

  unsigned long now = millis();
  if (lastEnergyMs != 0) {
    float dtHours = (now - lastEnergyMs) / 3600000.0;
    // Integrate PV power only. Piezo energy is not included because no
    // piezo current sensor is installed. Battery energy is not generation.
    pvEnergyWh += max(0.0f, pvPower) * dtHours;
  }
  lastEnergyMs = now;
}

void publishBlynk() {
  readSensors();

  if (pvSensorOK) {
    Blynk.virtualWrite(V0, pvVoltage);
    Blynk.virtualWrite(V1, pvCurrent);
    Blynk.virtualWrite(V2, pvPower);
  }

  if (ENABLE_PIEZO_VOLTAGE_ADC) {
    Blynk.virtualWrite(V3, piezoVoltage);
  }

  if (batterySensorOK) {
    Blynk.virtualWrite(V6, busVoltage);
    Blynk.virtualWrite(V7, batteryCurrent);
    Blynk.virtualWrite(V8, socEstimate);
    Blynk.virtualWrite(V10, batteryPower);
  }

  Blynk.virtualWrite(V9, pvEnergyWh);
  if (lightSensorOK) Blynk.virtualWrite(V11, luxValue);
  if (tempSensorOK) Blynk.virtualWrite(V12, tempC);
  Blynk.virtualWrite(V13, forceRaw);
  Blynk.virtualWrite(V14, footstepActivity);
  Blynk.virtualWrite(V15, WiFi.RSSI());
}

void printStatus() {
  Serial.println("\n--- Renewable Energy Monitor ---");
  Serial.printf("INA219 PV: %s | INA219 Battery: %s\n",
                pvSensorOK ? "OK" : "NOT FOUND",
                batterySensorOK ? "OK" : "NOT FOUND");
  Serial.printf("BH1750: %s | DS18B20: %s\n",
                lightSensorOK ? "OK" : "NOT FOUND",
                tempSensorOK ? "OK" : "NOT FOUND");
  Serial.printf("PV: %.2f V, %.3f A, %.2f W\n", pvVoltage, pvCurrent, pvPower);
  Serial.printf("Battery bus: %.2f V, current: %.3f A, power: %.2f W\n",
                busVoltage, batteryCurrent, batteryPower);
  Serial.printf("SOC estimate (display only): %.1f %% | PV energy: %.4f Wh\n",
                socEstimate, pvEnergyWh);
  Serial.printf("Light: %.1f lx | Temp: %.2f C | Force ADC: %d | Activity: %d\n",
                luxValue, tempC, forceRaw, footstepActivity);
}

void setup() {
  Serial.begin(115200);
  analogReadResolution(12);
  analogSetPinAttenuation(FSR_PIN, ADC_11db);
  analogSetPinAttenuation(PIEZO_ADC_PIN, ADC_11db);

  Wire.begin(SDA_PIN, SCL_PIN);

  pvSensorOK = inaPV.begin();
  batterySensorOK = inaBattery.begin();
  lightSensorOK = lightMeter.begin(BH1750::CONTINUOUS_HIGH_RES_MODE);

  tempSensor.begin();
  tempSensorOK = (tempSensor.getDeviceCount() > 0);

  Serial.println("Sensor startup complete.");
  printStatus();

  Blynk.begin(BLYNK_AUTH_TOKEN, ssid, pass);
  lastEnergyMs = millis();
  timer.setInterval(2000L, publishBlynk);
  timer.setInterval(10000L, [](){ readSensors(); printStatus(); });
}

void loop() {
  Blynk.run();
  timer.run();
}
