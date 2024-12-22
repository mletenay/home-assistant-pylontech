# Pylontech BMS monitoring component for Home Assistant

Home Assistant custom component for Pylontech (high voltage) BMS. Accessed via BMS' RS232 console port exposed over WIFI and cheap ESP8266/ESP32 hardware.

Component is developed on Pylontech's SC1000 BMS with H48050 BMU's but should also with SC0500 BMS or other PowerCube X1/X2 configurations.

## Required hardware

Any cheap ESP8266 or ESP32 microcontroller and a RS232 transciever like [MAX3232](https://www.sparkfun.com/products/11189) could be used to construct the necessary hw.

See [Pylontech Battery Monitoring via WiFi](https://github.com/irekzielinski/Pylontech-Battery-Monitoring#parts-needed-and-schematics) for schematics example, use the RJ45 connector version.

The ESP8266/32 microcontroller should be programmed and connected to Home Assistant via [ESPHome](https://esphome.io/) and its custom component [Pylontech BMS console server for ESPHome](https://github.com/mletenay/esphome-stream-server).

## Installation

Install this component using [HACS](https://hacs.xyz/) by adding custom repository [https://github.com/mletenay/home-assistant-pylontech](https://github.com/mletenay/home-assistant-pylontech) and searching for `Pylontech` in the `Integrations`.

## Configuration

The component requires the host/IP and the port where the [Pylontech BMS console server for ESPHome](https://github.com/mletenay/esphome-stream-server) is listening.

## Exposed sensors

The integration connects to BMS in regular intrervals (default 30s) and executes `pwr` and `unit` console commands to read and report current state (charge, voltage, current, temperature, state, error code etc.) of BMS itself as well as its individual BMUs.
