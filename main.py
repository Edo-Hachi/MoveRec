# coding: utf-8
# コーディングルール:
# - すべての変数・関数・戻り値に型アノテーションを必ず付与すること
# - 定数宣言時は"HOGHOGE"のような文字列は使わない。必ず HOGEHOGE = 1 みたいに宣言する。たくさんある時は enum にする
# - 1関数につき30行以内を目安に分割
# - コメントは日本語で記述

# - 関数宣言したら、関数の機能、引数がある時は引数名と、なんの値を受け取っているかをコメントで書く
#    def _draw_sprige(self, x: int, y: int w, int h):
# x : 表示する x座標
# y : 表示する y座標
# w : スプライトの幅
# h : スプライトの高さ

import pyxel
from player import Player, CameraManager
from typing import NoReturn

WIN_WIDTH: int = 128  # ウィンドウ幅
WIN_HEIGHT: int = 128  # ウィンドウ高さ
TRANSPARENT_COLOR: int = 0  # 透明色として扱う色番号

class App:
    # アプリケーション全体を管理するクラス
    def __init__(self) -> None:
        # Appの初期化処理。Pyxelの初期化、リソースロード、プレイヤー生成、メインループ開始。
        pyxel.init(WIN_WIDTH, WIN_HEIGHT, title="Move Rec", display_scale=4, fps=30)
        pyxel.load("my_resource.pyxres")
        
        # カメラマネージャーを作成
        self.camera_manager: CameraManager = CameraManager()
        # プレイヤーを初期位置(60,60)に配置、カメラマネージャーを渡す
        self.player: Player = Player(60, 60, self.camera_manager)
        
        pyxel.run(self.update, self.draw)

    def update(self) -> None:
        # 毎フレーム呼ばれる更新処理。Qキーで終了、プレイヤーの状態更新。
        if self._should_quit():
            pyxel.quit()
        self.player.update()

    def _should_quit(self) -> bool:
        # Qキーが押されたか判定。戻り値: Trueなら終了
        return pyxel.btnp(pyxel.KEY_Q)

    def draw(self) -> None:
        # 毎フレーム呼ばれる描画処理。背景・マップ・プレイヤー描画。
        self._draw_background()
        self._draw_map()
        self._draw_characters()

    def _draw_background(self) -> None:
        # 画面をクリアする
        pyxel.cls(0)

    def _draw_map(self) -> None:
        # タイルマップを描画する（スクロール対応）
        scroll_x = self.camera_manager.get_scroll_x()
        
        # カメラをリセット（背景描画用）
        self.camera_manager.reset_camera()
        
        # 背景レイヤーの描画（視差効果のためにスクロール量を調整）
        # 10_platformer.pyを参考に背景を少し遅くスクロールさせる
        pyxel.bltm(0, 0, 0, (scroll_x // 4) % WIN_WIDTH, WIN_HEIGHT, WIN_WIDTH, WIN_HEIGHT)
        
        # メインのタイルマップの描画
        pyxel.bltm(0, 0, 0, scroll_x, 0, WIN_WIDTH, WIN_HEIGHT, TRANSPARENT_COLOR)

    def _draw_characters(self) -> None:
        # キャラクターを描画する（カメラ座標系で描画）
        self.camera_manager.set_camera()
        self.player.draw()

# アプリケーションのエントリポイント
# 戻り値: なし（NoReturn）
def main() -> NoReturn:
    App()
    raise SystemExit

if __name__ == "__main__":
    main()
