"""
MAZE
"""

import network
import espnow
from machine import I2C
from ht16k33 import HT16K33Matrix

# Labyrinth (MAZE)

MAZE = [
    "########",  # Row 0 (top)
    "#      #",  # Row 1
    "#####  #",  # Row 2
    "#      #",  # Row 3
    "#   ####",  # Row 4
    "##     #",  # Row 5
    "#      #",  # Row 6
    "# ######",  # Row 7 (bottom)
]

WALL = "#"
PLAYER = "P" # only for testing purposes (print_maze())

# START AND GOAL POSITION
player_row = 1
player_col = 1

goal_row = 7  # bottom row = index 7
goal_col = 1  # 2 steps from the left edge = index 1

# MATRIX
i2c = I2C(0)
matrix = HT16K33Matrix(i2c)
matrix.set_angle(180)
matrix.set_brightness(3)

# HELPERS
## checks if (row, col) is a wall or outside of the maze
def is_wall(row, col) -> bool:
    if row < 0 or row >= len(MAZE):
        return True
    if col < 0 or col >= len(MAZE[0]):
        return True
    return MAZE[row][col] == WALL


## show MAZE and player position in terminal (for testing purposes)
def print_maze():
    for r, line in enumerate(MAZE):
        row_chars = list(line)

        if r == player_row:
            row_chars[player_col] = PLAYER

        if r == goal_row:
            row_chars[goal_col] = "G"

        print("".join(row_chars))
    print()  # space for better looks


# FEEDBACK
## show maze, player and goal on matrix
def draw_maze_on_matrix():
    # clear all pixels
    matrix.clear()

    for r, line in enumerate(MAZE):
        if r > 7:
            break  # height is only 8 pixels

        for c, ch in enumerate(line):
            if c > 7:
                break  # width is only 8 pixels

            # default: pixel off
            pixel = 0

            # pixel on if wall or player position
            if ch == WALL:
                pixel = 1

            if r == player_row and c == player_col:
                pixel = 1

            # pixel off if goal position
            if r == goal_row and c == goal_col:
                pixel = 0

            matrix.plot(7 - c, r, pixel)  # reverse matrix x-axis (de-mirror)

    # show wall, player and goal position pixels
    matrix.draw()

# RESET
def reset_game():
    global player_row, player_col
    player_row = 1
    player_col = 1
    print("GAME RESET")
    print_maze()
    draw_maze_on_matrix()

# STEP
## Applies step to player -> calculate new position, return status
def apply_step(row_change: int, col_change: int):
    global player_row, player_col

    ## new position
    new_row = player_row + row_change
    new_col = player_col + col_change

    ## wall
    if is_wall(new_row, new_col):
        status = "wall,{},{}".format(row_change, col_change)
    
    ## ok - keep going
    else:
        player_row = new_row
        player_col = new_col
        status = "ok"

    print_maze()
    draw_maze_on_matrix()

    ## goal reached
    if player_row == goal_row and player_col == goal_col:
        status = "goal"

    ## status (wall, ok, goal)
    return status

# MAIN
def main():
    ## activate wifi
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    ## initialize ESPNow
    esp = espnow.ESPNow()
    esp.active(True)

    controller_mac = b"tM\xbd\xa1\n\xbc"

    try:
        esp.add_peer(controller_mac)
        print("Controller peer added:", controller_mac)
    except OSError as e:
        print("Peer exists or error:", e)

    print("ESPNow Receiver ready. Waiting for steps...")
    print("Start:", player_row, player_col)
    print("Goal:", goal_row, goal_col)
    print_maze()
    draw_maze_on_matrix()

    while True:
        host, msg = esp.recv()
        ## code waits until command from controller received (movement or reset)
        if not msg:
            ## no command: go back to waiting
            continue

        print("RAW MSG:", msg)

        ## decode message
        try:
            decoded = msg.decode()  # example "-1,0" (dr, dc)

            ## check for reset command
            if decoded == "reset":
                reset_game()

                ## inform controller about reset
                try:
                    esp.send(controller_mac, b"reset_ok")
                except OSError as e:
                    print("ESPNow send status failed:", e)
                continue  

            ## else: step command
            dr_str, dc_str = decoded.split(",")
            dr = int(dr_str)
            dc = int(dc_str)

            print("APPLY STEP (dr, dc):", dr, dc)
            status = apply_step(dr, dc)
            print("STATUS:", status)

            try:
                esp.send(controller_mac, status.encode())
            except OSError as e:
                print("ESPNow send status failed:", e)

        except Exception as e:
            print("Error parsing message:", e)

if __name__ == "__main__":
    main()
