import pyxel

# 定数定義
TRANSPARENT_COLOR = 2  # 透明色として扱う色番号 (Pyxelのパレットにおける色番号)
SCROLL_BORDER_X = 80   # プレイヤーが画面端に到達した際にスクロールを開始するX座標の境界
TILE_FLOOR = (1, 0)    # 床タイルを表すタプル (タイルマップの(1,0)の位置にあるタイル)
TILE_SPAWN1 = (0, 1)   # 敵1の出現位置を示すタイル
TILE_SPAWN2 = (1, 1)   # 敵2の出現位置を示すタイル
TILE_SPAWN3 = (2, 1)   # 敵3の出現位置を示すタイル
WALL_TILE_X = 4        # 壁タイルとして扱うタイルマップのX座標の最小値 (これ以上のX座標を持つタイルは壁とみなす)

# グローバル変数
scroll_x = 0  # スクロール量 (カメラのX座標)
player = None # プレイヤーオブジェクト
enemies = []  # 敵オブジェクトのリスト


# 指定されたタイル座標のタイルデータを取得する関数
def get_tile(tile_x, tile_y):
    # pyxel.tilemap(0).pget(tile_x, tile_y) は、タイルマップ0番の(tile_x, tile_y)にあるピクセルデータを取得する
    # タイルマップの各タイルは8x8ピクセルで構成されており、その左上隅のピクセルデータを取得することで、
    # そのタイルがどの画像バンクのどの位置にあるかを示す情報（(u, v)座標）が得られる
    return pyxel.tilemap(0).pget(tile_x, tile_y)


# 衝突を検出する関数
def detect_collision(x, y, dy):
    # エンティティが占めるタイルの座標範囲を計算
    # Pyxelのデフォルトのタイルサイズは8x8ピクセル
    x1 = x // 8  # エンティティの左端が位置するタイルのX座標
    y1 = y // 8  # エンティティの上端が位置するタイルのY座標
    x2 = (x + 8 - 1) // 8 # エンティティの右端が位置するタイルのX座標
    y2 = (y + 8 - 1) // 8 # エンティティの下端が位置するタイルのY座標

    # エンティティが占める可能性のある領域内のソリッドなタイルとの衝突をチェック
    for yi in range(y1, y2 + 1):
        for xi in range(x1, x2 + 1):
            # get_tileで取得したタイルの情報(u, v)のu座標がWALL_TILE_X以上であれば壁とみなす
            if get_tile(xi, yi)[0] >= WALL_TILE_X:
                return True # 衝突が見つかったらTrueを返す

    # 下方向への移動中に床タイルとの衝突をチェック (着地判定)
    # dy > 0 は下方向への移動中、y % 8 == 1 はタイルの境界にいることを示す (Pyxelの座標系による)
    if dy > 0 and y % 8 == 1:
        for xi in range(x1, x2 + 1):
            # エンティティの足元にあるタイルが床タイル(TILE_FLOOR)であれば衝突とみなす
            if get_tile(xi, y1 + 1) == TILE_FLOOR:
                return True
    return False # 衝突がなければFalseを返す


# 衝突したエンティティを押し戻す関数
# x, y: エンティティの現在座標
# dx, dy: エンティティの移動量
def push_back(x, y, dx, dy):
    abs_dx = abs(dx) # X方向の移動量の絶対値
    abs_dy = abs(dy) # Y方向の移動量の絶対値

    # 移動量の大きい軸から衝突判定を行うことで、より正確な押し戻しを実現
    if abs_dx > abs_dy:
        # X方向の押し戻し
        sign = 1 if dx > 0 else -1 # 移動方向 (正:1, 負:-1)
        for _ in range(abs_dx): # X方向の移動量分ループ
            # 1ピクセルずつ移動を試み、衝突したらループを抜ける
            if detect_collision(x + sign, y, dy):
                break
            x += sign # 衝突しなければ移動
        # Y方向の押し戻し
        sign = 1 if dy > 0 else -1
        for _ in range(abs_dy):
            if detect_collision(x, y + sign, dy):
                break
            y += sign
    else:
        # Y方向の押し戻し
        sign = 1 if dy > 0 else -1
        for _ in range(abs_dy):
            if detect_collision(x, y + sign, dy):
                break
            y += sign
        # X方向の押し戻し
        sign = 1 if dx > 0 else -1
        for _ in range(abs_dx):
            if detect_collision(x + sign, y, dy):
                break
            x += sign
    return x, y, dx, dy # 押し戻し後の座標と移動量を返す


