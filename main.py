import pyxel
from player import Player #, CollisionDetector
#from typing import Tuple

WIN_WIDTH = 128
WIN_HEIGHT = 128

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