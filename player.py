import pyxel
from typing import Tuple

# ゲーム定数
TILE_SIZE = 8
SPRITE_SIZE = 8
ANIMATION_SPEED = 4
ANIMATION_FRAMES = 3

# 方向定数
DIR_RIGHT = 0
DIR_LEFT = 1
DIR_UP = 2
DIR_DOWN = 3

# スプライト座標定数
SPRITE_Y_OFFSET = 72
SPR_RIGHT = 0
SPR_DOWN = 24
SPR_UP = 48

NOT_FLOOR = 0
ON_FLOOR = 1
ON_THROUGH_FLOOR = 2

# タイル定数
WALL_TILE_X = 4
TILE_FLOOR = (1, 0) #ジャンプで通り抜けられる床のイメージ座標

#"""入力処理を担当するクラス"""
class InputHandler:
    
    @staticmethod
    def get_movement_input(is_on_ground: bool) -> Tuple[int, int, int, bool]:
        """キー入力から移動方向と向きを取得。ジャンプ入力も返す"""
        dx:int = 0
        direction:int = None
        jump:bool = False
        
        if pyxel.btn(pyxel.KEY_LEFT):
            dx, direction = -1, DIR_LEFT
        elif pyxel.btn(pyxel.KEY_RIGHT):
            dx, direction = 1, DIR_RIGHT
        # 上下移動は無効化
        # ジャンプ入力
        if is_on_ground and pyxel.btnp(pyxel.KEY_SPACE):
            jump = True
        return dx, direction, jump

#"""衝突判定を担当するクラス"""
class CollisionDetector:
    
    @staticmethod
    def get_tile(tile_x: int, tile_y: int) -> Tuple[int, int]:
        """タイル情報を取得"""
        return pyxel.tilemap(0).pget(tile_x, tile_y)
    
    @staticmethod
    def detect_collision(x: int, y: int, y_vector: int) -> bool:
        """衝突を検出"""
        x1:int = x // TILE_SIZE
        y1:int = y // TILE_SIZE
        x2:int = (x + SPRITE_SIZE - 1) // TILE_SIZE
        y2:int = (y + SPRITE_SIZE - 1) // TILE_SIZE

        # 壁との衝突判定
        for yi in range(y1, y2 + 1):
            for xi in range(x1, x2 + 1):
                fg_tile_u = CollisionDetector.get_tile(xi, yi)[0]
                if fg_tile_u >= WALL_TILE_X:
                    return True
        
        # フロアすり抜け判定
        if y_vector > 0 and y % TILE_SIZE == 1:
            for xi in range(x1, x2 + 1):
                if CollisionDetector.get_tile(xi, y1 + 1) == TILE_FLOOR:
                    return True
        return False

#"""移動処理を担当するクラス"""
class MovementHandler:
    
    @staticmethod
    def push_back(x: int, y: int, dx: int, dy: int) -> Tuple[int, int, int, int]:
        """衝突時の押し戻し処理"""
        abs_dx:int = abs(dx)
        abs_dy:int = abs(dy)

        # 移動量の大きい軸から衝突判定を行う
        if abs_dx > abs_dy:
            x = MovementHandler._push_back_x(x, y, dx, dy)
            y = MovementHandler._push_back_y(x, y, dx, dy)
        else:
            y = MovementHandler._push_back_y(x, y, dx, dy)
            x = MovementHandler._push_back_x(x, y, dx, dy)
            
        return x, y, dx, dy
    
    @staticmethod
    def _push_back_x(x: int, y: int, dx: int, dy: int) -> int:
        """X方向の押し戻し"""
        if dx == 0:
            return x
            
        sign:int = 1 if dx > 0 else -1
        for _ in range(abs(dx)):
            if CollisionDetector.detect_collision(x + sign, y, dy):
                break
            x += sign
        return x
    
    @staticmethod
    def _push_back_y(x: int, y: int, dx: int, dy: int) -> int:
        """Y方向の押し戻し"""
        if dy == 0:
            return y
            
        sign:int = 1 if dy > 0 else -1
        for _ in range(abs(dy)):
            if CollisionDetector.detect_collision(x, y + sign, dy):
                break
            y += sign
        return y

