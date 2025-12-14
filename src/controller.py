"""
GAME CONTROLLER

"""

from time import ticks_ms, ticks_diff, sleep_ms
from modulino import ModulinoMovement
from machine import Pin, I2C
from i2c_lcd import RGBDisplay
import network
import espnow
import math

move = ModulinoMovement()

# GAME STATE -> buttons
game_active = True

# STEP
STEP_THRESHOLD = 0.05  # strength of a peak, indicating a step
MIN_STEP_INTERVAL = 1000  # min. interval in ms between "steps"

# DIRECTION
TILT_THRESHOLD = 0.10  # slight controller tilt

last_step_time = 0

# ESPNow
wlan = network.WLAN(network.STA_IF)
wlan.active(True)

esp = espnow.ESPNow()
esp.active(True)

peer_maze = b"\xec\xda;U\x13\xb4"  # mac-address maze-arudino

try:
    esp.add_peer(peer_maze)
    print("Maze peer added:", peer_maze)
except OSError as e:
    print("Maze peer already exists or error:", e)

# HARDWARE
## GROVE LEDs
LED_UP_PIN = "A1"
LED_DOWN_PIN = "D8"
LED_LEFT_PIN = "D9"
LED_RIGHT_PIN = "A2"

led_up = Pin(LED_UP_PIN, Pin.OUT)
led_down = Pin(LED_DOWN_PIN, Pin.OUT)
led_right = Pin(LED_RIGHT_PIN, Pin.OUT)
led_left = Pin(LED_LEFT_PIN, Pin.OUT)

## DUAL BUTTONS
BUTTON_RED_PIN = "TX"
BUTTON_BLUE_PIN = "RX"

btn_red = Pin(BUTTON_RED_PIN, Pin.IN, Pin.PULL_UP)
btn_blue = Pin(BUTTON_BLUE_PIN, Pin.IN, Pin.PULL_UP)

### previous button press
prev_blue = 1
prev_red = 1

## LCD-DISPLAY (I2C)
i2c_bus = I2C(1)
display = RGBDisplay(i2c_bus)
display.clear()
display.write("Invisyrinth")  # show for 3 seconds
display.color(0, 0, 255)
sleep_ms(3000)
display.clear()


# FEEDBACK HELPER
## LEDs
def leds_off():
    led_up.value(0)
    led_down.value(0)
    led_left.value(0)
    led_right.value(0)


def led_wall_direction(dr, dc): # dr, dc = row_change, col_change
    leds_off()
    if dr == -1:  # wall above
        led_up.value(1)
    elif dr == 1:  # wall below
        led_down.value(1)
    elif dc == -1:  # wall left
        led_left.value(1)
    elif dc == 1:  # wall right
        led_right.value(1)


## LCD-DISPLAY
def lcd_message(line1: str = "", line2: str = ""):
    # shorten line to 16 chars (2x16 Display)
    line1 = (line1 or "")[:16]  # mandatory
    line2 = (line2 or "")[:16]  # optional

    try:
        display.clear()
        display.move(0, 0)  # col 0, row 0 (1st char, top row)
        display.write(line1)

        if line2:
            display.move(0, 1)  # col 0, row 1 (1st char, bottom row)
            display.write(line2)

    except Exception as e:
        # Fallback
        print("LCD ERROR:", e)
        print("LCD:", line1, "|", line2)


# STEP
def detect_step() -> bool:
    global last_step_time

    ax, ay, az = move.accelerometer
    magnitude = math.sqrt(ax * ax + ay * ay + az * az)
    delta = abs(magnitude - 1.0)  # 1.0 ~ resting value

    now = ticks_ms()

    # too close in time to last step (1 second) -> ignore
    if ticks_diff(now, last_step_time) < MIN_STEP_INTERVAL:
        return False

    if delta > STEP_THRESHOLD:
        last_step_time = now
        print("Step detected, delta =", delta)
        return True

    return False


