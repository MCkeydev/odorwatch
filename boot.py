import machine
import math
import time

# Broches pour les 4 LED (haut, bas, gauche, droite)
# Adaptez ces numéros de GPIO à votre montage
LED_UP_PIN = 18
LED_DOWN_PIN = 19
LED_LEFT_PIN = 21
LED_RIGHT_PIN = 17

led_up = machine.Pin(LED_UP_PIN, machine.Pin.OUT)
led_down = machine.Pin(LED_DOWN_PIN, machine.Pin.OUT)
led_left = machine.Pin(LED_LEFT_PIN, machine.Pin.OUT)
led_right = machine.Pin(LED_RIGHT_PIN, machine.Pin.OUT)

# Rassemble les 4 LEDs dans une liste pour simplifier l'extinction
leds = [led_up, led_down, led_left, led_right]

# Configurer les ADC pour le joystick sur les broches 34 et 35
adc_x = machine.ADC(machine.Pin(34))
adc_y = machine.ADC(machine.Pin(35))

# Configurer l'atténuation pour couvrir la plage 0 - 3,3V
adc_x.atten(machine.ADC.ATTN_11DB)
adc_y.atten(machine.ADC.ATTN_11DB)

# Valeur centrale et zone "morte" (à adapter selon votre joystick)
center = 2048   # Pour un ADC 12 bits (0-4095)
deadzone = 300  # Seuil pour considérer le joystick comme "au centre"

def clear_leds():
    """Éteint toutes les LEDs."""
    for led in leds:
        led.value(0)

while True:
    # Lecture des valeurs analogiques
    x_val = adc_x.read()  # entre 0 et 4095
    y_val = adc_y.read()  # entre 0 et 4095

    # Écarts par rapport au centre
    dx = x_val - center
    dy = y_val - center

    # Calcul de la magnitude (distance au centre)
    magnitude = math.sqrt(dx*dx + dy*dy)

    # Éteint toutes les LEDs avant de choisir la bonne
    clear_leds()

    # Si on est au centre (dans la deadzone), on n'allume rien
    if magnitude < deadzone:
        time.sleep(0.1)
        continue

    # Calcul de l'angle en degrés
    angle = math.atan2(dy, dx)  # Retourne un angle entre -pi et +pi
    angle_deg = math.degrees(angle)
    if angle_deg < 0:
        angle_deg += 360  # On normalise pour avoir un angle entre 0 et 360

    """
    Répartition des angles (0° = droite, 90° = haut, 180° = gauche, 270° = bas) :
      - Droite   : 315° à 360° ou 0° à 45°
      - Haut     : 45° à 135°
      - Gauche   : 135° à 225°
      - Bas      : 225° à 315°
    """

    if (angle_deg >= 315) or (angle_deg < 45):
        # Droite
        led_right.value(1)
    elif angle_deg < 135:
        # Haut
        led_up.value(1)
    elif angle_deg < 225:
        # Gauche
        led_left.value(1)
    else:
        # Bas
        led_down.value(1)
    
    time.sleep(0.1)
