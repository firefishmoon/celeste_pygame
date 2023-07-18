#
# app.py
#
import pygame
from pygame import Color, Rect
import sys
import math
import random

from pygame.display import flip
from map import Map
from objects import *

class Game:
    SCALE = 2
    SCREEN_WIDTH = 16 * 8 * SCALE
    SCREEN_HEIGHT = 16 * 8 * SCALE
    TILE_ROW = 16
    TILE_COL = 16
    TILE_WIDTH = 8 * SCALE
    TILE_HEIGHT = 8 * SCALE

    INPUT_LEFT = pygame.K_a
    INPUT_RIGHT = pygame.K_d
    INPUT_UP = pygame.K_w
    INPUT_DOWN = pygame.K_s
    INPUT_JUMP = pygame.K_j
    INPUT_DASH = pygame.K_k

    FONTMAP = "abcdefghijklmnopqrstuvwxyz0123456789~!@#4%^&*()_+-=?:."

    COLORS = [
            pygame.Color("#000000"),
            pygame.Color("#1d2b53"),
            pygame.Color("#7e2553"),
            pygame.Color("#008751"),
            pygame.Color("#ab5236"),
            pygame.Color("#5f574f"),
            pygame.Color("#c2c3c7"),
            pygame.Color("#fff1e8"),
            pygame.Color("#ff004d"),
            pygame.Color("#ffa300"),
            pygame.Color("#ffec27"),
            pygame.Color("#00e436"),
            pygame.Color("#29adff"),
            pygame.Color("#83769c"),
            pygame.Color("#ff77a8"),
            pygame.Color("#ffccaa")
    ]

    class DeadParticle:
        def __init__(self, x, y, t, spd) -> None:
            self.x = x
            self.y = y
            self.t = t
            self.spd = spd
            print(spd.x, spd.y)

    def __init__(self):
        self.frames = 0
        self.deaths = 0
        self.will_restart = False
        self.delay_restart = 0
        self.shake = 0
        self.max_djump = 1
        self.has_dashed = False
        self.has_key = False
        self.shakeoffset = pygame.Vector2(0, 0)
        self.room_x = 0
        self.room_y = 0
        self.freeze = 0
        self.map = Map(self)
        self.sprites = []
        self.font = []
        self.objects = []
        self.pause_player = False
        self.flash_bg = False
        self.new_bg = False
        self.start_game = False
        self.start_game_flash = 0
        self.got_fruit = {}
        self.dead_particles = []
        self.inputs = { 'up' : False, 'down' : False, 'left' : False, 'right' : False, 'jump' : False, 'dash' : False }
        atlas = pygame.image.load('atlas.png')
        for y in range(0, int(atlas.get_height() / 8)):
            for x in range(0, int(atlas.get_width() / 8)):
                self.sprites.append(pygame.transform.scale_by(atlas.subsurface((x * 8, y * 8, 8, 8)), Game.SCALE))
        font_atlas = pygame.image.load('font.png')
        for y in range(0, int(font_atlas.get_height() / 6)):
            for x in range(0, int(font_atlas.get_width() / 4)):
                self.font.append(pygame.transform.scale_by(font_atlas.subsurface((x * 4, y * 6, 4, 6)), Game.SCALE))

        #self.load_room(6, 3)
        self.title_screen()

    def destroy_object(self, obj):
        if self.objects.count(obj) > 0:
            index = self.objects.index(obj)
            self.objects[index] = None

    def kill_player(self, obj):
        self.deaths += 1
        self.shake = 10
        self.destroy_object(obj)

        self.dead_particles.clear()
        for dir in range(0, 8):
            angel = dir / 8.0
            self.dead_particles.append(Game.DeadParticle(
                obj.x + 4,
                obj.y + 4,
                10,
                pygame.Vector2(math.cos(angel) * 3, math.sin(angel + 0.5) * 3)
            ))

        self.restart_room()
        

    def solid_at(self, x, y, w, h):
        return self.tile_flag_at(x, y, w, h, 0)


    def tile_flag_at(self, x, y, w, h, flag):
        left = int(max(0, math.floor(x / 8)))
        right = int(min(15, (x + w - 1) / 8))
        bottom = int(max(0, math.floor(y / 8)))
        top = int(min(15, (y + h - 1) / 8))
        for i in range(left, right + 1):
            for j in range(bottom, top + 1):
                if self.map.fget(self.tile_at(i, j), flag):
                    return True
        return False
    
    def spikes_at(self, x, y, w, h, xspd, yspd):
        left = int(max(0, math.floor(x / 8)))
        right = int(min(15, (x + w - 1) / 8))
        bottom = int(max(0, math.floor(y / 8)))
        top = int(min(15, (y + h - 1) / 8))
        for i in range(left, right + 1):
            for j in range(bottom, top + 1):
                tile = self.tile_at(i, j)
                if tile == 17 and ((y + h - 1) % 8 >= 6 or y + h == j * 8 + 8) and yspd >= 0:
                    return True
                elif tile == 27 and y % 8 <= 2 and yspd <= 0:
                    return True
                elif tile == 43 and x % 8 <= 2 and xspd <= 0:
                    return True
                elif tile ==59 and ((x + w - 1) % 8 >= 6 or x + w == i * 8 + 8) and xspd >= 0:
                    return True
        return False

    def tile_at(self, x, y):
        return self.map.mget(self.room_x * 16 + x, self.room_y * 16 + y)

    def draw_grid(self):
        white = Color(255, 255, 255)
        # draw Vertical lines
        for x in range(0, Game.SCREEN_WIDTH, Game.TILE_WIDTH):
            pygame.draw.line(SURFACE, white, (x, 0), (x, Game.SCREEN_HEIGHT))
        # draw Horizontal lines
        for y in range(0, Game.SCREEN_HEIGHT, Game.TILE_HEIGHT):
            pygame.draw.line(SURFACE, white, (0, y), (Game.SCREEN_WIDTH, y))
    
    def draw_circfill(self, x, y, r, c):
        color = Game.COLORS[int(c) % 16]
        if r <= 1:
            pygame.draw.rect(SURFACE, color, ((x - 1) * Game.SCALE, y * Game.SCALE, 3 * Game.SCALE, 1 * Game.SCALE))
            pygame.draw.rect(SURFACE, color, (x * Game.SCALE, (y - 1) * Game.SCALE, 1 * Game.SCALE, 3 * Game.SCALE))
        elif r <= 2:
            pygame.draw.rect(SURFACE, color, ((x - 2) * Game.SCALE, (y - 1) * Game.SCALE, 5 * Game.SCALE, 3 * Game.SCALE))
            pygame.draw.rect(SURFACE, color, ((x - 1) * Game.SCALE, (y - 2) * Game.SCALE, 3 * Game.SCALE, 5 * Game.SCALE))
        elif r <= 3:
            pygame.draw.rect(SURFACE, color, ((x - 3) * Game.SCALE, (y - 1) * Game.SCALE, 7 * Game.SCALE, 3 * Game.SCALE))
            pygame.draw.rect(SURFACE, color, ((x - 1) * Game.SCALE, (y - 3) * Game.SCALE, 3 * Game.SCALE, 7 * Game.SCALE))
            pygame.draw.rect(SURFACE, color, ((x - 2) * Game.SCALE, (y - 2) * Game.SCALE, 5 * Game.SCALE, 5 * Game.SCALE))
    
    def title_screen(self):
        self.got_fruit = {}
        self.frames = 0
        self.max_djump = 1
        self.start_game = False
        self.start_game_flash = 0
        self.load_room(7, 3)
    
    def begin_game(self):
        self.frames = 0
        self.start_game = False
        self.load_room(0, 0)

    def update(self):
        self.frames = (self.frames + 1) % 30

        if self.freeze > 0:
            self.freeze -= 1
            return

        if self.will_restart and self.delay_restart > 0:
            self.delay_restart -= 1
            if self.delay_restart <= 0:
                self.will_restart = False
                self.load_room(self.room_x, self.room_y)

        for obj in self.objects:
            if obj:
                obj.move(obj.spd.x, obj.spd.y)
                obj.update()
        
        c = self.objects.count(None)
        for i in range(0, c):
            self.objects.remove(None)

        if self.is_title():
            if not self.start_game and (self.btn('jump') or self.btn('dash')):
                self.start_game_flash = 50
                self.start_game = True
            if self.start_game:
                self.start_game_flash -= 1
                if self.start_game_flash <= 20:
                    self.begin_game()


    def render(self):
        if self.shake > 0:
            self.shake -= 1
            self.shakeoffset = pygame.Vector2(0, 0)
            if self.shake > 0:
                self.shakeoffset = pygame.Vector2(random.randint(0, 5), random.randint(0, 5))
                
        #self.draw_grid() 
        self.map.draw(self.room_x * 16, self.room_y * 16, 0, 0, 16, 16, 2)
        self.map.draw(self.room_x * 16, self.room_y * 16, 0, 0, 16, 16, 1)

        for obj in self.objects:
            obj.draw()
        
        for i in range(0, len(self.dead_particles)):
            p = self.dead_particles[i]
            p.x += p.spd.x
            p.y += p.spd.y
            p.t -= 1
            if p.t <= 0:
                self.dead_particles[i] = None
            self.rectfill(p.x - p.t / 5, p.y - p.t / 5, p.x + p.t / 5, p.y + p.t / 5, int(14 + p.t % 2))
        c = self.dead_particles.count(None)
        for i in range(0, c):
            self.dead_particles.remove(None)

        if self.is_title():
            self.print("press button", 42, 96, 5)
            self.print("firemoon", 50, 106, 5)
        
       
    def draw_tile(self, idx, tx, ty):
        if idx < len(self.sprites):
            SURFACE.blit(self.sprites[idx], (tx * Game.SCALE - self.shakeoffset.x, ty * Game.SCALE - self.shakeoffset.y, 8 * Game.SCALE, 8 * Game.SCALE))
        else:
            print("sprite out of range")

    def draw_spr(self, idx, x, y, columns = 1, rows = 1, flipX = False, flipY = False):
        for sx in range(0, columns):
            for sy in range(0, rows):
                spr = self.sprites[int(idx + sx + sy * 16)]
                if flipX or flipY:
                    spr = pygame.transform.flip(spr, flipX, flipY)
                SURFACE.blit(spr, ((x + sx * 8) * Game.SCALE - self.shakeoffset.x, (y + sy * 8) * Game.SCALE - self.shakeoffset.y))
    
    def rectfill(self, x, y, x2, y2, c):
        left = min(x, x2)
        top = min(y, y2)
        width = max(x, x2) - left + 1
        height = max(y, y2) - top + 1
        pygame.draw.rect(SURFACE, Game.COLORS[int(c) % 16], (left * Game.SCALE, top * Game.SCALE, width * Game.SCALE, height * Game.SCALE))
    
    def print(self, str, x, y, c):
        left = x
        color = Game.COLORS[int(c) % 16]
        for i in range(0, len(str)):
            char = str[i]
            index = -1
            for j in range(0, len(Game.FONTMAP)):
                if Game.FONTMAP[j] == char:
                    index = j
                    break
            if index >= 0:
                s = pygame.surface.Surface((8,12))
                s.fill(color)
                d = self.font[index].copy()
                d.blit(s, (0, 0), special_flags=pygame.BLEND_MIN)
                SURFACE.blit(d, (left * Game.SCALE - self.shakeoffset.x, y * Game.SCALE - self.shakeoffset.y))
            left += 4

    def level_index(self):
        return self.room_x % 8 + self.room_y * 8
    
    def is_title(self):
        return self.level_index() == 31

    def restart_room(self):
        self.will_restart = True
        self.delay_restart = 15

    def load_room(self, x, y):
        self.has_dashed = False
        self.room_x = x
        self.room_y = y
        print("room {} {}".format(x, y))

        self.objects.clear()
        k = 1 + self.level_index()
        
        for tx in range(0, 16):
            for ty in range(0, 16):
                tile = self.map.mget(self.room_x * 16 + tx, self.room_y * 16 + ty)
                if tile == 1:
                    print("player spawn at {} {}".format(tx, ty))
                    obj = PlayerSpawn(self, tx * 8, ty * 8)
                elif tile == 18:
                    print("spring")
                    Spring(self, tx * 8, ty * 8)
                elif tile == 22:
                    print("balloon")
                    Balloon(self, tx * 8, ty * 8)
                elif tile == 23:
                    print("fall_floor at {} {}".format(tx, ty))
                    FallFloor(self, tx * 8, ty * 8)
                elif tile == 86:
                    print("message")
                    Message(self, tx * 8, ty * 8)
                elif tile == 96:
                    print("big_chest")
                    BigChest(self, tx * 8, ty * 8)
                elif tile == 118:
                    print("flag")
                    Flag(self, tx * 8, ty * 8)
                elif tile == 64:
                    print("fake_wall")
                    FakeWall(self, tx * 8, ty * 8)
                elif k not in self.got_fruit:
                    if tile  == 26:
                        print("fruit")
                        Fruit(self, tx * 8, ty * 8)
                    elif tile == 28:
                        print("fly_fruit")
                        FlyFruit(self, tx * 8, ty * 8)
                    elif tile == 8:
                        print("key")
                        Key(self, tx * 8, ty * 8)
                    elif tile == 20:
                        print("chest")
                        Chest(self, tx * 8, ty * 8)
                elif tile == 11:
                    print("platform_1")
                    p = Platform(self, tx * 8, ty * 8)
                    p.dir = -1
                elif tile == 12:
                    print("platform_2")
                    p = Platform(self, tx * 8, ty * 8)
                    p.dir = 1
    
    def next_room(self):
        if self.room_x == 7:
            self.load_room(0, self.room_y + 1)
        else:
            self.load_room(self.room_x + 1, self.room_y)

    def btn(self, key):
        return self.inputs[key]

    def appr(self, val, target, amount):
        return max(val - amount, target) if val > target else min(val + amount, target)
        

