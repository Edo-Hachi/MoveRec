import pyxel
WIN_WIDTH = 128
WIN_HEIGHT = 128

PL_RIGHT = 0 # イメージバンク0の(0,72)から
PL_DOWN = 24 # イメージバンク0の(24,72)から
PL_UP = 48 # イメージバンク0の(72,72)から
WALL_TILE_X = 4 # 壁タイルとして扱うタイルマップのX座標の最小値

# 方向定数
DIR_RIGHT = 0
DIR_LEFT = 1
DIR_UP = 2
DIR_DOWN = 3

def get_tile(tile_x, tile_y):
    bg = pyxel.tilemap(0).pget(tile_x, tile_y)
    print(bg)
    return bg

# 衝突を検出する関数
def detect_collision(x, y, dy):
    x1 = x // 8
    y1 = y // 8
    x2 = (x + 8 - 1) // 8
    y2 = (y + 8 - 1) // 8

    for yi in range(y1, y2 + 1):
        for xi in range(x1, x2 + 1):
            fg_tile_u = get_tile(xi, yi)[0] #x,yが入ってるタプルからX座標だけ引っ張り出してる

            if fg_tile_u >= WALL_TILE_X:    #X座標4以上のエリアにあるスプライトは壁という扱い
                return True
    return False

# 衝突したエンティティを押し戻す関数
def push_back(x, y, dx, dy):
    abs_dx = abs(dx)
    abs_dy = abs(dy)

    if abs_dx > abs_dy:
        sign = 1 if dx > 0 else -1
        for _ in range(abs_dx):
            if detect_collision(x + sign, y, dy):
                break
            x += sign
        sign = 1 if dy > 0 else -1
        for _ in range(abs_dy):
            if detect_collision(x, y + sign, dy):
                break
            y += sign
    else:
        sign = 1 if dy > 0 else -1
        for _ in range(abs_dy):
            if detect_collision(x, y + sign, dy):
                break
            y += sign
        sign = 1 if dx > 0 else -1
        for _ in range(abs_dx):
            if detect_collision(x + sign, y, dy):
                break
            x += sign
    return x, y, dx, dy

class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.dx = 0
        self.dy = 0
        self.direction = DIR_RIGHT # プレイヤーの向きを保持

    def update(self):
        self.dx = 0
        self.dy = 0

        if pyxel.btn(pyxel.KEY_LEFT):
            self.dx = -1
            self.direction = DIR_LEFT
        elif pyxel.btn(pyxel.KEY_RIGHT):
            self.dx = 1
            self.direction = DIR_RIGHT
        elif pyxel.btn(pyxel.KEY_UP):
            self.dy = -1
            self.direction = DIR_UP
        elif pyxel.btn(pyxel.KEY_DOWN):
            self.dy = 1
            self.direction = DIR_DOWN

        # 衝突判定と押し戻し処理
        self.x, self.y, self.dx, self.dy = push_back(self.x, self.y, self.dx, self.dy)

    def draw(self):
        u = 0
        horizon_flip = 1
        if self.direction == DIR_RIGHT:
            u = PL_RIGHT + (pyxel.frame_count // 4 % 3) * 8
        elif self.direction == DIR_LEFT:
            u = PL_RIGHT + (pyxel.frame_count // 4 % 3) * 8 # 右向きスプライトを使用
            horizon_flip = -1
        elif self.direction == DIR_DOWN:
            u = PL_DOWN + (pyxel.frame_count // 4 % 3) * 8
        elif self.direction == DIR_UP:
            u = PL_UP + (pyxel.frame_count // 4 % 3) * 8

        pyxel.blt(self.x, self.y, 0, u, 72, 8 * horizon_flip, 8, 0) # 最後の0は透明色

class App:
    def __init__(self):
        pyxel.init(WIN_WIDTH, WIN_HEIGHT, title="Move Rec" ,display_scale=4, fps=30)
        pyxel.load("my_resource.pyxres")
        
        self.player = Player(60, 60) # プレイヤーを初期位置(60,60)に配置
        
        pyxel.run(self.update, self.draw)

    def update(self):
        if pyxel.btnp(pyxel.KEY_Q):
            pyxel.quit()
        
        self.player.update() # プレイヤーの状態を更新

    def draw(self):
        pyxel.cls(0)
        pyxel.bltm(0, 0, 0, 0, 0, 128, 128)
        
        self.player.draw() # プレイヤーを描画

App()