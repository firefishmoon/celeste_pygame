import pygame
import math
import random

class ClassicObject:
    def __init__(self, game, x, y, tile=0) -> None:
        self.G = game
        self.type = 0
        self.spr = tile
        self.flipX = False
        self.flipY = False
        self.solids = True
        self.collideable = True
        self.x = x
        self.y = y
        self.hitbox = pygame.Rect(0, 0, 8, 8)
        self.spd = pygame.Vector2(0, 0)
        self.rem = pygame.Vector2(0, 0)

    def is_solid(self, ox, oy):
        if oy > 0 and not self.check(Platform, ox, 0) and self.check(Platform, ox, oy):
            return True
        solid = self.G.solid_at(self.x + self.hitbox.x + ox, self.y + self.hitbox.y + oy, self.hitbox.w, self.hitbox.h) or \
                self.check(FallFloor, ox, oy) or self.check(FakeWall, ox, oy)
        #print(solid)
        return solid

    def move(self, ox, oy):
        self.rem.x += ox
        amount = math.floor(self.rem.x + 0.5)
        self.rem.x -= amount
        self.move_x(amount, 0)

        self.rem.y += oy
        amount = math.floor(self.rem.y + 0.5)
        self.rem.y -= amount
        self.move_y(amount)

    def sign(self, n):
        return -1 if n < 0 else 1 if n > 0 else 0

    def clamp(self, val, a, b):
        return max(a, min(b, val))
    
    def maybe(self):
        return random.random() < 0.5

    def move_x(self, amount, start):
        if self.solids:
            step = self.sign(amount)
            for i in range(start, int(abs(amount)) + 1):
                if not self.is_solid(step, 0):
                    self.x += step
                else:
                    self.spd.x = 0
                    self.rem.x = 0
                    break
        else:
            self.x += amount
            

    def move_y(self, amount):
        if self.solids:
            step = self.sign(amount)
            for i in range(0, int(abs(amount)) + 1):
                if not self.is_solid(0, step):
                    self.y += step
                else:
                    self.spd.y = 0
                    self.rem.y = 0
                    break
        else:
            self.y += amount

    def update(self):
        pass

    def draw(self):
        if self.spr > 0:
            self.G.draw_spr(self.spr, self.x, self.y, 1, 1, self.flipX, self.flipY)

    def collide(self, ty, ox, oy):
        for obj in self.G.objects:
            if obj and type(obj) == ty and self != obj and obj.collideable and \
                obj.x + obj.hitbox.x + obj.hitbox.w > self.x + self.hitbox.x + ox and \
                obj.y + obj.hitbox.y + obj.hitbox.h > self.y + self.hitbox.y + oy and \
                obj.x + obj.hitbox.x < self.x + self.hitbox.x + self.hitbox.w + ox and \
                obj.y + obj.hitbox.y < self.y + self.hitbox.y + self.hitbox.h + oy:
                return obj
        return None
                
    def check(self, ty, ox, oy):
        return self.collide(ty, ox, oy) != None

class PlayerHair(ClassicObject):
    class Node:
        def __init__(self) -> None:
            self.x = 0
            self.y = 0
            self.size = 0

    def __init__(self, game, x, y, tile=0) -> None:
        super().__init__(game, x, y, tile)
        self.hair = []
        for i in range(0, 5):
            node = PlayerHair.Node()
            node.x = x
            node.y = y
            node.size = max(1, min(2, 3 - i))
            self.hair.append(node)

    def draw_hair(self, obj, facing, djump):
        c = 8 if djump == 1 else (7 + math.floor((self.G.frames / 3) % 2) * 4) if djump == 2 else 12
        last = pygame.Vector2(obj.x + 4 - facing * 2, obj.y + 3)
        for h in self.hair:
            h.x += (last.x - h.x) / 1.5
            h.y += (last.y + 0.5 - h.y) / 1.5
            self.G.draw_circfill(h.x, h.y, h.size, c)
            last = pygame.Vector2(h.x, h.y)
            