# 指定されたピクセル座標が壁かどうかを判定する関数
def is_wall(x, y):
    # ピクセル座標をタイル座標に変換
    tile_x = x // 8
    tile_y = y // 8

    # 前景レイヤーのタイルをチェック
    tile = get_tile(tile_x, tile_y)
    if tile == TILE_FLOOR or tile[0] >= WALL_TILE_X:
        return True

    # 背景レイヤーのタイルをチェック
    # pyxel.bltmのv=128に対応するため、タイルY座標に16を加算
    # 背景の床も前景と同じTILE_FLOORと仮定
    bg_tile = get_tile(tile_x, tile_y + 16)
    if bg_tile == TILE_FLOOR:
        return True

    return False


# 敵を生成する関数
# left_x, right_x: 敵を生成するX座標の範囲 (ピクセル単位)
def spawn_enemy(left_x, right_x):
    # ピクセル座標をタイル座標に変換
    left_x = pyxel.ceil(left_x / 8) # 左端のタイルX座標 (切り上げ)
    right_x = pyxel.floor(right_x / 8) # 右端のタイルX座標 (切り捨て)

    # 指定された範囲のタイルを走査し、敵の出現タイルがあれば敵を生成
    for x in range(left_x, right_x + 1):
        for y in range(16): # Y座標は0から15まで (タイルマップの高さ)
            tile = get_tile(x, y) # タイル情報を取得
            if tile == TILE_SPAWN1: # TILE_SPAWN1であればEnemy1を生成
                enemies.append(Enemy1(x * 8, y * 8))
            elif tile == TILE_SPAWN2: # TILE_SPAWN2であればEnemy2を生成
                enemies.append(Enemy2(x * 8, y * 8))
            elif tile == TILE_SPAWN3: # TILE_SPAWN3であればEnemy3を生成
                enemies.append(Enemy3(x * 8, y * 8))


# リストからis_aliveがFalseの要素を削除する関数
def cleanup_list(list):
    i = 0
    while i < len(list):
        elem = list[i]
        if elem.is_alive: # 生存していれば次の要素へ
            i += 1
        else: # 生存していなければリストから削除
            list.pop(i)