# DIRECTION
def get_direction_from_tilt():
    ax, ay, az = move.accelerometer

    row_change = 0
    col_change = 0

    # abs = strength of tilt per axis
    abs_x = abs(ax)
    abs_y = abs(ay)

    if max(abs_x, abs_y) < TILT_THRESHOLD:
        return 0, 0

    if abs_y >= abs_x:
        # VERTICAL movement (forward / backward)
        if ay < 0:
            row_change = -1  # up
        else:
            row_change = 1  # down
        col_change = 0
    else:
        # HORIZONTAL movement (left / right)
        if ax < 0:
            col_change = -1  # left
        else:
            col_change = 1  # right
        row_change = 0

    print("DIR (dr, dc):", row_change, col_change)
    return row_change, col_change


## ESPNow (sender)
### sends 2 values (dr, dc) as string per ESPNow
def send_step_via_espnow(row_change: int, col_change: int): # row_change, col_change = dr, dc
    message = "{},{}".format(row_change, col_change)
    print("SEND:", message)
    try:
        esp.send(peer_maze, message.encode())
    except OSError as e:
        print("ESPNow send failed:", e)


## ESPNow Feedback (status) from receiver
### checks if maze-ESP has sent a status
def check_for_feedback():
    host, msg = esp.recv(0)
    if not msg:
        return

    try:
        status = msg.decode()
        print("STATUS RECEIVED:", status)
        handle_feedback(status)
    except Exception as e:
        print("Error decoding status:", e)


# FEEDBACK
def handle_feedback(status: str):
    parts = status.split(",")

    ## reset
    if status == "reset_ok":
        leds_off()
        display.color(0, 0, 255)  # blue
        lcd_message("New run", "Good luck!")
        return

    ## wall
    if parts[0] == "wall":
        display.color(255, 0, 0)  # red
        if len(parts) == 3: # 3 values expected (wall, dr, dc)
            try:
                dr = int(parts[1]) # forward / backward
                dc = int(parts[2]) # left / right
                led_wall_direction(dr, dc)
            except ValueError:
                leds_off()
        lcd_message("Careful,", "wall!")

    ## goal
    elif parts[0] == "goal":
        leds_off()
        display.color(0, 255, 0)  # green
        lcd_message("Congratulations,", "you won!")

    ## ok - keep going
    elif parts[0] == "ok":
        leds_off()
        display.color(255, 255, 0)  # yellow
        lcd_message("Keep going!", "")

    ## unknown (error)
    else:
        leds_off()
        display.color(255, 255, 255)  # white
        lcd_message("Unknown status", status)


# BUTTONS
## reset maze / game (blue button)
def send_reset():
    print("SEND: reset")
    try:
        esp.send(peer_maze, b"reset")
    except OSError as e:
        print("ESPNow send failed:", e)


def handle_buttons():
    global prev_blue, prev_red, game_active

    blue = btn_blue.value()
    red = btn_red.value()

    ## RED BUTTON: only react when transition 1 -> 0 (button pushed just now)
    ### handles reset
    if red == 0 and prev_red == 1:
        print("Red button pressed -> RESET GAME")
        send_reset()
        lcd_message("New run", "Good luck!")
        sleep_ms(300)

    prev_red = red

    ## BLUE BUTTON: switch game state
    ### handles pause / resume
    if blue == 0 and prev_blue == 1:
        game_active = not game_active

        if game_active:
            print("Blue button pressed -> GAME RESUME")
            leds_off()
            display.color(0, 0, 255)  # blue
            lcd_message("Game on", "")
        else:
            print("Blue button pressed -> GAME PAUSE")
            leds_off()
            display.color(0, 0, 255)  # blue
            lcd_message("Game paused", "")

        sleep_ms(300)

    prev_blue = blue

# MAIN
def main():
    print("Controller ready.") 
    lcd_message("Ready to play!", "Take a step.")

    while True:
        check_for_feedback()
        handle_buttons()

        # if game paused (False), do not detect steps
        if not game_active:
            sleep_ms(50)
            continue

        if not detect_step():
            sleep_ms(50)
            continue

        row_change, col_change = get_direction_from_tilt()

        if row_change == 0 and col_change == 0:
            print("Step without clear direction – ignored.")
            continue

        send_step_via_espnow(row_change, col_change)
        sleep_ms(50)


if __name__ == "__main__":
    main()