class PlayerSpawn(ClassicObject):
    def __init__(self, game, x, y, tile=0) -> None:
        super().__init__(game, x, y, tile)
        self.spr = 3
        self.spd.y = -4
        self.target = pygame.Vector2(x, y)
        self.y = 128
        self.state = 0
        self.solids = False
        self.delay = 0
        self.hair = PlayerHair(game, self.x, self.y)
        self.G.objects.append(self)

    def update(self):
        # jumping up
        if self.state == 0:
            if self.y < self.target.y + 16:
                self.state = 1
                self.delay = 3
        # falling
        elif self.state == 1:
            self.spd.y += 0.5
            if self.spd.y > 0 and self.delay > 0:
                self.spd.y = 0
                self.delay -= 1
            if self.spd.y > 0 and self.y > self.target.y:
                self.y = self.target.y
                self.spd = pygame.Vector2(0, 0)
                self.state = 2
                self.delay = 5
                self.G.shake = 5
                Smoke(self.G, self.x, self.y + 4)
        elif self.state == 2:
            self.delay -= 1
            self.spr = 6
            if self.delay < 0:
                print("Init player...")
                self.G.destroy_object(self)
                player = Player(self.G, self.x, self.y)
                player.hair = self.hair
                
    
    def draw(self):
        self.hair.draw_hair(self, 1, 1)
        super().draw()

class Smoke(ClassicObject):
    def __init__(self, game, x, y, tile=0) -> None:
        super().__init__(game, x, y, tile)
        game.objects.append(self)
        self.spr = 29
        self.spd.y = -0.1
        self.spd.x = 0.3 + (random.random() % 0.2)
        self.x += -1 + random.randint(0, 2)
        self.y += -1 + random.randint(0, 2)
        self.flipX = self.maybe()
        self.flipY = self.maybe()
    
    def update(self):
        self.spr += 0.2
        if self.spr >= 32:
            self.G.destroy_object(self)

class FakeWall(ClassicObject):
    def __init__(self, game, x, y, tile=0) -> None:
        super().__init__(game, x, y, tile)
        game.objects.append(self)
    
    def update(self):
        pass

    def draw(self):
        self.G.draw_spr(64, self.x, self.y)
        self.G.draw_spr(65, self.x + 8, self.y)
        self.G.draw_spr(80, self.x, self.y + 8)
        self.G.draw_spr(81, self.x + 8, self.y + 8)

def break_fall_floor(obj):
    if obj.state == 0:
        obj.state = 1
        obj.delay = 15
        Smoke(obj.G, obj.x, obj.y)
        hit = obj.collide(Spring, 0, -1)
        if hit:
            break_spring(hit)

def break_spring(obj):
    obj.hide_in = 15

class FallFloor(ClassicObject):
    def __init__(self, game, x, y, tile=0) -> None:
        super().__init__(game, x, y, tile)
        game.objects.append(self)
        self.state = 0
        self.solid = True
        self.delay = 0

    def update(self):
        if self.state == 0:
            if self.check(Player, 0, -1) or self.check(Player, -1, 0) or self.check(Player, 1, 0):
                break_fall_floor(self)
        elif self.state == 1:
            self.delay -= 1
            if self.delay <= 0:
                self.state = 2
                self.delay = 60
                self.collideable = False
        elif self.state == 2:
            self.delay -= 1
            if self.delay <= 0 and self.check(Player, 0, 0):
                self.state = 0
                self.collideable = True
                Smoke(self.G, self.x, self.y)
            

    def draw(self):
        if self.state != 2:
            if self.state != 1:
                self.G.draw_spr(23, self.x, self.y)
            else:
                self.G.draw_spr(23 + int((15 - self.delay) / 5), self.x, self.y)

class Fruit(ClassicObject):
    def __init__(self, game, x, y, tile=0) -> None:
        super().__init__(game, x, y, tile)
        game.objects.append(self)
        self.spr = 26
        self.start = y
        self.off = 0
    
    def update(self):
        hit = self.collide(Player, 0, 0)
        if hit:
            hit.djump = self.G.max_djump
            self.G.got_fruit[1 + self.G.level_index] = 1
            Lifeup(self.G, self.x, self.y)
            self.G.destroy_object(self)
        self.off += 1
        self.y = self.start + math.sin(self.off / 40.0) * 2.5

