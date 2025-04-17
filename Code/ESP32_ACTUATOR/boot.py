import machine
import network
import time
import ujson
from umqtt.simple import MQTTClient
import webrepl

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
webrepl.start()



# --- Configuration MQTT ---
mqtt_server = "192.168.197.72"  # Adresse de votre broker
client_id = "ESP32_Actuator"
username = "user1"  # Remplace par ton utilisateur MQTT
password = "123456789"  # Remplace par ton mot de passe MQTT
topic_gas = b"odorwatch/gassensor"
topic_kpi = b"odorwatch/kpi"

client = MQTTClient(client_id, mqtt_server, port=1883, user=username, password=password)

# --- Configuration de l'actionneur ---
# LED sur GPIO 2
led = machine.Pin(2, machine.Pin.OUT)
# Contrôle du moteur sur GPIO 23
motor_ctrl = machine.Pin(23, machine.Pin.OUT)

def moteur_on():
    motor_ctrl.value(1)

def moteur_off():
    motor_ctrl.value(0)

# Callback appelée lors de la réception d'un message MQTT
def sub_callback(topic, msg):
    print("Reçu sur", topic, ":", msg)
    try:
        # Décodage du message JSON
        data = ujson.loads(msg.decode())
    except Exception as e:
        print("Erreur lors du décodage JSON:", e)
        return

    # Traiter en fonction du topic
    if topic == topic_gas:
        gas_val = data.get("gaz_level", 0)
        if gas_val > 500:
            led.value(1)
            moteur_on()
            print("LED et Moteur ON (gaz élevé: {})".format(gas_val))
        else:
            led.value(0)
            moteur_off()
            print("LED et Moteur OFF (gaz normal: {})".format(gas_val))
    elif topic == topic_kpi:
        free_memory_percent = data.get("free_memory_percent", 0)
        cpu_freq_percent = data.get("cpu_freq_percent", 0)
        print("KPI reçu : Mémoire Libre: {:.2f}% - CPU: {:.2f}%".format(free_memory_percent, cpu_freq_percent))
    else:
        print("Topic inconnu :", topic)

# Définir le callback AVANT l'abonnement
client.set_callback(sub_callback)

try:
    client.connect()
    print("Connecté au broker MQTT")
except Exception as e:
    print("Erreur lors de la connexion au broker MQTT:", e)

# Abonnement aux deux topics
client.subscribe(topic_gas)
client.subscribe(topic_kpi)
print("Abonné aux topics", topic_gas, "et", topic_kpi)

# Boucle principale : attente des messages MQTT
while True:
    try:
        client.check_msg()  # check_msg() évite de bloquer l'exécution
        time.sleep(0.1)  # Petite pause pour éviter une boucle trop rapide
    except Exception as e:
        print("Erreur MQTT:", e)
        time.sleep(1)  # Pause avant de réessayer


