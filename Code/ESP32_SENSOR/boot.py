import machine
import network
import time
import gc
import ujson
import ntptime
from umqtt.simple import MQTTClient

# --- Configuration WiFi ---
ssid = "Matthieu"
password = "alternant"

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    while not wlan.isconnected():
        time.sleep(0.5)
    print("Connecté au WiFi:", wlan.ifconfig())
    return wlan

wlan = connect_wifi()


def get_epoch():
    # return int(time.time())
    # en secondes
    result = time.time() * 1000
    return str(result)   # en millisecondes

# --- Synchronisation horaire via NTP ---
try:
    ntptime.host = "pool.ntp.org"
    ntptime.settime()  # met à jour l’horloge interne
    print("Heure NTP synchronisée :", time.localtime())
except Exception as e:
    print("Erreur NTP :", e)

# --- Fonction de génération de timestamp ISO ---
"""
def get_timestamp():
    tm = time.localtime()
    return "{:04d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}Z".format(
        tm[0], tm[1], tm[2], tm[3], tm[4], tm[5]
    )
"""
# --- Fonction de génération de timestamp ISO ---
def get_timestamp():
    tm = time.localtime()  # Obtenir l'heure locale sous forme de tuple
    return tm
      # Format: DD:MM:YYYY HH:MM:SS


# --- Configuration MQTT ---
mqtt_server = "192.168.197.72"
client_id = "ESP32_Sensor"
username = "user1"  # Remplace par ton utilisateur MQTT
password = "123456789"  # Remplace par ton mot de passe MQTT
topic_sensor = b"odorwatch/gassensor"
topic_kpi = b"odorwatch/kpi"

client = MQTTClient(client_id, mqtt_server, port=1883, user=username, password=password)
try:
    client.connect()
    time.sleep(1)
    print("Connecté au broker MQTT")
except Exception as e:
    print("Erreur lors de la connexion au broker MQTT:", e)

# --- Configuration du capteur de gaz ---
gas_sensor_pin = 32  # Capteur de gaz v1.4 branché à la broche ADC32
adc_gas = machine.ADC(machine.Pin(gas_sensor_pin))
adc_gas.atten(machine.ADC.ATTN_11DB)  # Pour couvrir toute la plage 0-3,3V

# Définir la fréquence maximale supposée (en Hz) pour le calcul du pourcentage CPU
MAX_CPU_FREQ = 240_000_000  # 240 MHz

def reconnect_mqtt():
    global client
    try:
        client.disconnect()
    except:
        pass  # Ignore l'erreur si déjà déconnecté
    client = MQTTClient(client_id, mqtt_server, port=1883, user=username, password=password)
    client.connect()
    time.sleep(1)
    print("Reconnecté au broker MQTT")

while True:
    try:
        gas_value = adc_gas.read()

        threshold = 500
        if gas_value > threshold:
            available = False
            #status = "toilette occupée"
        else:
            available = True
            #status = "toilette libre"

        sensor_msg = ujson.dumps({
            "esp_id": client_id, 
            "available": available, 
            "gaz_level": gas_value, 
            "sensor_status_ok": True, 
            #"value": status,
            "timestamp": get_timestamp()
        })

        client.publish(topic_sensor, sensor_msg.encode())  # Convertir en bytes
        print("Publiée sur sensor:", sensor_msg)

    except OSError as e:
        print("Erreur MQTT:", e)
        reconnect_mqtt()

    time.sleep(1)

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
        "cpu_freq_percent": cpu_freq_percent,
        "timestamp": get_timestamp()
    })
    client.publish(topic_kpi, kpi_msg.encode())
    print("Publiée sur KPI:", kpi_msg)
    
    time.sleep(1)