class FlyFruit(ClassicObject):
    def __init__(self, game, x, y, tile=0) -> None:
        super().__init__(game, x, y, tile)
        game.objects.append(self)
        self.start = y
        self.fly = False
        self.step = 0.5
        self.solids = False
        self.spr = 28
    
    def update(self):
        if self.fly:
            self.spd.y = self.G.appr(self.spd.y, -3.5, 0.25)
            if self.y < -16:
                self.G.destroy_object(self)
        else:
            if self.G.has_dashed:
                self.fly = True
            self.step += 0.05
            self.spd.y = math.sin(self.step) * 0.5

        hit = self.collide(Player, 0, 0)
        if hit:
            hit.djump = self.G.max_djump
            self.G.got_fruit[1 + self.G.level_index] = 1
            Lifeup(self.G, self.x, self.y)
            self.G.destroy_object(self)

    def draw(self):
        off = 0
        if not self.fly:
            dir = math.sin(self.step)
            if dir < 0:
                off = 1 + max(0, self.sign(self.y - self.start))
        else:
            off = (off + 0.25) % 3
        self.G.draw_spr(45 + off, self.x - 6, self.y - 2, 1, 1, True, False)
        self.G.draw_spr(self.spr, self.x, self.y)
        self.G.draw_spr(45 + off, self.x + 6, self.y - 2)

class Chest(ClassicObject):
    def __init__(self, game, x, y, tile=0) -> None:
        super().__init__(game, x, y, tile)
        game.objects.append(self)
        self.spr = 20
        self.x -= 4
        self.start = x
        self.timer = 20
    
    def update(self):
        if self.G.has_key:
            self.timer -= 1
            self.x = self.start - 1 + random.randint(0, 3)
            if self.timer <= 0:
                Fruit(self.G, self.x, self.y - 4)
                self.G.destroy_object(self)

class Key(ClassicObject):
    def __init__(self, game, x, y, tile=0) -> None:
        super().__init__(game, x, y, tile)
        game.objects.append(self)

    def update(self):
        was = math.floor(self.spr)
        self.spr = 9 + int(math.sin(self.G.frames / 30.0) + 0.5)
        current = math.floor(self.spr)
        if current == 10 and current != was:
            self.flipX = not self.flipX
        if self.check(Player, 0, 0):
            self.G.destroy_object(self)
            self.G.has_key = True

class Balloon(ClassicObject):
    def __init__(self, game, x, y, tile=0) -> None:
        super().__init__(game, x, y, tile)
        game.objects.append(self)
        self.offset = random.random()
        self.start = y
        self.hitbox = pygame.Rect(-1, -1, 10, 10)
        self.spr = 22
        self.timer = 0

    def update(self):
        if self.spr == 22:
            self.offset += 0.01
            self.y = self.start + math.sin(self.offset) * 2
            hit = self.collide(Player, 0, 0)
            if hit and hit.djump < self.G.max_djump:
                Smoke(self.G, self.x, self.y)
                hit.djump = self.G.max_djump
                self.spr = 0
                self.timer = 60
        elif self.timer > 0:
            self.timer -= 1
        else:
            Smoke(self.G, self.x, self.y)
            self.spr = 22

class Spring(ClassicObject):
    def __init__(self, game, x, y, tile=0) -> None:
        super().__init__(game, x, y, tile)
        game.objects.append(self)
        self.hide_in = 0
        self.hide_for = 0
        self.delay = 0
        self.spr = 18
    
    def update(self):
        if self.hide_for > 0:
            self.hide_for -= 1
            if self.hide_for <= 0:
                self.spr = 18
                self.delay = 0
        elif self.spr == 18:
            hit = self.collide(Player, 0, 0)
            if hit and hit.spd.y >= 0:
                self.spr = 19
                hit.y = self.y - 4
                hit.spd.x *= 0.2
                hit.spd.y = -3
                hit.djump = self.G.max_djump
                self.delay = 10
                Smoke(self.G, self.x, self.y)

                below = self.collide(FallFloor, 0, 1)
                if below:
                    break_fall_floor(below)
        elif self.delay > 0:
            self.delay -= 1
            if self.delay <= 0:
                self.spr = 18
        
        if self.hide_in > 0:
            self.hide_in -= 1
            if self.hide_in <= 0:
                self.hide_for = 60
                self.spr = 0
            


