#Pico Temp Sensor
#v1.0 - C Olson
#
# Designed for Raspberry Pi Pico W, using a DHT22 Temp/Humidity Sensor to record
# data and share via MQTT to a target server.  All Configuration Contained within 
# Config.py

import network
import rp2
import time
import machine
from machine import Pin
from umqtt.simple import MQTTClient
import dht
import urequests
import config

def read_cpu_temp():
    cpu_temp_conversion_factor = 3.3 / 65535
    cpu_temp_sensor = machine.ADC(4)
    reading = cpu_temp_sensor.read_u16() * cpu_temp_conversion_factor
    temperature_c = 27 - (reading - 0.706) / 0.001721
    return temperature_c

def read_dht_22_raw(sensor):
    """
        reads the temperature and humidity from dht.DHT22 sensor.
        returns tuple(temperature, humidity) if no errors
        returns None if there was an error
    """
    try:
        sensor.measure()
        temperature = sensor.temperature()
        temp_f = temperature * (9/5) + 32.0
        humidity = sensor.humidity()
        return temp_f, humidity
    except OSError:
        return None
    
def read_dht_22_with_retry(sensor):
    """Same as [read_dht_22_raw] but tries a few times before giving up. Same returns as [read_dht_22_raw]"""
    count = 0
    while count < 2:
        reading = read_dht_22_raw(sensor)
        count += 1
        if reading is not None:
            return reading
        time.sleep(2)
    return None
    
def read_dht_22(sensor):
    """
        When DHT22 runs on 3.3v sometimes the output results are incomplete, at least what I've seen before
        i.e it can return 2deg, 0deg for a measurement, and the normal readings
        This is a hack to see if this solves this problem, we take 2 measurements and if they are not same (or close), discard
    """
    reading_1 = read_dht_22_with_retry(sensor)
    
    if reading_1 is None:
        print("read_dht_22, reading 1 is None. Abort")
        return None
    # print("Reading 1: {}".format(reading_1))
    
    time.sleep(2)
    
    reading_2 = read_dht_22_with_retry(sensor)
    
    if reading_2 is None:
        print("read_dht_22, reading 2 is None. Abort")
        return None
    
    # print("Reading 2: {}".format(reading_2))
    
    diff = abs(reading_1[0] - reading_2[0])
    #print("Reading between 1 and 2 is {}".format(diff))
    if diff > 2:
        print("Reading between 1 and 2 is more than 2 deg apart, {}".format(diff))
        return None
    
    return reading_1

def wlan_up(wlan):
    print("Connecting to Wifi...")
    wlan.active(True)
    print("Wifi chip is active ... wlan.connect now")
    wlan.connect(config.HOME_WIFI_SSID, config.HOME_WIFI_PWD)
    print("wlan.connect is done")
    
    # Wait for connect or fail
    max_wait = 10
    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
    max_wait -= 1
    print('waiting for connection...')
    time.sleep(1)

    if wlan.status() != 3:
        raise RuntimeError('network connection failed, {}'.format(wlan.status()))
    
    ifconfig = wlan.ifconfig()
    print(ifconfig)
    print("Connected to Wifi")
    return ifconfig
    
def led_error_code(led, error_code: int):
    """Blink LED for a given error code (int). error code == number of times to blink"""
    print("LED Error Status code: {}".format(error_code))
    
    # Run a quick 'start error code sequence'
    # So we know when LED error sequence starts
    start_sequence_counter = 0
    while start_sequence_counter < 3:
        led.value(True)
        time.sleep(0.1)
        led.value(False)
        time.sleep(0.1)
        start_sequence_counter += 1
    
    # Run real error code sequence
    blink_counter = 0
    while blink_counter < error_code:
        time.sleep(1)
        led.value(True)
        time.sleep(1)
        led.value(False)
        blink_counter += 1
    # Make sure to turn off LED when this subroutine finished
    led.value(False)
    print("LED Error Status code finished for: {}".format(error_code))

def ConnectMQTT(mqtt_client):
    #Handle all MQTT connection logic, including retry and recovery should connection to 
    #MQTT server be lost
    try:
        mqtt_client.connect()
        print("Connected to MQTT")
    except Exception as e:
        print("Trouble to connecting to MQTT: {}".format(e))
        #led_error_code(led, 2)
        time.sleep(60)
        ConnectMQTT(mqtt_client)

    
def main():
    print("****Initial Start up****")

    #Set up LED Logic
    led = machine.Pin('LED', machine.Pin.OUT)
    led.value(False)
    led_error_code(led, 1)

    #Set up Sensor
    sensor = dht.DHT22(Pin(config.GPIO_PIN))
    
    #Set up Network
    rp2.country('US')
    wlan = network.WLAN( network.STA_IF )
    try:
        ifconfig = wlan_up(wlan)
    except Exception as e:
        print("Trouble to connecting WiFi: {}".format(e))
        led_error_code(led, 3)

    # Set up MQTT Connection
    mqtt_client = MQTTClient(config.MQTT_CLIENT_ID, config.MQTT_HOST_NAME)    
    ConnectMQTT(mqtt_client)

    print("Entering main loop")
    while True:
        led.value(False)
 
        dht22_reading = read_dht_22(sensor)
        
        debug_str = "None"
        if dht22_reading is not None:
            temp,hum = dht22_reading
            try:
                mqtt_client.publish("sensors/{}/temperature".format(config.MQTT_HW_ID), str(temp), retain=True)
                mqtt_client.publish("sensors/{}/humidity".format(config.MQTT_HW_ID), str(hum), retain=True)
            except Exception as e:
                print("Trouble to connecting to MQTT - Retrying: {}".format(e))
                led_error_code(led, 2)
                time.sleep(60)
                ConnectMQTT(mqtt_client)
                    
            debug_str = "{} ; {}".format(temp, hum,)
        
        #grab CPU Temp if desired
        cpu_temp = read_cpu_temp()
        
        print("{} ; CPU: {}".format(debug_str, cpu_temp))
        
        print("Going to sleep for {}...".format(config.READINTERVAL))
        time.sleep(config.READINTERVAL)
        print("Waking up ...")

    machine.reset()

if __name__=="__main__":
    print('Start/Woke, reset clause {}'.format(machine.reset_cause()))
    main()
