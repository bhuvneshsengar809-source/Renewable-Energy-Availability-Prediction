# SAFE WIRING GUIDE — ESP32 / 2 x INA219 / 3S Li-ion

## First: battery safety
- A conventional 3S Li-ion pack is 11.1 V nominal and typically 12.6 V at full charge (4.2 V/cell). Confirm the pack label and cell chemistry.
- Use a 3S CC/CV charger specifically intended for that pack and current rating.
- Confirm BMS model, cell tap order, balance wiring, discharge/charge current rating, and whether it uses common-port or separate charge/discharge ports.
- Do not guess BMS B-, B1, B2, B+ wiring. Do not connect charger directly to cell taps.
- BMS is not a substitute for a proper charger. Add correctly rated fuses and insulated wiring.
- If the battery pack is not a professionally assembled/protected pack, have the BMS wiring checked by a qualified person before connecting it.

## A. Low-voltage logic connections (ESP32 powered from USB during initial testing)
ESP32 GPIO21 (SDA) -> INA219 #1 SDA, INA219 #2 SDA, BH1750 SDA
ESP32 GPIO22 (SCL) -> INA219 #1 SCL, INA219 #2 SCL, BH1750 SCL
ESP32 3V3 -> INA219 #1 VCC, INA219 #2 VCC, BH1750 VCC, DS18B20 VDD, FSR top
ESP32 GND -> sensor GNDs and analog divider ground
Use 3.3V logic. Check the breakout board accepts 3.3V logic and avoid multiple conflicting I2C pull-up rails.

INA219 addresses:
- Module #1 must be 0x40 (default address on many boards).
- Module #2 must be changed to 0x41 using its A0/A1 address jumper/pad as supported by that exact breakout.
- Verify addresses with an I2C scanner before connecting power paths.

DS18B20:
- VDD -> 3V3
- GND -> GND
- DQ/DATA -> GPIO4
- 4.7 kOhm from DATA to 3V3 (omit only if the module already has a pull-up fitted).

FSR (only if it is a two-terminal analog force-sensitive resistor):
- 3V3 -> one FSR terminal
- other FSR terminal -> GPIO34
- 10 kOhm resistor from GPIO34 -> GND
- The GPIO34 node must remain 0–3.3V.
If your "force sensor" is a 3-pin module, use its AO output and module wiring diagram; do not assume this 2-wire FSR circuit.

## B. INA219 #1 — PV measurement
Panel positive -> correctly rated fuse -> INA219 VIN+
INA219 VIN- -> solar charge controller PV+
Panel negative -> solar charge controller PV-
INA219 VCC/GND/SDA/SCL -> ESP32 logic connections above.

This places the shunt in series with PV positive. Confirm panel open-circuit voltage is below the INA219 module's 26 V bus limit, and confirm module shunt/current rating exceeds the panel's worst-case current. A 30 W panel's label Isc and Voc must be checked. If the board rating is unknown, do not put it in the power path; use a correctly rated external shunt/current monitor instead.

## C. INA219 #2 — battery bidirectional current measurement
This is a high-side monitor on the protected BMS output, not on individual cell taps:
BMS P+ -> fuse -> INA219 VIN+
INA219 VIN- -> system positive bus
System positive bus -> protected load positive
System positive bus -> compatible 3S charger positive
BMS P- -> system negative bus
System negative bus -> protected load negative and charger negative

This arrangement measures net current flowing between battery and the common system bus. Verify current sign with a small known load and then with the charger disconnected. Charging should show the opposite sign to discharging (depending on breakout orientation/library convention).
IMPORTANT: Some BMS boards have separate C-/P- ports. The above assumes a common-port BMS with P+ and P-. If yours is separate-port, wiring must follow its exact manual; do not use this generic connection.

INA219 VIN+ / VIN- are the high-current shunt terminals. Do not route battery current through thin Dupont wires or breadboard tracks. Use appropriately rated conductors, terminals and fuses. Confirm the INA219 breakout shunt rating; many inexpensive modules are not suitable for high battery currents.

## D. Piezo measurement
Do not connect raw piezo discs to ESP32 or INA219. Raw piezo can produce high-voltage transients and is high impedance.
First use a suitable bridge rectifier, capacitor rated for expected peak voltage, and a current-limited/regulated DC-DC stage. Keep the piezo path electrically separate until its voltage/current and charging topology are verified.
The supplied firmware leaves piezo ADC disabled by default. It only supports optional voltage monitoring after a conditioned output is verified to stay <=15 V DC:
- conditioned output positive -> 100 kOhm resistor -> GPIO35 node
- GPIO35 node -> 27 kOhm resistor -> GND
- conditioned output negative -> ESP32 GND (only if the DC-DC output is non-isolated and its grounding scheme permits this)
- 100 nF capacitor from GPIO35 node to GND is recommended for ADC noise filtering.
This divider gives approximately 2.69 V at 12.6 V input. Do not enable the code until the maximum output and transient behavior have been measured. It measures voltage only, not piezo current or power. If the DC-DC output is isolated, do not bond its negative to ESP32 ground without reviewing the isolation design.

## E. Solar/piezo charging topology
Do not parallel raw PV and piezo sources. Each needs its own conditioning and reverse-current protection. Use a charge controller/power-path design explicitly compatible with the source arrangement and 3S Li-ion battery. Do not connect a generic 12 V lead-acid solar controller to a 3S Li-ion pack unless its charge profile is explicitly configurable and correct for the pack.

## F. First power-up order
1. Disconnect battery, PV and piezo power paths.
2. Power ESP32 from USB only; scan I2C and confirm 0x40, 0x41, 0x23.
3. Test DS18B20 and force sensor with no high-voltage source attached.
4. Verify INA219 modules and calibration against a multimeter using a current-limited low-voltage test source.
5. Have the BMS/charger/power wiring independently checked before connecting the battery.
6. Connect PV through its fuse and controller, then verify readings.
7. Only add piezo conditioning after measuring its output and validating the charging path.
8. Keep the battery away from flammable materials during supervised testing; stop if it swells, heats, smells, or behaves abnormally.
