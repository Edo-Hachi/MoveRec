# coding: utf-8
# コーディングルール:
# - すべての変数・関数・戻り値に型アノテーションを必ず付与すること
# - 定数宣言時は"HOGHOGE"のような文字列は使わない。必ず HOGEHOGE = 1 みたいに宣言する。たくさんある時は enum にする
# - 1関数につき30行以内を目安に分割
# - コメントは日本語で記述
# - 関数宣言したら、関数の機能、引数がある時は引数名と、なんの値を受け取っているかをコメントで書く

import pyxel
from typing import Tuple
from enum import Enum, auto

# === 定数 ===
TILE_SIZE = 8
SPRITE_SIZE = 8
ANIMATION_SPEED = 4
ANIMATION_FRAMES = 3

# スクロール関連定数
SCROLL_BORDER_X = 80   # プレイヤーが画面端に到達した際にスクロールを開始するX座標の境界
TILEMAP_WIDTH = 240    # タイルマップの幅（タイル単位）
MAX_SCROLL_X = TILEMAP_WIDTH * TILE_SIZE  # 最大スクロール量

# 方向定数（Enum化）
class Direction(Enum):
    RIGHT = 0
    LEFT = 1
    UP = 2
    DOWN = 3

# 床状態定数（Enum化）
class FloorState(Enum):
    NOT_FLOOR = 0      # 床がない状態（空中）
    ON_FLOOR = 1       # 通常の床の上にいる状態
    ON_THROUGH_FLOOR = 2  # すり抜け床の上にいる状態

# スプライト座標定数
SPRITE_Y_OFFSET = 72
SPR_RIGHT = 0
SPR_DOWN = 24
SPR_UP = 48

# タイル定数
WALL_TILE_X = 4 #乗っかれる壁床タイルタイプ
TILE_FLOOR = (1, 0)  # ジャンプで通り抜けられる床のイメージ座標

# プレイヤーの足元の当たり判定オフセット（左右の端から内側に何ピクセル狭めるか）
FOOT_COLLISION_INSET_LEFT = 0   # 足元判定の左端オフセット（0ならスプライトの左端）
FOOT_COLLISION_INSET_RIGHT = 0  # 足元判定の右端オフセット（0ならスプライトの右端）