class Platform(ClassicObject):
    def __init__(self, game, x, y, tile=0) -> None:
        super().__init__(game, x, y, tile)
        game.objects.append(self)
        self.x -= 4
        self.solids = False
        self.hitbox.w = 16
        self.last = x
        self.dir = 1

    def update(self):
        self.spd.x = self.dir * 0.65
        if self.x < -16:
            self.x = 128
        if self.x > 128:
            self.x = -16
        if not self.check(Player, 0, 0):
            hit = self.collide(Player, 0, -1)
            if hit:
                hit.move_x(int(self.x - self.last), 1)
        self.last = self.x
    
    def draw(self):
        self.G.draw_spr(11, self.x, self.y - 1)
        self.G.draw_spr(12, self.x + 8, self.y - 1)

class FakeWall(ClassicObject):
    def __init__(self, game, x, y, tile=0) -> None:
        super().__init__(game, x, y, tile)
        game.objects.append(self)

    def update(self):
        self.hitbox = pygame.Rect(-1, -1, 18, 18)
        hit = self.collide(Player, 0, 0)
        if hit and hit.dash_effect_time > 0:
            self.spd.x = -self.sign(hit.spd.x) * 1.5
            self.spd.y = -1.5
            hit.dash_time = -1
            self.G.destroy_object(self)
            Smoke(self.G, self.x, self.y)
            Smoke(self.G, self.x + 8, self.y)
            Smoke(self.G, self.x, self.y + 8)
            Smoke(self.G, self.x + 8, self.y + 8)
            Smoke(self.G, self.x + 4, self.y + 4)
        self.hitbox = pygame.Rect(0, 0, 16, 16)
    
    def draw(self):
       self.G.draw_spr(64, self.x, self.y) 
       self.G.draw_spr(65, self.x + 8, self.y) 
       self.G.draw_spr(80, self.x, self.y + 8) 
       self.G.draw_spr(81, self.x + 8, self.y + 8) 

class Message(ClassicObject):
    def __init__(self, game, x, y, tile=0) -> None:
        super().__init__(game, x, y, tile)
        game.objects.append(self)
        self.last = 0
        self.index = 0
    
    def draw(self):
        text = "-- celeste mountain --#this memorial to those# perished on the climb"
        if self.check(Player, 4, 0):
            if self.index < len(text):
                self.index += 0.5
                if self.index >= self.last + 1:
                    self.last += 1

                off = pygame.Vector2(8, 96)
                for i in range(0, int(self.index)):
                    if text[i] != '#':
                        self.G.rectfill(off.x - 2, off.y - 2, off.x + 7, off.y + 6, 7)
                        self.G.print("" + text[i], off.x, off.y, 0)
                        off.x += 5
                    else:
                        off.x = 8
                        off.y += 7
        else:
            self.last = 0
            self.index = 0

class Orb(ClassicObject):
    def __init__(self, game, x, y, tile=0) -> None:
        super().__init__(game, x, y, tile)
        game.objects.append(self)
        self.spd.y = -4
        self.solids = False
    
    def draw(self):
        self.spd.y = self.G.appr(self.spd.y, 0, 0.5)
        hit = self.collide(Player, 0, 0)
        if self.spd.y == 0 and hit:
            self.G.freeze = 10
            self.G.shake = 10
            self.G.destroy_object(self)
            self.G.max_djump = 2
            hit.djump = 2
        self.G.draw_spr(102, self.x, self.y)
        off = self.G.frames / 30
        for i in range(0, 8):
            self.G.circfill(self.x + 4 + math.cos(off + i / 8) * 8, self.y + 4 + math.sin(off + i / 8) * 8, 1, 7)
    

class BigChest(ClassicObject):
    class Particle:
        def __init__(self, x, y, h, spd) -> None:
            self.x = x
            self.y = y
            self.h = h
            self.spd = spd

    def __init__(self, game, x, y, tile=0) -> None:
        super().__init__(game, x, y, tile)
        game.objects.append(self)
        self.spr = 96
        self.particles = []
        self.hitbox.w = 16
        self.state = 0
        self.timer = 0
    
    def draw(self):
        if self.state == 0:
            hit = self.collide(Player, 0, 8)
            if hit and hit.is_solid(0, 1):
                hit.spd.x = 0
                hit.spd.y = 0
                self.G.pause_player = True
                self.state = 1
                Smoke(self.G, self.x, self.y)
                Smoke(self.G, self.x + 8, self.y)
                self.timer = 60
            self.G.draw_spr(96, self.x, self.y)
            self.G.draw_spr(97, self.x + 8, self.y)
        elif self.state == 1:
            self.timer -= 1
            self.G.shake = 5
            self.G.flash_bg = True
            if self.timer <= 45 and len(self.particles) < 50:
                self.particles.append(BigChest.Particle(
                    1 + random.randint(0, 14),
                    0,
                    32 + random.randint(0, 32),
                    8 + random.randint(0, 8)
                ))
            if self.timer < 0:
                self.state = 2
                self.particles.clear()
                self.G.flash_bg = False
                self.G.new_bg = True
                Orb(self.G, self.x + 4, self.y + 4)
                self.G.pause_player = False
            for p in self.particles:
                p.y += p.spd
                self.G.rectfill(self.x + p.x, self.y + 8 - p.y, self.x + p.x + 1, min(self.y + 8 - p.y + p.h, self.y + 8), 7)

        self.G.spr(112, self.x, self.y + 8)
        self.G.spr(113, self.x + 8, self.y + 8)

