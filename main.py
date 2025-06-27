import pyxel

# 定数定義
WIN_WIDTH = 128             # ウィンドウの幅
WIN_HEIGHT = 128            # ウィンドウの高さ
TILE_SIZE = 8               # タイルのサイズ (ピクセル単位)
PLAYER_SPEED = 2            # プレイヤーの水平移動速度
PLAYER_GRAVITY = 1          # プレイヤーにかかる重力 (Y方向の加速度)
PLAYER_MAX_FALL_SPEED = 3   # プレイヤーの最大落下速度
TRANSPARENT_COLOR = 0       # プレイヤーのスプライトの透明色 (Pyxelのパレットにおける色番号)

# カスタムタイルマップからタイルを取得するためのヘルパー関数
def get_tile(tilemap, tile_x, tile_y):
    # 指定されたタイル座標がタイルマップの範囲内にあるかチェック
    if 0 <= tile_y < len(tilemap) and 0 <= tile_x < len(tilemap[0]):
        # 範囲内であれば、その座標にあるタイルの値を返す
        return tilemap[tile_y][tile_x]
    # 範囲外の場合は0を返す。0は空のタイルまたはソリッドではないタイルと仮定
    return 0

# ソリッドなタイル（値が1のタイル）との衝突を検出するためのヘルパー関数
def detect_collision(tilemap, x, y):
    # エンティティが占めるタイルの座標を計算
    x1 = x // TILE_SIZE
    y1 = y // TILE_SIZE
    x2 = (x + TILE_SIZE - 1) // TILE_SIZE
    y2 = (y + TILE_SIZE - 1) // TILE_SIZE

    # エンティティが占める可能性のある領域内のソリッドなタイルとの衝突をチェック
    for yi in range(y1, y2 + 1):
        for xi in range(x1, x2 + 1):
            if get_tile(tilemap, xi, yi) == 1: # 1がソリッドなタイルと仮定
                return True
    return False

# 衝突したエンティティを押し戻すヘルパー関数
def push_back(tilemap, x, y, dx, dy):
    # まず水平方向の移動を適用
    new_x = x + dx
    if detect_collision(tilemap, new_x, y):
        # 衝突した場合、衝突しなくなるまで1ピクセルずつ戻す
        while detect_collision(tilemap, new_x, y):
            new_x -= (1 if dx > 0 else -1)
        dx = 0 # 水平方向の移動を停止
    x = new_x

    # 次に垂直方向の移動を適用
    new_y = y + dy
    if detect_collision(tilemap, x, new_y):
        # 衝突した場合、衝突しなくなるまで1ピクセルずつ戻す
        while detect_collision(tilemap, x, new_y):
            new_y -= (1 if dy > 0 else -1)
        dy = 0 # 垂直方向の移動を停止
    y = new_y
    
    return x, y, dx, dy


class Player:
    # プレイヤーの初期化
    def __init__(self, x, y):
        self.x = x # X座標
        self.y = y # Y座標
        self.dx = 0 # X方向の速度
        self.dy = 0 # Y方向の速度
        self.direction = 1 # 向き (1:右, -1:左)

    # プレイヤーの状態を更新するメソッド
    def update(self, tilemap):
        # 水平移動の入力処理
        if pyxel.btn(pyxel.KEY_LEFT):
            self.dx = -PLAYER_SPEED
            self.direction = -1
        elif pyxel.btn(pyxel.KEY_RIGHT):
            self.dx = PLAYER_SPEED
            self.direction = 1
        else:
            self.dx = 0 # キーが押されていない場合は停止

        # 重力を適用
        self.dy = min(self.dy + PLAYER_GRAVITY, PLAYER_MAX_FALL_SPEED)

        # 移動を適用し、衝突を解決
        self.x, self.y, self.dx, self.dy = push_back(tilemap, self.x, self.y, self.dx, self.dy)

        # プレイヤーを画面内に留める
        self.x = max(0, min(self.x, WIN_WIDTH - TILE_SIZE))
        self.y = max(0, min(self.y, WIN_HEIGHT - TILE_SIZE))

    # プレイヤーを描画するメソッド
    def draw(self):
        # プレイヤーのスプライトを描画 (my_resource.pyxresの画像バンク0、(0,1)の位置にあるタイル)
        # pyxel.blt(x, y, img, u, v, w, h, [colkey])
        # x, y: 描画位置
        # img: 画像バンク番号 (0)
        # u, v: 画像バンク内の描画開始位置 (0 * TILE_SIZE, 1 * TILE_SIZE)
        # w, h: 描画する画像の幅と高さ (TILE_SIZE, TILE_SIZE)
        # colkey: 透明色 (TRANSPARENT_COLOR)
        pyxel.blt(self.x, self.y, 0, 0 * TILE_SIZE, 1 * TILE_SIZE, TILE_SIZE, TILE_SIZE, TRANSPARENT_COLOR)


class App:
    # アプリケーションの初期化
    def __init__(self):
        # Pyxelの初期化 (ウィンドウサイズとタイトルを設定)
        pyxel.init(WIN_WIDTH, WIN_HEIGHT, title="Pyxel Platformer")
        # リソースファイル"my_resource.pyxres"をロード
        pyxel.load("my_resource.pyxres")

        # タイルマップの初期化 (全て0で埋める)
        self.tilemap = [[0 for _ in range(WIN_WIDTH // TILE_SIZE)] for _ in range(WIN_HEIGHT // TILE_SIZE)]
        # タイルマップの最下段を1 (床) で初期化
        for i in range(WIN_WIDTH // TILE_SIZE):
            self.tilemap[WIN_HEIGHT // TILE_SIZE - 1][i] = 1
        
        # プレイヤーの初期化
        self.player = Player(WIN_WIDTH // 2 - TILE_SIZE // 2, WIN_HEIGHT // 2 - TILE_SIZE * 2)

        # Pyxelアプリケーションの実行 (updateとdrawメソッドを呼び出し続ける)
        pyxel.run(self.update, self.draw)

    # アプリケーションの状態を更新するメソッド (毎フレーム呼び出される)
    def update(self):
        self.player.update(self.tilemap) # プレイヤーの状態を更新

    # アプリケーションの描画を行うメソッド (毎フレーム呼び出される)
    def draw(self):
        pyxel.cls(0) # 画面をクリア (色0で塗りつぶす)

        # タイルマップの描画
        for y in range(WIN_HEIGHT // TILE_SIZE):
            for x in range(WIN_WIDTH // TILE_SIZE):
                if self.tilemap[y][x] == 1: # タイルの値が1 (床) であれば描画
                    # pyxel.blt(x, y, img, u, v, w, h, [colkey])
                    # x, y: 描画位置 (タイル座標をピクセル座標に変換)
                    # img: 画像バンク番号 (0)
                    # u, v: 画像バンク内の描画開始位置 (1 * TILE_SIZE, 0 * TILE_SIZE) - 床タイルの画像
                    # w, h: 描画する画像の幅と高さ (TILE_SIZE, TILE_SIZE)
                    pyxel.blt(x * TILE_SIZE, y * TILE_SIZE, 0, 1 * TILE_SIZE, 0 * TILE_SIZE, TILE_SIZE, TILE_SIZE)
        
        # プレイヤーを描画
        self.player.draw()

# アプリケーションの開始
App()