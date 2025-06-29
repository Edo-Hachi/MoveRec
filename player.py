import pyxel
from typing import Tuple
from enum import Enum, auto

# === 定数 ===
TILE_SIZE = 8
SPRITE_SIZE = 8
ANIMATION_SPEED = 4
ANIMATION_FRAMES = 3

# 方向定数（Enum化）
class Direction(Enum):
    RIGHT = 0
    LEFT = 1
    UP = 2
    DOWN = 3

# スプライト座標定数
SPRITE_Y_OFFSET = 72
SPR_RIGHT = 0
SPR_DOWN = 24
SPR_UP = 48

# 床判定定数
NOT_FLOOR = 0
ON_FLOOR = 1
ON_THROUGH_FLOOR = 2

# タイル定数
WALL_TILE_X = 4 #乗っかれる壁床タイルタイプ
TILE_FLOOR = (1, 0)  # ジャンプで通り抜けられる床のイメージ座標

# === 衝突判定 ===
class CollisionDetector:
    @staticmethod
    def get_tile(tile_x: int, tile_y: int) -> Tuple[int, int]:
        return pyxel.tilemap(0).pget(tile_x, tile_y)

    @staticmethod
    def detect_collision(x: int, y: int, y_vector: int) -> bool:
        x1 = x // TILE_SIZE
        y1 = y // TILE_SIZE
        x2 = (x + SPRITE_SIZE - 1) // TILE_SIZE
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
    @staticmethod
    def push_back(x: int, y: int, dx: int, dy: int) -> Tuple[int, int, int, int]:
        abs_dx = abs(dx)
        abs_dy = abs(dy)
        if abs_dx > abs_dy:
            x = MovementHandler._push_back_x(x, y, dx, dy)
            y = MovementHandler._push_back_y(x, y, dx, dy)
        else:
            y = MovementHandler._push_back_y(x, y, dx, dy)
            x = MovementHandler._push_back_x(x, y, dx, dy)
        return x, y, dx, dy

    @staticmethod
    def _push_back_x(x: int, y: int, dx: int, dy: int) -> int:
        if dx == 0:
            return x
        sign = 1 if dx > 0 else -1
        for _ in range(abs(dx)):
            if CollisionDetector.detect_collision(x + sign, y, dy):
                break
            x += sign
        return x

    @staticmethod
    def _push_back_y(x: int, y: int, dx: int, dy: int) -> int:
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
    @staticmethod
    def get_sprite_coordinates(direction: Direction) -> Tuple[int, int]:
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
    def __init__(self, x: int, y: int):
        # 位置・速度
        self.x: int = x
        self.y: int = y
        self.dx: int = 0
        self.dy: int = 0
        self.direction: Direction = Direction.RIGHT
        # ジャンプ・床状態
        self.is_on_ground: bool = False
        self.jump_count: int = 0
        self.max_jumps: int = 1
        self.jump_start_y: int = 0
        self.max_jump_height: int = 8 * 3
        self.is_jumping: bool = False
        self.skip_jump: bool = False
        self.floor_state: int = NOT_FLOOR
        self.was_on_ground: bool = False
        self._jump_input: bool = False
        # 各処理クラス
        self.movement_handler: MovementHandler = MovementHandler()
        self.renderer: SpriteRenderer = SpriteRenderer()

    def get_floor_state(self) -> int:
        # プレイヤーの左右両端で判定
        results = set()
        for offset in [0, SPRITE_SIZE - 1]:
            tile_x = (self.x + offset) // TILE_SIZE
            tile_y = (self.y + SPRITE_SIZE) // TILE_SIZE
            tile = CollisionDetector.get_tile(tile_x, tile_y)
            if tile == TILE_FLOOR:
                results.add(ON_THROUGH_FLOOR)
            elif tile[0] >= WALL_TILE_X:
                results.add(ON_FLOOR)
            else:
                results.add(NOT_FLOOR)
        # 優先順位: ON_THROUGH_FLOOR > ON_FLOOR > NOT_FLOOR
        if ON_THROUGH_FLOOR in results:
            return ON_THROUGH_FLOOR
        elif ON_FLOOR in results:
            return ON_FLOOR
        else:
            return NOT_FLOOR

    def update(self) -> None:
        self._update_floor_state()
        self._handle_through_floor_action()
        self._handle_landing_reset()
        self._handle_input_and_movement()
        self._handle_jump()
        self._handle_gravity_and_move()
        self.skip_jump = False

    def _update_floor_state(self) -> None:
        self.floor_state: int = self.get_floor_state()
        self.was_on_ground: bool = getattr(self, 'is_on_ground', False)
        self.is_on_ground: bool = CollisionDetector.detect_collision(self.x, self.y + 1, 1)

    def _handle_through_floor_action(self) -> None:
        if self.is_on_ground and self.floor_state == ON_THROUGH_FLOOR:
            if pyxel.btn(pyxel.KEY_DOWN) and pyxel.btnp(pyxel.KEY_SPACE):
                self.y += 1
                self.skip_jump = True

    def _handle_landing_reset(self) -> None:
        if self.is_on_ground and not getattr(self, 'was_on_ground', False):
            self.jump_count = 0
            self.is_jumping = False

    def _get_movement_input(self, is_on_ground: bool) -> Tuple[int, Direction | None, bool]:
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

    def _handle_input_and_movement(self) -> None:
        dx: int
        direction: Direction | None
        jump: bool
        dx, direction, jump = self._get_movement_input(self.is_on_ground or (self.jump_count < self.max_jumps))
        if direction is not None:
            self.direction = direction
        self.dx = dx * 2
        self._jump_input = jump

    def _handle_jump(self) -> None:
        if self._jump_input and not self.skip_jump and (self.is_on_ground or self.jump_count < self.max_jumps):
            if not self.is_jumping:
                self.jump_start_y = self.y
                self.is_jumping = True
                self.jump_count += 1
            if self.is_jumping and (self.jump_start_y - self.y < self.max_jump_height):
                self.dy = -7
        if not pyxel.btn(pyxel.KEY_SPACE):
            self.is_jumping = False

    def _handle_gravity_and_move(self) -> None:
        self.dy = min(self.dy + 1, 3) if self.dy < 3 else self.dy
        self.x, self.y, self.dx, self.dy = self.movement_handler.push_back(
            self.x, self.y, self.dx, self.dy
        )
        if self.is_on_ground and self.dy > 0:
            self.dy = 0

    def draw(self) -> None:
        Spr_x_Offset: int
        horizon_flip: int
        Spr_x_Offset, horizon_flip = self.renderer.get_sprite_coordinates(self.direction)
        pyxel.blt(
            self.x, self.y, 0,
            Spr_x_Offset, SPRITE_Y_OFFSET,
            SPRITE_SIZE * horizon_flip, SPRITE_SIZE,
            0
        ) 