class Flag(ClassicObject):
    def __init__(self, game, x, y, tile=0) -> None:
        super().__init__(game, x, y, tile)
        game.objects.append(self)
        self.score = 0
        self.show = False
        self.x += 5
    
    def draw(self):
        self.spr = 118 + int((self.G.frames / 5) % 3)
        self.G.draw_spr(self.spr, self.x, self.y)
        if self.show:
            self.G.rectfill(32, 2, 96, 31, 0)
            self.G.draw_spr(26, 55, 6)
            self.G.print("x{}".format(len(self.G.got_fruit)), 64, 9, 7)
            self.G.print("deaths:{}".format(self.G.deaths), 48, 24, 7)
        elif self.check(Player, 0, 0):
            self.show = True

class Lifeup(ClassicObject):
    def __init__(self, game, x, y, tile=0) -> None:
        super().__init__(game, x, y, tile)
        game.objects.append(self)
        self.spd.y = -0.25
        self.duration = 30
        self.x -= 2
        self.y -= 4
        self.flash = 0
        self.solids = False
    
    def update(self):
        self.duration -= 1
        if self.duration <= 0:
            self.G.destroy_object(self)
    
    def draw(self):
        self.flash += 0.5
        self.G.print("1000", self.x - 2, self.y, int(7 + self.flash % 2))

