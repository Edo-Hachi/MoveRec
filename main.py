import pyxel
WIN_WIDTH = 128
WIN_HEIGHT = 128

PL_RIGHT = 0 # イメージバンク0の(0,72)から
PL_DOWN = 24 # イメージバンク0の(24,72)から
PL_UP = 48 # イメージバンク0の(48,72)から
WALL_TILE_X = 4 # 壁タイルとして扱うタイルマップのX座標の最小値

# 方向定数
DIR_RIGHT = 0
DIR_LEFT = 1
DIR_UP = 2
DIR_DOWN = 3

def get_tile(tile_x, tile_y):
    # pyxel.tilemap(0).pget(tile_x, tile_y) は、タイルマップ0番の(tile_x, tile_y)にあるピクセルデータを取得する
    # タイルマップの各タイルは8x8ピクセルで構成されており、その左上隅のピクセルデータを取得することで、
    # そのタイルがどの画像バンクのどの位置にあるかを示す情報（(u, v)座標）が得られる
    return pyxel.tilemap(0).pget(tile_x, tile_y)

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

        self.x += self.dx
        self.y += self.dy

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