# PicoW_DHT22_TempSensor

Micropython code designed to leverage a Raspberry Pi Pico W DHT22 Temperature Sensor to read Temperature and Humidity levels, and publish to an MQTT target server for collection and processing, for example into InfluxDB, Grafana, etc.

All configuration items are contained withing Config.py:
  - Wifi SSID and Password
  - Reading Interfal
  - Location Tag (used to differentiate different sensor locations if multiple are required) within the MQTT topic string
  
  