class Player:
    # プレイヤーの初期化
    def __init__(self, x, y):
        self.x = x # X座標
        self.y = y # Y座標
        self.dx = 0 # X方向の速度
        self.dy = 0 # Y方向の速度
        self.direction = 1 # 向き (1:右, -1:左)
        self.is_falling = False # 落下中かどうか

    # プレイヤーの状態を更新するメソッド
    def update(self):
        global scroll_x # グローバル変数scroll_xを使用
        last_y = self.y # 更新前のY座標を保存

        # 左右移動の入力処理
        if pyxel.btn(pyxel.KEY_LEFT):
            self.dx = -2
            self.direction = -1
        if pyxel.btn(pyxel.KEY_RIGHT):
            self.dx = 2
            self.direction = 1

        # 重力による落下速度の更新 (最大速度3)
        self.dy = min(self.dy + 1, 3)

        # ジャンプの入力処理
        if pyxel.btnp(pyxel.KEY_SPACE):
            self.dy = -6 # 上向きに速度を設定
            pyxel.play(3, 8) # ジャンプ音を再生

        # 衝突判定と押し戻し処理
        self.x, self.y, self.dx, self.dy = push_back(self.x, self.y, self.dx, self.dy)

        # 画面左端と上端の境界処理
        if self.x < scroll_x:
            self.x = scroll_x
        if self.y < 0:
            self.y = 0

        # 摩擦によるX方向の速度減衰
        self.dx = int(self.dx * 0.8)

        # 落下中かどうかの判定
        self.is_falling = self.y > last_y

        # 画面スクロール処理
        if self.x > scroll_x + SCROLL_BORDER_X:
            last_scroll_x = scroll_x
            # プレイヤーが画面右端の境界を超えたらスクロール
            # スクロール量は最大240 * 8 (タイルマップの幅) まで
            scroll_x = min(self.x - SCROLL_BORDER_X, 240 * 8)
            # 新しくスクロールされた範囲に敵を生成
            spawn_enemy(last_scroll_x + 128, scroll_x + 127)

    # プレイヤーを描画するメソッド
    def draw(self):
        # プレイヤーのアニメーションフレームを計算
        # 落下中は常に特定のフレーム、それ以外は歩行アニメーション
        u = (2 if self.is_falling else pyxel.frame_count // 3 % 2) * 8
        # プレイヤーの向きに応じて画像を反転させるための幅 (w)
        w = 8 if self.direction > 0 else -8
        # pyxel.blt(x, y, img, u, v, w, h, colkey)
        # x, y: 描画位置
        # img: 画像バンク番号 (0)
        # u, v: 画像バンク内の描画開始位置 (uは計算されたアニメーションフレーム、vは16)
        # w, h: 描画する画像の幅と高さ (wは向きに応じて反転、hは8)
        # colkey: 透明色 (TRANSPARENT_COLOR)
        pyxel.blt(self.x, self.y, 0, u, 16, w, 8, TRANSPARENT_COLOR)


class Enemy1:
    # 敵1の初期化
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.dx = 0
        self.dy = 0
        self.direction = -1 # 初期方向は左
        self.is_alive = True # 生存フラグ

    # 敵1の状態を更新するメソッド
    def update(self):
        self.dx = self.direction # 移動方向を設定
        self.dy = min(self.dy + 1, 3) # 重力による落下速度の更新

        # 壁の検出と方向転換
        # 左に進んでいて、左に壁がある場合、または右に進んでいて右に壁がある場合
        if self.direction < 0 and is_wall(self.x - 1, self.y + 4): # 左に壁があるか
            self.direction = 1 # 右に方向転換
        elif self.direction > 0 and is_wall(self.x + 8, self.y + 4): # 右に壁があるか
            self.direction = -1 # 左に方向転換

        # 衝突判定と押し戻し処理
        self.x, self.y, self.dx, self.dy = push_back(self.x, self.y, self.dx, self.dy)

    # 敵1を描画するメソッド
    def draw(self):
        # アニメーションフレームを計算
        u = pyxel.frame_count // 4 % 2 * 8
        # 向きに応じて画像を反転
        w = 8 if self.direction > 0 else -8
        # 敵1の描画 (画像バンク0、uはアニメーションフレーム、vは24)
        pyxel.blt(self.x, self.y, 0, u, 24, w, 8, TRANSPARENT_COLOR)


class Enemy2:
    # 敵2の初期化
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.dx = 0
        self.dy = 0
        self.direction = 1 # 初期方向は右
        self.is_alive = True

    # 敵2の状態を更新するメソッド
    def update(self):
        self.dx = self.direction
        self.dy = min(self.dy + 1, 3)

        # 足元に壁があるか、または足元が途切れている場合の方向転換
        if is_wall(self.x, self.y + 8) or is_wall(self.x + 7, self.y + 8):
            # 左に進んでいて、左に壁があるか、または左の足元が途切れている場合
            if self.direction < 0 and (
                is_wall(self.x - 1, self.y + 4) or not is_wall(self.x - 1, self.y + 8)
            ):
                self.direction = 1 # 右に方向転換
            # 右に進んでいて、右に壁があるか、または右の足元が途切れている場合
            elif self.direction > 0 and (
                is_wall(self.x + 8, self.y + 4) or not is_wall(self.x + 7, self.y + 8)
            ):
                self.direction = -1 # 左に方向転換
        self.x, self.y, self.dx, self.dy = push_back(self.x, self.y, self.dx, self.dy)

    # 敵2を描画するメソッド
    def draw(self):
        # アニメーションフレームを計算 (Enemy1とは異なる画像を使用)
        u = pyxel.frame_count // 4 % 2 * 8 + 16
        # 向きに応じて画像を反転
        w = 8 if self.direction > 0 else -8
        # 敵2の描画 (画像バンク0、uはアニメーションフレーム、vは24)
        pyxel.blt(self.x, self.y, 0, u, 24, w, 8, TRANSPARENT_COLOR)


class Enemy3:
    # 敵3の初期化
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.time_to_fire = 0 # 弾を発射するまでの時間
        self.is_alive = True

    # 敵3の状態を更新するメソッド
    def update(self):
        self.time_to_fire -= 1 # 発射までの時間を減らす
        if self.time_to_fire <= 0: # 発射時間になったら
            dx = player.x - self.x # プレイヤーとのX方向の距離
            dy = player.y - self.y # プレイヤーとのY方向の距離
            sq_dist = dx * dx + dy * dy # プレイヤーとの距離の2乗
            if sq_dist < 60 ** 2: # プレイヤーが一定範囲内 (60ピクセル以内) にいれば
                dist = pyxel.sqrt(sq_dist) # 距離を計算
                # プレイヤーに向かって弾を発射
                enemies.append(Enemy3Bullet(self.x, self.y, dx / dist, dy / dist))
                self.time_to_fire = 60 # 次の発射までの時間をリセット (60フレーム = 1秒)

    # 敵3を描画するメソッド
    def draw(self):
        # アニメーションフレームを計算
        u = pyxel.frame_count // 8 % 2 * 8
        # 敵3の描画 (画像バンク0、uはアニメーションフレーム、vは32)
        pyxel.blt(self.x, self.y, 0, u, 32, 8, 8, TRANSPARENT_COLOR)


class Enemy3Bullet:
    # 敵3の弾の初期化
    def __init__(self, x, y, dx, dy):
        self.x = x
        self.y = y
        self.dx = dx # X方向の速度
        self.dy = dy # Y方向の速度
        self.is_alive = True # 生存フラグ

    # 弾の状態を更新するメソッド
    def update(self):
        self.x += self.dx # X座標を更新
        self.y += self.dy # Y座標を更新

    # 弾を描画するメソッド
    def draw(self):
        # アニメーションフレームを計算
        u = pyxel.frame_count // 2 % 2 * 8 + 16
        # 弾の描画 (画像バンク0、uはアニメーションフレーム、vは32)
        pyxel.blt(self.x, self.y, 0, u, 32, 8, 8, TRANSPARENT_COLOR)


class App:
    # アプリケーションの初期化
    def __init__(self):
        # Pyxelの初期化 (ウィンドウサイズ128x128、タイトル"Pyxel Platformer")
        pyxel.init(128, 128, title="Pyxel Platformer")
        # リソースファイル"assets/platformer.pyxres"をロード
        pyxel.load("assets/platformer.pyxres")

        # 敵の出現タイルを透明にする (ゲーム中に見えないようにする)
        # pyxel.image(0).rect(x, y, w, h, col)
        # 画像バンク0の(0, 8)から幅24、高さ8の範囲を透明色で塗りつぶす
        pyxel.image(0).rect(0, 8, 24, 8, TRANSPARENT_COLOR)

        global player # グローバル変数playerを使用
        player = Player(0, 0) # プレイヤーを初期位置(0,0)に生成
        spawn_enemy(0, 127) # 初期画面に敵を生成
        pyxel.playm(0, loop=True) # BGMをループ再生
        # Pyxelアプリケーションの実行 (updateとdrawメソッドを呼び出し続ける)
        pyxel.run(self.update, self.draw)

    # アプリケーションの状態を更新するメソッド (毎フレーム呼び出される)
    def update(self):
        # Qキーが押されたらアプリケーションを終了
        if pyxel.btn(pyxel.KEY_Q):
            pyxel.quit()

        player.update() # プレイヤーの状態を更新

        # 敵の更新とプレイヤーとの衝突判定
        for enemy in enemies:
            # プレイヤーと敵の距離が一定以下であればゲームオーバー
            if abs(player.x - enemy.x) < 6 and abs(player.y - enemy.y) < 6:
                game_over() # ゲームオーバー処理を呼び出し
                return # update処理を終了
            enemy.update() # 敵の状態を更新
            # 敵が画面外に出たら生存フラグをFalseにする
            if enemy.x < scroll_x - 8 or enemy.x > scroll_x + 160 or enemy.y > 160:
                enemy.is_alive = False
        cleanup_list(enemies) # 生存していない敵をリストから削除

    # アプリケーションの描画を行うメソッド (毎フレーム呼び出される)
    def draw(self):
        pyxel.cls(0) # 画面をクリア (色0で塗りつぶす)

        # レベルの描画
        pyxel.camera() # カメラをリセット (スクロールしない状態)
        # 背景レイヤーの描画 (視差効果のためにスクロール量を調整)
        pyxel.bltm(0, 0, 0, (scroll_x // 4) % 128, 128, 128, 128)
        # メインのタイルマップの描画
        # pyxel.bltm(x, y, tm, u, v, w, h, colkey)
        # x, y: 描画位置
        # tm: タイルマップ番号 (0)
        # u, v: タイルマップ内の描画開始位置 (scroll_x, 0)
        # w, h: 描画する範囲の幅と高さ (128, 128)
        # colkey: 透明色 (TRANSPARENT_COLOR)
        pyxel.bltm(0, 0, 0, scroll_x, 0, 128, 128, TRANSPARENT_COLOR)

        # キャラクターの描画
        pyxel.camera(scroll_x, 0) # カメラをスクロール量に合わせて設定
        player.draw() # プレイヤーを描画
        for enemy in enemies:
            enemy.draw() # 敵を描画


# ゲームオーバー時の処理
def game_over():
    global scroll_x, enemies # グローバル変数scroll_xとenemiesを使用
    scroll_x = 0 # スクロール量をリセット
    player.x = 0 # プレイヤーのX座標をリセット
    player.y = 0 # プレイヤーのY座標をリセット
    player.dx = 0 # プレイヤーのX速度をリセット
    player.dy = 0 # プレイヤーのY速度をリセット
    enemies = [] # 敵リストをクリア
    spawn_enemy(0, 127) # 新しい敵を生成
    pyxel.play(3, 9) # ゲームオーバー音を再生


# アプリケーションの開始
App()
