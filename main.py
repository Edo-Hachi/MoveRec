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
from player import Player
from typing import NoReturn

WIN_WIDTH: int = 128  # ウィンドウ幅
WIN_HEIGHT: int = 128  # ウィンドウ高さ

class App:
    # アプリケーション全体を管理するクラス
    def __init__(self) -> None:
        # Appの初期化処理。Pyxelの初期化、リソースロード、プレイヤー生成、メインループ開始。
        pyxel.init(WIN_WIDTH, WIN_HEIGHT, title="Move Rec", display_scale=4, fps=30)
        pyxel.load("my_resource.pyxres")
        self.player: Player = Player(60, 60)  # プレイヤーを初期位置(60,60)に配置
        pyxel.run(self.update, self.draw)

    # 毎フレーム呼ばれる更新処理。Qキーで終了、プレイヤーの状態更新。
    def update(self) -> None:
        if self._should_quit():
            pyxel.quit()
        self.player.update()

    # Qキーが押されたか判定。戻り値: Trueなら終了
    def _should_quit(self) -> bool:
        return pyxel.btnp(pyxel.KEY_Q)

    # 毎フレーム呼ばれる描画処理。背景・マップ・プレイヤー描画。
    def draw(self) -> None:
        self._draw_background()
        self._draw_map()
        self.player.draw()

    # 画面をクリアする
    def _draw_background(self) -> None:
        pyxel.cls(0)

    # タイルマップを描画する
    def _draw_map(self) -> None:
        pyxel.bltm(0, 0, 0, 0, 0, WIN_WIDTH, WIN_HEIGHT)

# アプリケーションのエントリポイント
# 戻り値: なし（NoReturn）
def main() -> NoReturn:
    App()
    raise SystemExit

if __name__ == "__main__":
    main()