class Player(ClassicObject):
    def __init__(self, game, x, y, tile=0) -> None:
        super().__init__(game, x, y, tile)
        game.objects.append(self)
        self.p_jump = False
        self.p_dash = False
        self.grace = 0
        self.jbuffer = 0
        self.spr = 1
        self.djump = 1
        self.dash_time = 0
        self.dash_effect_time = 0
        self.dash_target = pygame.Vector2(0, 0)
        self.dash_accel = pygame.Vector2(0, 0)
        self.spr_off = 0
        self.was_on_ground = False
        self.hitbox = pygame.Rect(1, 3, 6, 5)
        self.hair = None

    def update(self):
        if self.G.pause_player:
            return
        
        input = 1 if self.G.btn('right') else -1 if self.G.btn('left') else 0

        if self.G.spikes_at(self.x + self.hitbox.x, self.y + self.hitbox.y, self.hitbox.w, self.hitbox.h, self.spd.x, self.spd.y):
            self.G.kill_player(self)

        if self.y > 128:
            self.G.kill_player(self)

        on_ground = self.is_solid(0, 1)

        if on_ground and not self.was_on_ground:
            Smoke(self.G, self.x, self.y + 4)

        jump = self.G.btn('jump') and not self.p_jump
        self.p_jump = self.G.btn('jump')
        if jump:
            self.jbuffer = 4  # 4 frames before landing, you can perform jump
        elif self.jbuffer > 0:
            self.jbuffer -= 1

        dash = self.G.btn('dash') and not self.p_dash
        self.p_dash = self.G.btn('dash')
        
        if on_ground:
            self.grace = 6 # 6 frames after jumping from ground, you can perform wall jump.
            if self.djump < self.G.max_djump:
                self.djump = self.G.max_djump
        elif self.grace > 0:
            self.grace -= 1

        self.dash_effect_time -= 1
        if self.dash_time > 0:
            Smoke(self.G, self.x, self.y)
            self.dash_time -= 1
            self.spd.x = self.G.appr(self.spd.x, self.dash_target.x, self.dash_accel.x)
            self.spd.y = self.G.appr(self.spd.y, self.dash_target.y, self.dash_accel.y)
        else:
            maxrun = 1
            accel = 0.6
            deaccel = 0.15

            if not on_ground:
                accel = 0.4

            if abs(self.spd.x) > maxrun:
                self.spd.x = self.G.appr(self.spd.x, self.sign(self.spd.x) * maxrun, deaccel)
            else:
                self.spd.x = self.G.appr(self.spd.x, input * maxrun, accel)

            if self.spd.x != 0:
                self.flipX = (self.spd.x < 0)
            
            maxfall = 2
            gravity = 0.21

            if abs(self.spd.y) <= 0.15:
                gravity *= 0.5
            
            # wall slide
            if not on_ground and input != 0 and self.is_solid(input, 0):
                maxfall = 0.4
                if random.randint(0, 10) < 2:
                    Smoke(self.G, self.x + input * 6, self.y)
            
            if not on_ground:
                self.spd.y = self.G.appr(self.spd.y, maxfall, gravity)

            # jump 
            if self.jbuffer > 0:
                if self.grace > 0:
                    # normal jump
                    self.jbuffer = 0
                    self.grace = 0
                    self.spd.y = -2
                    Smoke(self.G, self.x, self.y + 4)
                else:
                    # wall jump
                    wall_dir = -1 if self.is_solid(-3, 0) else 1 if self.is_solid(3, 0) else 0
                    if wall_dir != 0:
                        self.jbuffer = 0
                        self.spd.y = -2
                        self.spd.x = -wall_dir * (maxrun + 1)
            # dash
            d_full = 5
            d_half = 5 * 0.70710678118
            if self.djump > 0 and dash:
                Smoke(self.G, self.x, self.y)
                self.djump -= 1
                self.dash_time = 4
                self.G.has_dashed = True
                self.dash_effect_time = 10

                dash_x_input = -1 if self.G.btn('left') else 1 if self.G.btn('right') else 0
                dash_y_input = -1 if self.G.btn('up') else 1 if self.G.btn('down') else 0

                if dash_x_input != 0 and dash_y_input != 0:
                    self.spd.x = dash_x_input * d_half
                    self.spd.y = dash_y_input * d_half
                elif dash_x_input != 0:
                    self.spd.x = dash_x_input * d_full
                    self.spd.y = 0
                else:
                    self.spd.x = 0
                    self.spd.y = dash_y_input * d_full
                self.G.freeze = 3
                self.G.shake = 6
                self.dash_target.x = 2 * self.sign(self.spd.x)
                self.dash_target.y = 2 * self.sign(self.spd.y)
                self.dash_accel.x = 1.5
                self.dash_accel.y = 1.5

                if self.spd.y < 0:
                    self.dash_target.y *= 0.75
                if self.spd.y != 0:
                    self.dash_accel.x *= 0.70710678118
                if self.spd.x != 0:
                    self.dash_accel.y *= 0.70710678118
            elif dash and self.djump <= 0:
                print('dash only smoke')
                Smoke(self.G, self.x, self.y)


        self.spr_off += 0.25
        if not on_ground:
            if self.is_solid(input, 0):
                self.spr = 5
            else:
                self.spr = 3
        elif self.G.btn('down'):
            self.spr = 6
        elif self.G.btn('up'):
            self.spr = 7
        elif self.spd.x == 0 or (not self.G.btn('left') and not self.G.btn('right')):
            self.spr = 1
        else:  
            self.spr = 1 + int(self.spr_off % 4)
        
        if self.y < -4 and self.G.level_index() < 30:
            self.G.next_room()
        
        self.was_on_ground = on_ground

    def draw(self):
        if self.x < -1 or self.x > 121:
            self.x = self.clamp(self.x, -1, 121)
            self.spd.x = 0
        
        self.draw_player()
    
    def draw_player(self):
        spritePush = 0
        if self.djump == 2:
            if (self.G.frames / 3) % 2 == 0:
                spritePush = 10 * 16
            else:
                spritePush = 9 * 16
        elif self.djump == 0:
            spritePush = 8 * 16

        self.hair.draw_hair(self, -1 if self.flipX else 1, self.djump)
        self.G.draw_spr(self.spr + spritePush, self.x, self.y, 1, 1, self.flipX, self.flipY)