#"""スプライト描画を担当するクラス"""
class SpriteRenderer:
    
    @staticmethod
    def get_sprite_coordinates(direction: int) -> Tuple[int, int]:
        """方向に応じたスプライト座標を取得"""
        SprBaseidx_X:int = 0    #スプライト描画開始座標
        horizon_flip:int = 1    #左右反転
        
        if direction == DIR_RIGHT:
            SprBaseidx_X = SPR_RIGHT
        elif direction == DIR_LEFT:
            SprBaseidx_X = SPR_RIGHT
            horizon_flip = -1
        elif direction == DIR_DOWN:
            SprBaseidx_X = SPR_DOWN
        elif direction == DIR_UP:
            SprBaseidx_X = SPR_UP
            
        # アニメーション用のオフセット計算
        animation_offset = (pyxel.frame_count // ANIMATION_SPEED % ANIMATION_FRAMES) * SPRITE_SIZE
        return SprBaseidx_X + animation_offset, horizon_flip 
        # u = SprBaseidx_X + animation_offset
        
        # return u, horizon_flip

#    """プレイヤーを表すクラス"""
class Player:
    
    def __init__(self, x: int, y: int):
        self.x: int = x
        self.y: int = y
        self.dx: int = 0
        self.dy: int = 0
        self.direction: int = DIR_RIGHT
        self.is_on_ground: bool = False
        # ジャンプ関連
        self.jump_count: int = 0
        self.max_jumps: int = 1  # 2や3にすれば多段ジャンプ化できる
        self.jump_start_y: int = 0
        self.max_jump_height: int = (8 * 3)  # 3タイル分がジャンプ最大高さ　
        self.is_jumping: bool = False
        self.skip_jump = False  # すり抜けアクション時ジャンプ禁止
        # 各処理を担当するクラスのインスタンス
        self.input_handler = InputHandler()
        self.movement_handler = MovementHandler()
        self.renderer = SpriteRenderer()

    def get_floor_state(self):
        tile_x = self.x // TILE_SIZE
        tile_y = (self.y + SPRITE_SIZE) // TILE_SIZE
        tile = CollisionDetector.get_tile(tile_x, tile_y)
        if tile == TILE_FLOOR:
            return ON_THROUGH_FLOOR
        elif tile[0] >= WALL_TILE_X:
            return ON_FLOOR
        else:
            return NOT_FLOOR

    def update(self):
        """プレイヤーの状態を更新（ジャンプ高さ3ブロック制限、将来多段ジャンプ拡張可）"""
        # 足元の床状態を毎フレーム取得
        self.floor_state = self.get_floor_state()
        # 地面判定
        was_on_ground = self.is_on_ground
        self.is_on_ground = CollisionDetector.detect_collision(self.x, self.y + 1, 1)
        # すり抜け床の上で下＋ジャンプキーで特殊アクション
        if self.is_on_ground and self.floor_state == ON_THROUGH_FLOOR:
            if pyxel.btn(pyxel.KEY_DOWN) and pyxel.btnp(pyxel.KEY_SPACE):
                #print("Through!!")
                self.y += 1  # すり抜け可能床を下に降りる
                self.skip_jump = True
        # 着地したらジャンプ回数リセット
        if self.is_on_ground and not was_on_ground:
            self.jump_count = 0
            self.is_jumping = False
        # 入力処理
        dx, direction, jump = self.input_handler.get_movement_input(self.is_on_ground or (self.jump_count < self.max_jumps))
        if direction is not None:
            self.direction = direction
        # 左右移動
        self.dx = dx * 2  # 移動速度2
        # ジャンプ開始
        if jump and not self.skip_jump and (self.is_on_ground or self.jump_count < self.max_jumps):
            if not self.is_jumping:
                self.jump_start_y = self.y
                self.is_jumping = True
                self.jump_count += 1
            # ジャンプ中かつ高さ制限内なら上昇
            if self.is_jumping and (self.jump_start_y - self.y < self.max_jump_height):
                self.dy = -7
        # ジャンプボタンを離したら上昇終了
        if not pyxel.btn(pyxel.KEY_SPACE):
            self.is_jumping = False
        # 重力
        self.dy = min(self.dy + 1, 3) if self.dy < 3 else self.dy
        # 移動処理（衝突判定と押し戻し含む）
        self.x, self.y, self.dx, self.dy = self.movement_handler.push_back(
            self.x, self.y, self.dx, self.dy
        )
        # 地面に着地したらdyを0に
        if self.is_on_ground and self.dy > 0:
            self.dy = 0
        # updateの最後でskip_jumpをリセット
        self.skip_jump = False

    def draw(self):
        """プレイヤーを描画"""
        Spr_x_Offset, horizon_flip = self.renderer.get_sprite_coordinates(self.direction)
        
        pyxel.blt(
            self.x, self.y, 0, 
            Spr_x_Offset, SPRITE_Y_OFFSET, 
            SPRITE_SIZE * horizon_flip, SPRITE_SIZE, 
            0  # 透明色
        ) 