def main():
    global SURFACE
    pygame.init()
    G = Game()
    SURFACE = pygame.display.set_mode((Game.SCREEN_WIDTH, Game.SCREEN_HEIGHT))
    pygame.display.set_caption('Celeste python')
    clock = pygame.time.Clock()
    while True:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == Game.INPUT_LEFT:
                    G.inputs['left'] = True
                elif event.key == Game.INPUT_RIGHT:
                    G.inputs['right'] = True
                elif event.key == Game.INPUT_UP:
                    G.inputs['up'] = True
                elif event.key == Game.INPUT_DOWN:
                    G.inputs['down'] = True
                elif event.key == Game.INPUT_JUMP:
                    G.inputs['jump'] = True
                elif event.key == Game.INPUT_DASH:
                    G.inputs['dash'] = True
            elif event.type == pygame.KEYUP:
                if event.key == Game.INPUT_LEFT:
                    G.inputs['left'] = False
                elif event.key == Game.INPUT_RIGHT:
                    G.inputs['right'] = False
                elif event.key == Game.INPUT_UP:
                    G.inputs['up'] = False
                elif event.key == Game.INPUT_DOWN:
                    G.inputs['down'] = False
                elif event.key == Game.INPUT_JUMP:
                    G.inputs['jump'] = False
                elif event.key == Game.INPUT_DASH:
                    G.inputs['dash'] = False
        bg_col = Game.COLORS[0]
        if G.flash_bg:
            bg_col = Game.COLORS[int(G.frames / 5)]
        elif G.new_bg:
            bg_col = Game.COLORS[2]
        SURFACE.fill(bg_col)
        G.update()
        G.render()
        pygame.display.flip()
main()
