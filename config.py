#MQTT Config
#MQTT_HW_ID - Set to unique name for sensor, such as location.  This will be sent in the MQTT Topic
MQTT_HW_ID = "YOURLOCATION"
MQTT_ZONE_ID = "picoDebug"
MQTT_CLIENT_ID = "pico-temp-mqtt-debug"
#MQTT_HOST_NAME - Set to IP or hostname of destination MQTT server on network
MQTT_HOST_NAME = "192.168.2.2"

#WIFI Config
HOME_WIFI_SSID = "YOURSSID"
HOME_WIFI_PWD = "YOURSSIDPASS"

#Main Config
#GPIO_PIN - Set to GPIO Pin of DHT11/DHT22 Temperature Sensor
GPIO_PIN = 26
#READINTERVAL - Set to number of seconds the interval to read from the Temp Sensor
READINTERVAL = 60