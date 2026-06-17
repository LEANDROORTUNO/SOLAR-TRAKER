from machine import Pin, SoftI2C, PWM
from time import sleep_ms

class MiniLCD:
    def __init__(self, i2c, addr=0x27):
        self.i2c = i2c
        self.addr = addr
        self.bl = 0x08
        sleep_ms(50)
        self.write_cmd(0x03)
        sleep_ms(5)
        self.write_cmd(0x03)
        sleep_ms(5)
        self.write_cmd(0x03)
        self.write_cmd(0x02)
        self.write_cmd(0x28)
        self.write_cmd(0x0C)
        self.write_cmd(0x06)
        self.clear()

    def write_word(self, data):
        self.i2c.writeto(self.addr, bytes([data | self.bl]))

    def send_half(self, data):
        self.write_word(data | 0x04)
        sleep_ms(1)
        self.write_word(data & ~0x04)
        sleep_ms(1)

    def write_cmd(self, cmd):
        self.send_half(cmd & 0xF0)
        self.send_half((cmd << 4) & 0xF0)

    def write_data(self, data):
        self.send_half((data & 0xF0) | 0x01)
        self.send_half(((data << 4) & 0xF0) | 0x01)
        
    def clear(self):
        self.write_cmd(0x01)
        sleep_ms(2)

    def cursor(self, x, y):
        addr = x & 0x0F
        if y == 1:
            addr |= 0x40
        self.write_cmd(0x80 | addr)

    def print_str(self, text):
        for char in text:
            self.write_data(ord(char))

# --- CONFIGURACIÓN DE SERVOS (¡CORREGIDO!) ---
servo_h = PWM(Pin(13))
servo_h.init(freq=50, duty=77) # Inicializa en 90 grados (parado para 360°)

servo_v = PWM(Pin(12))
servo_v.init(freq=50, duty=77) # Inicializa en 90 grados para el de 180°

def controlar_servo_h(accion):
    if accion == "IZQUIERDA":
        servo_h.duty(55)   # Pulso claro de giro antihorario
    elif accion == "DERECHA":
        servo_h.duty(100)  # Pulso claro de giro horario
    else:
        servo_h.duty(77)   # Detener por completo el servo de 360°

def mover_servo_v(grados):
    # Conversión estándar precisa para el servo de 180°
    duty = int(25 + (grados / 180) * 102)
    servo_v.duty(duty)

# Inicialización de posiciones
pos_v = 90
pos_h = 90
controlar_servo_h("PARAR")
mover_servo_v(pos_v)

# --- CONFIGURACIÓN DE SENSORES DIGITALES ---
tl = Pin(36, Pin.IN) 
tr = Pin(39, Pin.IN) 
bl = Pin(34, Pin.IN) 
br = Pin(35, Pin.IN) 

# Configuración de la Pantalla LCD
i2c = SoftI2C(scl=Pin(22), sda=Pin(21), freq=100000)
lcd = MiniLCD(i2c)

lcd.print_str("  SOLAR TRACKER")
lcd.cursor(0, 1)
lcd.print_str(" DIGITAL MODE V2")
sleep_ms(2000)
lcd.clear()

# LÍMITES DEFINIDOS
lim_v_max, lim_v_min = 150, 30
lim_h_max, lim_h_min = 180, 0

while True:
    # 1. Leer los estados puros del pin (0 o 1)
    luz_tl = not tl.value()
    luz_tr = not tr.value()
    luz_bl = not bl.value()
    luz_br = not br.value()
    
    print("TL:{} TR:{} BL:{} BR:{} | H:{} V:{}".format(luz_tl, luz_tr, luz_bl, luz_br, pos_h, pos_v))
    
    # --- LÓGICA VERTICAL (SERVO 180°) ---
    if (luz_tl or luz_tr) and not (luz_bl or luz_br):
        pos_v = max(lim_v_min, pos_v - 2)
        mover_servo_v(pos_v)
    elif (luz_bl or luz_br) and not (luz_tl or luz_tr):
        pos_v = min(lim_v_max, pos_v + 2)
        mover_servo_v(pos_v)
        
    # --- LÓGICA HORIZONTAL (SERVO 360°) ---
    if (luz_tl or luz_bl) and not (luz_tr or luz_br):
        controlar_servo_h("IZQUIERDA")
        pos_h = max(lim_h_min, pos_h - 2)
        sleep_ms(60) 
    elif (luz_tr or luz_br) and not (luz_tl or luz_bl):
        controlar_servo_h("DERECHA")
        pos_h = min(lim_h_max, pos_h + 2)
        sleep_ms(60)
    else:
        controlar_servo_h("PARAR")
        
    # Mostrar estado en la LCD
    lcd.cursor(0, 0)
    lcd.print_str("H-Angle: {}   ".format(pos_h))
    lcd.cursor(0, 1)
    lcd.print_str("V-Angle: {}   ".format(pos_v))
    
    sleep_ms(40)