import machine
import network
import time
import gc
import ujson
from umqtt.simple import MQTTClient

# --- Configuration WiFi ---
ssid = "Galaxy S22 4473"
password = "mjet3193"

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    while not wlan.isconnected():
        time.sleep(0.5)
    print("Connecté au WiFi:", wlan.ifconfig())
    return wlan

wlan = connect_wifi()

# --- Configuration MQTT ---
mqtt_server = "raspberrypi.local"  # Adresse de votre broker
client_id = "ESP32_Sensor"
topic_sensor = b"odorwatch/gassensor"
topic_kpi = b"odorwatch/kpi"

client = MQTTClient(client_id, mqtt_server, port=1883)

try:
    client.connect()
    print("Connecté au broker MQTT")
except Exception as e:
    print("Erreur lors de la connexion au broker MQTT:", e)

# --- Configuration du capteur de gaz ---
gas_sensor_pin = 32  # Capteur de gaz v1.4 branché à la broche ADC32
adc_gas = machine.ADC(machine.Pin(gas_sensor_pin))
adc_gas.atten(machine.ADC.ATTN_11DB)  # Pour couvrir toute la plage 0-3,3V

# Définir la fréquence maximale supposée (en Hz) pour le calcul du pourcentage CPU
MAX_CPU_FREQ = 240_000_000  # 240 MHz

while True:
    gas_value = adc_gas.read()  # Valeur entre 0 et 4095

    # Publication de la valeur du capteur
    sensor_msg = ujson.dumps({"gas_value": gas_value})
    client.publish(topic_sensor, sensor_msg)
    print("Publiée sur sensor:", sensor_msg)

    # Calcul de la mémoire libre en pourcentage
    free_mem = gc.mem_free()
    alloc_mem = gc.mem_alloc()
    total_mem = free_mem + alloc_mem
    free_mem_percent = (free_mem / total_mem) * 100 if total_mem > 0 else 0

    # Calcul du pourcentage de la fréquence CPU par rapport à MAX_CPU_FREQ
    cpu_freq = machine.freq()  # En Hz
    cpu_freq_percent = (cpu_freq / MAX_CPU_FREQ) * 100

    # Publication des KPI
    kpi_msg = ujson.dumps({
        "free_memory_percent": free_mem_percent,
        "cpu_freq_percent": cpu_freq_percent
    })
    client.publish(topic_kpi, kpi_msg)
    print("Publiée sur KPI:", kpi_msg)
    
    time.sleep(1)

