import pyxel

WIN_WIDTH = 128
WIN_HEIGHT = 128
TILE_SIZE = 8
PLAYER_SPEED = 2
PLAYER_GRAVITY = 1
PLAYER_MAX_FALL_SPEED = 3
TRANSPARENT_COLOR = 0 # Assuming 0 is the transparent color for player sprite

# Helper function to get tile from our custom tilemap
def get_tile(tilemap, tile_x, tile_y):
    if 0 <= tile_y < len(tilemap) and 0 <= tile_x < len(tilemap[0]):
        return tilemap[tile_y][tile_x]
    return 0 # Return 0 for out of bounds, assuming 0 is empty/non-solid

# Helper function to detect collision with solid tiles (value 1)
def detect_collision(tilemap, x, y):
    # Calculate the tile coordinates that the entity occupies
    x1 = x // TILE_SIZE
    y1 = y // TILE_SIZE
    x2 = (x + TILE_SIZE - 1) // TILE_SIZE
    y2 = (y + TILE_SIZE - 1) // TILE_SIZE

    # Check for collision with any solid tiles in the occupied area
    for yi in range(y1, y2 + 1):
        for xi in range(x1, x2 + 1):
            if get_tile(tilemap, xi, yi) == 1: # Assuming 1 is a solid tile
                return True
    return False

# Helper function to push back entity from collision
def push_back(tilemap, x, y, dx, dy):
    # Apply horizontal movement first
    new_x = x + dx
    if detect_collision(tilemap, new_x, y):
        # If collision, move back one pixel at a time until no collision
        while detect_collision(tilemap, new_x, y):
            new_x -= (1 if dx > 0 else -1)
        dx = 0 # Stop horizontal movement
    x = new_x

    # Apply vertical movement
    new_y = y + dy
    if detect_collision(tilemap, x, new_y):
        # If collision, move back one pixel at a time until no collision
        while detect_collision(tilemap, x, new_y):
            new_y -= (1 if dy > 0 else -1)
        dy = 0 # Stop vertical movement
    y = new_y
    
    return x, y, dx, dy


class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.dx = 0
        self.dy = 0
        self.direction = 1 # 1 for right, -1 for left

    def update(self, tilemap):
        # Horizontal movement
        if pyxel.btn(pyxel.KEY_LEFT):
            self.dx = -PLAYER_SPEED
            self.direction = -1
        elif pyxel.btn(pyxel.KEY_RIGHT):
            self.dx = PLAYER_SPEED
            self.direction = 1
        else:
            self.dx = 0 # Stop if no key pressed

        # Apply gravity
        self.dy = min(self.dy + PLAYER_GRAVITY, PLAYER_MAX_FALL_SPEED)

        # Apply movement and resolve collisions
        self.x, self.y, self.dx, self.dy = push_back(tilemap, self.x, self.y, self.dx, self.dy)

        # Keep player within screen bounds
        self.x = max(0, min(self.x, WIN_WIDTH - TILE_SIZE))
        self.y = max(0, min(self.y, WIN_HEIGHT - TILE_SIZE))

    def draw(self):
        # Player sprite (0,1) from my_resource.pyxres
        # pyxel.blt(x, y, img, u, v, w, h, [colkey])
        pyxel.blt(self.x, self.y, 0, 0 * TILE_SIZE, 1 * TILE_SIZE, TILE_SIZE, TILE_SIZE, TRANSPARENT_COLOR)


class App:
    def __init__(self):
        pyxel.init(WIN_WIDTH, WIN_HEIGHT, title="Pyxel Platformer")
        pyxel.load("my_resource.pyxres")

        self.tilemap = [[0 for _ in range(WIN_WIDTH // TILE_SIZE)] for _ in range(WIN_HEIGHT // TILE_SIZE)]
        # Initialize the bottom row of the tilemap with 1s (floor)
        for i in range(WIN_WIDTH // TILE_SIZE):
            self.tilemap[WIN_HEIGHT // TILE_SIZE - 1][i] = 1
        
        # Initialize player
        self.player = Player(WIN_WIDTH // 2 - TILE_SIZE // 2, WIN_HEIGHT // 2 - TILE_SIZE * 2)

        pyxel.run(self.update, self.draw)

    def update(self):
        self.player.update(self.tilemap)

    def draw(self):
        pyxel.cls(0) # Clear screen with color 0

        # Draw tilemap
        for y in range(WIN_HEIGHT // TILE_SIZE):
            for x in range(WIN_WIDTH // TILE_SIZE):
                if self.tilemap[y][x] == 1: # If it's a floor tile
                    pyxel.blt(x * TILE_SIZE, y * TILE_SIZE, 0, 1 * TILE_SIZE, 0 * TILE_SIZE, TILE_SIZE, TILE_SIZE)
        
        # Draw player
        self.player.draw()

App()