# === カメラ・スクロール管理 ===
class CameraManager:
    # カメラのスクロール処理を管理するクラス
    def __init__(self):
        # カメラの初期化。スクロール量を0で開始。
        self.scroll_x: int = 0

    def update_scroll(self, player_x: int) -> None:
        # プレイヤーの位置に基づいてスクロール量を更新
        # player_x: プレイヤーのX座標
        if player_x > self.scroll_x + SCROLL_BORDER_X:
            # プレイヤーが画面右端の境界を超えたらスクロール
            self.scroll_x = min(player_x - SCROLL_BORDER_X, MAX_SCROLL_X)
        elif player_x < self.scroll_x + SCROLL_BORDER_X // 2:
            # プレイヤーが画面左端の境界を超えたらスクロール（左方向）
            # 左端の境界は右端の半分の位置（SCROLL_BORDER_X // 2）に設定
            self.scroll_x = max(player_x - SCROLL_BORDER_X // 2, 0)

    def get_scroll_x(self) -> int:
        # 現在のスクロール量を取得
        return self.scroll_x

    def set_camera(self) -> None:
        # Pyxelのカメラをスクロール位置に設定
        pyxel.camera(self.scroll_x, 0)

    def reset_camera(self) -> None:
        # Pyxelのカメラをリセット（スクロールしない状態）
        pyxel.camera()

# === 衝突判定 ===
class CollisionDetector:
    @staticmethod
    def get_tile(tile_x: int, tile_y: int) -> Tuple[int, int]:
        """
        指定したタイル座標(tile_x, tile_y)のタイル情報（画像バンク上の(u, v)座標）を取得する関数。
        - tile_x: タイルマップ上のX座標（タイル単位）
        - tile_y: タイルマップ上のY座標（タイル単位）
        戻り値: (u, v) タイル画像の座標タプル
        """
        return pyxel.tilemap(0).pget(tile_x, tile_y)

    @staticmethod
    def detect_collision(x: int, y: int, y_vector: int) -> bool:
        """
        指定した座標範囲に壁や床が存在するかを判定する関数。
        - x, y: 判定したいスプライトの左上座標（ピクセル単位）
        - y_vector: Y方向の移動量（下方向の判定時に床タイルも考慮するために使用）
        戻り値: 壁や床に衝突していればTrue、何もなければFalse
        
        スプライトの左上(x, y)から右下(x+SPRITE_SIZE-1, y+SPRITE_SIZE-1)までの範囲、
        もしくは足元の中心付近だけをタイル単位で走査し、
        ・壁タイル（WALL_TILE_X以上）
        ・床タイル（TILE_FLOOR）
        に当たるかどうかを判定する。
        """
        x1 = (x + 1) // TILE_SIZE
        y1 = y // TILE_SIZE
        x2 = (x + SPRITE_SIZE - 2) // TILE_SIZE
        y2 = (y + SPRITE_SIZE - 1) // TILE_SIZE
        for yi in range(y1, y2 + 1):
            for xi in range(x1, x2 + 1):
                fg_tile_u = CollisionDetector.get_tile(xi, yi)[0]
                if fg_tile_u >= WALL_TILE_X:
                    return True
        if y_vector > 0 and y % TILE_SIZE == 1:
            for xi in range(x1, x2 + 1):
                if CollisionDetector.get_tile(xi, y1 + 1) == TILE_FLOOR:
                    return True
        return False

# === 移動処理 ===
class MovementHandler:
    def __init__(self, camera_manager: 'CameraManager'):
        # 移動処理の初期化。カメラマネージャーの参照を保持。
        # camera_manager: カメラマネージャーのインスタンス
        self.camera_manager: CameraManager = camera_manager

    def push_back(self, x: int, y: int, dx: int, dy: int) -> Tuple[int, int, int, int]:
        abs_dx = abs(dx)
        abs_dy = abs(dy)
        if abs_dx > abs_dy:
            x = self._push_back_x(x, y, dx, dy)
            y = self._push_back_y(x, y, dx, dy)
        else:
            y = self._push_back_y(x, y, dx, dy)
            x = self._push_back_x(x, y, dx, dy)
        
        # 画面左端の境界処理（マップの開始位置で制限）
        if x < 0:
            x = 0
        
        return x, y, dx, dy

    def _push_back_x(self, x: int, y: int, dx: int, dy: int) -> int:
        if dx == 0:
            return x
        sign = 1 if dx > 0 else -1
        for _ in range(abs(dx)):
            if CollisionDetector.detect_collision(x + sign, y, dy):
                break
            x += sign
        return x

    def _push_back_y(self, x: int, y: int, dx: int, dy: int) -> int:
        if dy == 0:
            return y
        sign = 1 if dy > 0 else -1
        for _ in range(abs(dy)):
            if CollisionDetector.detect_collision(x, y + sign, dy):
                break
            y += sign
        return y

# === スプライト描画 ===
class SpriteRenderer:
    SPRITE_INFO = {
        Direction.RIGHT: (SPR_RIGHT, 1),
        Direction.LEFT: (SPR_RIGHT, -1),
        Direction.DOWN: (SPR_DOWN, 1),
        Direction.UP: (SPR_UP, 1),
    }

    @staticmethod
    def get_sprite_coordinates(direction: Direction) -> Tuple[int, int]:
        """
        指定された向き(direction)に応じたスプライト画像のX座標オフセットと、
        左右反転フラグ（horizon_flip）を計算して返す関数。
        - direction: プレイヤーの向き（Direction列挙型）
        戻り値: (スプライト画像のX座標, 左右反転フラグ)
        歩行アニメーションのフレームも考慮し、アニメーションオフセットを加算する。
        """
        SprBaseidx_X = 0
        horizon_flip = 1
        if direction == Direction.RIGHT:
            SprBaseidx_X = SPR_RIGHT
        elif direction == Direction.LEFT:
            SprBaseidx_X = SPR_RIGHT
            horizon_flip = -1
        elif direction == Direction.DOWN:
            SprBaseidx_X = SPR_DOWN
        elif direction == Direction.UP:
            SprBaseidx_X = SPR_UP
        animation_offset = (pyxel.frame_count // ANIMATION_SPEED % ANIMATION_FRAMES) * SPRITE_SIZE
        return SprBaseidx_X + animation_offset, horizon_flip

# === プレイヤークラス ===
class Player:
    # プレイヤーキャラクターの状態と動作を管理するクラス
    def __init__(self, x: int, y: int, camera_manager: CameraManager):
        # Playerの初期化処理。位置・速度・状態変数の初期化。
        # x: 初期X座標
        # y: 初期Y座標
        # camera_manager: カメラマネージャーのインスタンス
        self.x: int = x  # プレイヤーのX座標
        self.y: int = y  # プレイヤーのY座標
        self.dx: int = 0  # プレイヤーのX方向速度
        self.dy: int = 0  # プレイヤーのY方向速度
        self.direction: Direction = Direction.RIGHT  # プレイヤーの向き
        self.is_on_ground: bool = False  # 地面に接しているかどうか
        self.jump_count: int = 0  # ジャンプ回数（多段ジャンプ用）
        self.max_jumps: int = 1  # 最大ジャンプ回数
        self.jump_start_y: int = 0  # ジャンプ開始時のY座標
        self.max_jump_height: int = 8 * 3  # 最大ジャンプ高さ（ピクセル）
        self.is_jumping: bool = False  # ジャンプ中かどうか
        self.skip_jump: bool = False  # すり抜け床でジャンプをスキップするフラグ
        self.floor_state: FloorState = FloorState.NOT_FLOOR  # 足元の床状態
        self.was_on_ground: bool = False  # 1フレーム前に地面にいたか
        self._jump_input: bool = False  # 今フレームでジャンプ入力があったか
        self.camera_manager: CameraManager = camera_manager  # カメラ管理インスタンス
        self.movement_handler: MovementHandler = MovementHandler(camera_manager)  # 移動処理インスタンス
        self.renderer: SpriteRenderer = SpriteRenderer()  # スプライト描画インスタンス
        self.coyote_timer: int = 0  # コヨーテタイム用カウンタ（地面を離れてからジャンプ可能な残りフレーム数）
        self.COYOTE_TIME_MAX: int = 3  # コヨーテタイム最大値（地面を離れてからジャンプ可能な最大フレーム数）

    def _get_floor_state(self) -> FloorState:
        # プレイヤーの足元の床状態を取得する
        start_tile_x: int = (self.x + FOOT_COLLISION_INSET_LEFT) // TILE_SIZE
        end_tile_x: int = (self.x + SPRITE_SIZE - 1 - FOOT_COLLISION_INSET_RIGHT) // TILE_SIZE
        tile_y: int = (self.y + SPRITE_SIZE) // TILE_SIZE

        # 左足から右足までのタイルをチェック
        for tile_x in range(start_tile_x, end_tile_x + 1):
            tile: Tuple[int, int] = CollisionDetector.get_tile(tile_x, tile_y)
            
            if tile == TILE_FLOOR:
                return FloorState.ON_THROUGH_FLOOR
            elif tile[0] >= WALL_TILE_X:
                return FloorState.ON_FLOOR

        return FloorState.NOT_FLOOR

    def update(self) -> None:
        # プレイヤーの状態を更新（ジャンプ・移動・床すり抜け等）
        self._update_floor_state()
        # コヨーテタイム処理
        if self.is_on_ground:
            self.coyote_timer = self.COYOTE_TIME_MAX
        else:
            self.coyote_timer = max(self.coyote_timer - 1, 0)
        self._handle_through_floor_action()
        self._handle_landing_reset()
        self._handle_input_and_movement()
        self._handle_jump()
        self._handle_gravity_and_move()
        self._handle_boundary_limits()
        # スクロール処理を更新
        self.camera_manager.update_scroll(self.x)
        self.skip_jump = False

    def _update_floor_state(self) -> None:
        # 足元の床状態・地面判定を更新
        self.was_on_ground = self.is_on_ground
        self.floor_state = self._get_floor_state()
        self.is_on_ground = CollisionDetector.detect_collision(self.x, self.y + 1, 1)

    def _handle_through_floor_action(self) -> None:
        # すり抜け床の上で下＋ジャンプキーで下に降りる処理
        if self.is_on_ground and self.floor_state == FloorState.ON_THROUGH_FLOOR:
            if pyxel.btn(pyxel.KEY_DOWN) and pyxel.btnp(pyxel.KEY_SPACE):
                self.y += 1
                self.skip_jump = True

    def _handle_landing_reset(self) -> None:
        # 着地時にジャンプ状態をリセット
        if self.is_on_ground and not self.was_on_ground:
            self.jump_count = 0
            self.is_jumping = False

    def _handle_input_and_movement(self) -> None:
        # 入力取得・左右移動処理
        dx: int
        direction: Direction | None
        jump: bool
        dx, direction, jump = self._get_movement_input(self.is_on_ground or (self.jump_count < self.max_jumps))
        if direction is not None:
            self.direction = direction
        self.dx = dx * 2
        self._jump_input = jump

    def _handle_jump(self) -> None:
        # ジャンプ処理
        if self._jump_input and not self.skip_jump and (self.is_on_ground or self.coyote_timer > 0):
            if not self.is_jumping:
                self.jump_start_y = self.y
                self.is_jumping = True
                self.jump_count += 1
            if self.is_jumping and (self.jump_start_y - self.y < self.max_jump_height):
                self.dy = -7
        if not pyxel.btn(pyxel.KEY_SPACE):
            self.is_jumping = False

    def _handle_gravity_and_move(self) -> None:
        # 重力・移動・押し戻し処理
        self.dy = min(self.dy + 1, 3) if self.dy < 3 else self.dy
        self.x, self.y, self.dx, self.dy = self.movement_handler.push_back(
            self.x, self.y, self.dx, self.dy
        )
        if self.is_on_ground and self.dy > 0:
            self.dy = 0

    def _handle_boundary_limits(self) -> None:
        # 画面上端の境界処理
        if self.y < 0:
            self.y = 0

    def _get_movement_input(self, is_on_ground: bool) -> Tuple[int, Direction | None, bool]:
        # 入力取得（左右移動・ジャンプ）
        # is_on_ground: 地面にいるかどうか
        dx: int = 0
        direction: Direction | None = None
        jump: bool = False
        if pyxel.btn(pyxel.KEY_LEFT):
            dx, direction = -1, Direction.LEFT
        elif pyxel.btn(pyxel.KEY_RIGHT):
            dx, direction = 1, Direction.RIGHT
        if is_on_ground and pyxel.btnp(pyxel.KEY_SPACE):
            jump = True
        return dx, direction, jump

    def draw(self) -> None:
        # プレイヤーを描画
        Spr_x_Offset: int
        horizon_flip: int
        Spr_x_Offset, horizon_flip = self.renderer.get_sprite_coordinates(self.direction)
        pyxel.blt(
            self.x, self.y, 0,
            Spr_x_Offset, SPRITE_Y_OFFSET,
            SPRITE_SIZE * horizon_flip, SPRITE_SIZE,
            0
        )

    def get_camera_manager(self) -> CameraManager:
        # カメラマネージャーを取得
        return self.camera_manager
    