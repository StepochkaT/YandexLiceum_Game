import random

import pygame
from math_funcs import load_image, obstacle_intersect_by_line, euclidean_distance, find_path_in_graph, load_sound
import math

import settings


class Object(pygame.sprite.Sprite):
    def __init__(self, points, texture, game, angle=0, *groups):
        super().__init__(game.all_sprites, *groups)

        min_x = min(p[0] for p in points)
        min_y = min(p[1] for p in points)
        max_x = max(p[0] for p in points)
        max_y = max(p[1] for p in points)

        rect_width = max_x - min_x
        rect_height = max_y - min_y

        self.image = pygame.Surface((rect_width, rect_height), pygame.SRCALPHA)
        self.rect = self.image.get_rect(topleft=(min_x, min_y))
        self.points = points

        tile = pygame.transform.rotate(load_image(texture), angle)

        tile_width, tile_height = tile.get_size()

        tiled_texture = pygame.Surface((rect_width, rect_height), pygame.SRCALPHA)
        for y in range(0, rect_height, tile_height):
            for x in range(0, rect_width, tile_width):
                tiled_texture.blit(tile, (x, y))

        mask_surface = pygame.Surface((rect_width, rect_height), pygame.SRCALPHA)
        offset_points = [(p[0] - min_x, p[1] - min_y) for p in points]
        pygame.draw.polygon(mask_surface, (255, 255, 255), offset_points)

        tiled_texture.blit(mask_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        self.image.blit(tiled_texture, (0, 0))
        self.mask = pygame.mask.from_surface(self.image)


class AnimatedSprite(pygame.sprite.Sprite):
    def __init__(self, position, default_image, game, *groups):
        super().__init__(game.all_sprites, *groups)

        self.position = pygame.Vector2(position)
        self.image = default_image
        self.default_image = self.image
        self.rect = self.image.get_rect(center=position)

        self.angle = 0

        self.animation_frames = None
        self.animation_speed = 0
        self.animation_index = -1
        self.animation_timer = 0
        self.loop_animation = False
        self.animation_complete = False

    def play_animation(self, frames, speed, loop=False):
        self.animation_frames = frames
        self.animation_speed = speed
        self.animation_index = -1
        self.animation_timer = pygame.time.get_ticks()
        self.loop_animation = loop
        self.animation_complete = False

    def update_animation(self):
        if not self.animation_frames:
            return

        current_time = pygame.time.get_ticks()
        if current_time - self.animation_timer > self.animation_speed or self.animation_index == -1:
            self.animation_index += 1
            self.animation_timer = current_time

            if self.animation_index >= len(self.animation_frames):
                if self.loop_animation:
                    self.animation_index = 0
                else:
                    self.animation_frames = None
                    self.animation_complete = True
                    return

            self.image = self.animation_frames[self.animation_index]
            self.rect = self.image.get_rect(center=self.rect.center)
            self.default_image = self.image

    def update(self):
        self.update_animation()
        self.image = pygame.transform.rotate(self.default_image, self.angle)


class XP_Particle(AnimatedSprite):
    def __init__(self, position, game):
        frames = [load_image(f"xp_particles{i}.png") for i in range(0, 6)]
        super().__init__(position=position, default_image=frames[0], game=game)

        self.appear_frames = frames
        self.default_frames = [load_image(f"default_xp{i}.png") for i in range(0, 2)]
        self.image = self.appear_frames[0]
        self.rect = self.image.get_rect(center=position)

        self.play_animation(self.appear_frames, 50, False)

        self.game = game

    def update(self):
        super().update()

        if not self.animation_frames:
            self.mask = pygame.mask.from_surface(self.image)
            self.play_animation(self.default_frames, 500, True)

        if pygame.sprite.collide_mask(self, self.game.player):
            self.game.player.heal(100)
            self.kill()


class Bullet_Particle(AnimatedSprite):
    def __init__(self, position, game):
        frames = [load_image(f"bullet_particle{i}.png") for i in range(0, 5)]
        super().__init__(position=position, default_image=frames[0], game=game)

        self.appear_frames = frames
        self.default_frames = [load_image(f"default_bullet{i}.png") for i in range(0, 3)]
        self.image = self.appear_frames[0]
        self.rect = self.image.get_rect(center=position)

        self.play_animation(self.appear_frames, 50, False)

        self.game = game

    def update(self):
        super().update()

        if not self.animation_frames:
            self.mask = pygame.mask.from_surface(self.image)
            self.play_animation(self.default_frames, 500, True)

        if pygame.sprite.collide_mask(self, self.game.player):
            self.game.player.amo += 10
            self.kill()


class Entity(AnimatedSprite):
    def __init__(self, position, health, death_frames, damaged_frames, game):
        image = death_frames[0]
        super().__init__(position, image, game, game.all_enemies)

        self.position = pygame.Vector2(position)
        self.health = health
        self.is_dying = False
        self.death_frames = death_frames
        self.damaged_frames = damaged_frames
        self.image = image
        self.rect = self.image.get_rect(center=position)
        self.angle = 0
        self.is_moving = False

        self.game = game

    def damage(self, damage):
        if not self.is_dying:
            self.health -= damage
            self.play_animation(self.damaged_frames, 200)
            self.game.hit_sound.play()

            if self.health <= 0:
                self.start_death()
                return

    def start_death(self):
        self.is_dying = True
        self.play_animation(self.death_frames, 300, False)
        self.game.dead_sound.play()

    def update(self):
        if self not in self.game.all_enemies:
            return
        super().update()
        if self.is_dying and self.animation_complete is True:
            if isinstance(self, Enemy):
                XP_Particle((self.position.x, self.position.y - 30), game=self.game)
                self.game.spawn_new_enemies()
            else:
                Bullet_Particle((self.position.x, self.position.y - 30), game=self.game)

            self.game.all_enemies.remove(self)


class Enemy(Entity):
    def __init__(self, position, speed, game):
        death_frames = [load_image(f"deathing_moving{i}.png") for i in range(0, 9)]
        damaged_frames = [load_image(f"damaged_moving{i}.png") for i in range(1, 3)]

        super().__init__(position, health=500, death_frames=death_frames, damaged_frames=damaged_frames, game=game)

        self.speed = speed
        self.path = []
        self.attack_timer = 0
        self.preparing_attack = False
        frames = ['00', '01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11']
        self.walking_frames = [load_image(f"walking_enemy{i}.png") for i in
                               frames]
        self.attacking_frames = [load_image(f"attacking_enemy{i}.png") for i in
                                 frames]

        self.game = game

    def set_path(self, path):
        self.path = [pygame.Vector2(p) for p in path]
        if int(self.path[0].x) == int(self.position.x) and int(self.path[0].y) == int(self.position.y):
            self.path = self.path[1:]

    def generate_path(self):
        dynamic_graph = self.game.static_graph.copy()
        start_point = tuple([int(i) for i in tuple(self.position)])
        target = tuple([int(i) for i in tuple(self.game.player.position)])
        dynamic_graph[start_point] = []
        dynamic_graph[target] = []

        for point in self.game.graph_points:
            if all([type(obstacle_intersect_by_line(start_point[0], start_point[1], point[0], point[1],
                                                    obstacle.points, self.game.graph_points)) != list
                    for obstacle in self.game.all_obstacles]):
                distance = euclidean_distance(start_point, point)
                dynamic_graph[start_point].append((point, distance))
                dynamic_graph[point].append((start_point, distance))

            if all([type(obstacle_intersect_by_line(target[0], target[1], point[0], point[1], obstacle.points,
                                                    self.game.graph_points)) != list
                    for
                    obstacle in self.game.all_obstacles]):
                distance = euclidean_distance(target, point)
                dynamic_graph[target].append((point, distance))
                dynamic_graph[point].append((target, distance))

            if all([type(obstacle_intersect_by_line(target[0], target[1], start_point[0], start_point[1],
                                                    obstacle.points, self.game.graph_points)) != list
                    for obstacle in self.game.all_obstacles]):
                distance = euclidean_distance(target, start_point)
                dynamic_graph[target].append((start_point, distance))
                dynamic_graph[start_point].append((target, distance))
        cost, shortest_path = find_path_in_graph(dynamic_graph, start_point, target)
        self.set_path(shortest_path)

    def attack(self, player):
        if euclidean_distance(player.position, self.position) <= 35:
            self.attack_timer = pygame.time.get_ticks()
            self.preparing_attack = False
            self.play_animation(self.attacking_frames, 50, False)
            player.damage(200)
            self.game.knife_sound.play()

    def update(self):
        super().update()

        if self.is_dying:
            return

        if self.path:
            if euclidean_distance(self.path[-1], self.game.player.position) > 10:
                self.generate_path()

            target = self.path[0]
            direction = target - self.position
            distance = direction.length()

            if distance < self.speed:
                self.position = target
                self.path.pop(0)

            if euclidean_distance(self.position, self.game.player.position) <= 30:
                self.path = []

            else:
                if direction.length() > 0:
                    direction.normalize_ip()
                    self.position += direction * self.speed
                self.is_moving = True
            self.angle = math.degrees(math.atan2(-direction.y, direction.x))
        else:
            if euclidean_distance(self.position, self.game.player.position) > 30:
                self.generate_path()
            direction = pygame.Vector2(self.game.player.position) - self.position
            if direction.length() > 0:
                self.angle = math.degrees(math.atan2(-direction.y, direction.x))
            self.is_moving = False

        self.rect = self.image.get_rect(center=self.position)
        self.rect.center = self.position

        if euclidean_distance(self.position, self.game.player.position) <= 35:
            if not self.preparing_attack:
                self.preparing_attack = True
                self.attack_timer = pygame.time.get_ticks()

        if pygame.time.get_ticks() - self.attack_timer >= 500 and self.game.player.in_battle:
            self.attack(self.game.player)
            self.preparing_attack = False

        if self.is_moving and not self.animation_frames:
            self.play_animation(self.walking_frames, 60, True)

        if not self.is_moving and self.animation_frames == self.walking_frames:
            self.animation_frames = None


class Archer(Entity):
    def __init__(self, position, fire_rate, game):
        death_frames = [load_image(f"deathing_archer{i}.png") for i in range(0, 6)]
        damaged_frames = [load_image(f"damaged_enemy{i}.png") for i in range(1, 3)]
        super().__init__(position, health=400, death_frames=death_frames, damaged_frames=damaged_frames, game=game)

        self.fire_rate = fire_rate
        self.last_shot_time = 0
        self.shooting_frames = [load_image(f"shooting_enemy{i}.png") for i in range(0, 5)]
        self.default_frames = [load_image(f"enemy_standart{i}.png") for i in range(0, 3)]

    def can_shoot(self):
        for enemy in self.game.all_enemies:
            if enemy is not self:
                t = 15
                points = [(enemy.rect.x - t, enemy.rect.y - t),
                          (enemy.rect.x + enemy.rect.width + t, enemy.rect.y - t),
                          (enemy.rect.x + enemy.rect.width + t,
                           enemy.rect.y + enemy.rect.height + t),
                          (enemy.rect.x - t, enemy.rect.y + enemy.rect.height + t)]
                x1, y1, x2, y2 = self.game.player.position[0], self.game.player.position[1], self.position[0], \
                    self.position[1]
                res = obstacle_intersect_by_line(x1, y1, x2, y2, points, self.game.graph_points)
                if isinstance(res, list):
                    return False

        if all([type(obstacle_intersect_by_line(self.game.player.position[0], self.game.player.position[1],
                                                int(self.position[0]),
                                                int(self.position[1]),
                                                obstacle.points, self.game.graph_points)) != list for obstacle in
                self.game.all_obstacles]):
            return True
        return False

    def shoot(self):
        if pygame.time.get_ticks() - self.last_shot_time > self.fire_rate and (
                not self.animation_frames or self.animation_frames == self.default_frames):
            self.play_animation(self.shooting_frames, 50, False)
            self.last_shot_time = pygame.time.get_ticks()
            direction = (self.game.player.position - self.position).normalize()
            EnemyArrow(self.rect.center, direction, speed=4, color=(255, 255, 0), game=self.game)

    def update(self):
        super().update()

        if self.is_dying:
            return

        if self.game.player.in_battle and self.can_shoot():
            self.shoot()

        direction = self.game.player.position - self.position
        self.angle = math.degrees(math.atan2(-direction.y, direction.x))
        self.rect = self.image.get_rect(center=self.position)

        self.rect.center = self.position

        if not self.animation_frames:
            self.play_animation(self.default_frames, random.randrange(300, 350), True)


class Arrow(pygame.sprite.Sprite):
    def __init__(self, position, direction, speed, color, game):
        super().__init__(game.all_arrows, game.all_sprites)
        self.image = pygame.Surface((10, 3), pygame.SRCALPHA)
        pygame.draw.rect(self.image, color, (0, 0, 10, 3))
        self.original_image = self.image
        self.rect = self.image.get_rect(center=position)
        self.position = pygame.Vector2(position)
        self.direction = direction.normalize()
        self.speed = speed
        self.angle = math.degrees(-math.atan2(direction.y, direction.x))
        self.image = pygame.transform.rotate(self.original_image, self.angle)

        self.game = game
        self.game.shot_sound.play()

        self.collids = {}

        self.start_pos = self.position.copy()
        self.end_pos = self.start_pos + self.direction * 800
        for obstacle in game.all_obstacles:
            res = obstacle_intersect_by_line(self.start_pos[0], self.start_pos[1], self.end_pos[0], self.end_pos[1],
                                             obstacle.points, self.game.graph_points)
            if isinstance(res, list):
                for i in res:
                    self.collids[i[0]] = (i[1], i[2])

    def update(self):

        self.position += self.direction * self.speed
        self.rect.center = self.position

        for point in self.collids.keys():
            if euclidean_distance(point, self.position) <= 15:
                start_pos = pygame.Vector2(self.start_pos[0], self.start_pos[1])
                line = self.collids[point]
                point1 = pygame.Vector2(point[0], point[1])
                direction = (point1 - start_pos).normalize()

                line_vector = pygame.Vector2(line[1][0] - line[0][0], line[1][1] - line[0][1])
                normal = pygame.Vector2(-line_vector.y, line_vector.x).normalize()
                dot_product = direction.dot(normal)
                reflected_direction = direction - 2 * dot_product * normal
                create_particles(point1, 'spark.png', reflected_direction, 100, 2, 0.5, 5, game=self.game)
                self.kill()
                self.game.rikoshet_sound.play()

        if not (0 <= self.position.x <= self.game.width and 0 <= self.position.y <= self.game.height):
            self.kill()


class EnemyArrow(Arrow):
    def update(self):
        super().update()

        if pygame.sprite.collide_mask(self, self.game.player):
            self.game.player.damage(150)
            create_particles(self.position, 'blood.png', -self.direction, 200, 2, 0.5, 20, game=self.game)
            self.kill()


class PlayerArrow(Arrow):
    def update(self):
        super().update()

        for enemy in self.game.all_enemies:
            if pygame.sprite.collide_mask(self, enemy):
                enemy.damage(50)
                create_particles(self.position, 'blood.png', -self.direction, 200, 2, 0.5, 20, game=self.game)
                self.kill()
                return


class Player(AnimatedSprite):
    def __init__(self, position, size, speed, amo, typ, game):
        original_image = pygame.Surface(size, pygame.SRCALPHA)
        original_image.fill((0, 0, 255))
        super().__init__(position, original_image, game, game.all_players)

        self.game = game

        self.original_image = original_image
        self.image = self.original_image
        self.rect = self.image.get_rect(center=position)
        self.death_frames = [load_image(f"deathing_player{i}.png") for i in range(0, 5)]
        self.standing_up_frames = [load_image(f"player_standing_up{i}.png") for i in range(0, 6)]
        self.damaged_frames = [load_image(f"damaged_player{i}.png") for i in range(0, 2)]
        self.healing_frames = [load_image(f"player_healed{i}.png") for i in range(0, 2)]

        self.position = pygame.Vector2(position)
        self.speed = speed
        self.angle = 0

        self.amo = amo
        self.mask = pygame.mask.from_surface(self.image)
        self.in_battle = False
        self.is_dying = False

        self.health = 1000

        self.damage_timer = 0
        self.shoot_timer = 0
        self.shoot_cooldown = 550

        self.typ = typ

        if self.typ == 'peacefull':
            self.default_frames = [load_image(f"defaut_player{i}.png") for i in range(0, 2)]
            self.play_animation(self.standing_up_frames, 600, False)

        else:
            self.default_frames = [load_image(f"default_battle_player{i}.png") for i in range(0, 2)]

        self.attacking_frames = [load_image(f"shooting_player{i}.png") for i in range(0, 6)]
        self.falling_frames = [load_image(f"player_laying{i}.png") for i in range(0, 5)]

    def update_walk_sound(self, moving):
        if moving and self.typ == 'peacefull':
            if not self.game.mixer.get_busy():
                self.game.walk_sound.play(-1)
        else:
            self.game.walk_sound.stop()

    def update(self):
        super().update()

        if self.is_dying:
            if self.animation_complete:
                self.game.all_players.remove(self)
            return

        if self.animation_frames not in [self.standing_up_frames, self.falling_frames]:
            self.in_battle = True
            if not self.game.camera:
                mouse_pos = pygame.mouse.get_pos()
                direction = pygame.Vector2(mouse_pos) - self.position
                self.angle = -math.degrees(math.atan2(direction.y, direction.x)) + 90
                self.rect = self.image.get_rect(center=self.rect.center)

            self.mask = pygame.mask.from_surface(self.image)

            keys = pygame.key.get_pressed()
            mouse_buttons = pygame.mouse.get_pressed()

            initial_position = self.position.copy()

            moving = False
            if keys[pygame.K_w]:
                if self.game.camera:
                    self.angle = 180
                self.position.y -= self.speed
                moving = True
            if keys[pygame.K_s]:
                if self.game.camera:
                    self.angle = 0
                self.position.y += self.speed
                moving = True
            if keys[pygame.K_d]:
                if self.game.camera:
                    self.angle = 90
                self.position.x += self.speed
                moving = True
            if keys[pygame.K_a]:
                if self.game.camera:
                    self.angle = -90
                self.position.x -= self.speed
                moving = True

            self.update_walk_sound(moving)

            current_time = pygame.time.get_ticks()
            if mouse_buttons[0] and current_time - self.shoot_timer >= self.shoot_cooldown:
                self.shoot()
                self.shoot_timer = current_time

            self.rect.center = self.position

            for obstacle in self.game.all_obstacles:
                if pygame.sprite.collide_mask(self, obstacle):
                    self.position = initial_position
                    self.rect.center = self.position
                    break

            if not self.animation_frames:
                self.play_animation(self.default_frames, 1000, True)

    def shoot(self):
        if self.amo > 0:
            self.amo -= 1
            mouse_pos = pygame.mouse.get_pos()
            direction = pygame.Vector2(mouse_pos) - self.game.player.position
            if direction.length() > 0:
                self.play_animation(self.attacking_frames, 50, False)
                direction.normalize_ip()
                PlayerArrow(self.game.player.position, direction, color=(255, 255, 0), game=self.game, speed=4)

    def damage(self, damage):
        if not self.is_dying:
            self.health -= damage
            self.play_animation(self.damaged_frames, 100, False)

            if self.health <= 0:
                self.in_battle = False
                self.is_dying = True
                self.play_animation(self.death_frames, 400, False)

    def heal(self, xp):
        if not self.health == 1000:
            self.health = min(self.health + xp, 1000)
            self.play_animation(self.healing_frames, 200, False)


# Класс НПС. Пу-пу-пу x2

class NPS(AnimatedSprite):
    def __init__(self, position, size, ind, ismain, game):
        animation_frames = [pygame.transform.scale2x(load_image(name)) for name in settings.nps_textures[ind]]
        original_image = animation_frames[0]
        super().__init__(position, original_image, game, game.all_npc)

        self.game = game

        self.frames = animation_frames

        self.image = original_image
        self.rect = self.image.get_rect(center=position)
        self.position = pygame.Vector2(position)
        self.mask = pygame.mask.from_surface(self.image)
        self.replicas = []
        self.press_space_timer = 0
        self.press_f_timer = 0
        self.ind = ind
        self.num_phrse = 0
        self.is_dialogue = False
        self.can_show_next = True
        self.current_text = ""
        self.text_index = 0
        self.last_letter_time = 0
        self.sound_timer = 0
        self.typing_sound = self.game.mixer.Sound(load_sound("sound (2).mp3"))
        self.typing_sound.set_volume(0.5)
        self.ismain = ismain
        self.available_for_dialogue = True

        self.play_animation(self.frames, 300, True)

    def update(self):
        super().update()

        if self.is_dialogue and self.within_a_radius(self.position[0], self.position[1], self.game.player.position[0],
                                                     self.game.player.position[1]) and self.available_for_dialogue:
            if pygame.time.get_ticks() - self.press_space_timer > 500 and pygame.key.get_pressed()[pygame.K_SPACE] \
                    and self.can_show_next:
                self.can_show_next = False
                self.num_phrse += 1
                self.current_text = ""
                self.text_index = 0
                self.last_letter_time = 0
                self.press_space_timer = pygame.time.get_ticks()
                self.typing_sound.stop()
            if not pygame.key.get_pressed()[pygame.K_SPACE]:
                self.can_show_next = True
            if self.num_phrse == len(self.replicas):
                self.num_phrse = 0
                self.is_dialogue = False
                self.typing_sound.stop()
            self.print_replicas(self.replicas[self.num_phrse])
            self.skip_dialogue()
        self.can_start_talking()
        self.position = [self.rect.x, self.rect.y]

    def skip_dialogue(self):
        font = pygame.font.Font(None, 30)
        text = font.render('Вы можете пропустить диалог, нажав "E"', False, 'white')
        self.game.texts.append((text, (15, 15)))
        if pygame.key.get_pressed()[pygame.K_e]:
            if self.ismain:
                print('завершаю уровень нпс')
                self.game.switch_to_next_level = True
            self.is_dialogue = False
            self.available_for_dialogue = False

    def within_a_radius(self, x1, y1, x2, y2):
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2) <= 60

    def can_talk(self):
        return all([nps == self or nps.is_dialogue is False for nps in self.game.all_npc])

    def can_start_talking(self):
        if self.within_a_radius(self.position[0], self.position[1], self.game.player.position[0],
                                self.game.player.position[1]) and self.available_for_dialogue:
            if not self.is_dialogue and self.can_talk():
                text = self.game.font.render('Нажмите кнопку "F", чтобы начать разговор.', 1, 'white')

                self.game.texts.append((text, (
                    self.position[0] - 125 - self.game.camera.offset.x,
                    self.position[1] - 60 - self.game.camera.offset.y)))

                self.typing_sound.stop()
            keys = pygame.key.get_pressed()
            if keys[pygame.K_f] and pygame.time.get_ticks() - self.press_f_timer >= 1000 and self.can_talk() \
                    and not self.is_dialogue:
                self.press_f_timer = 0
                self.start_dialogue()
        else:
            self.typing_sound.stop()
            self.is_dialogue = False
            self.current_text = ""
            self.text_index = 0
            self.last_letter_time = 0
            self.num_phrse = 0

    def start_dialogue(self):
        self.replicas = self.get_replicas()
        self.is_dialogue = True
        self.num_phrse = 0

    def get_replicas(self):
        if not self.replicas:
            replicas = []
            with open('Data/Texts/nps_replicas.txt', 'r', encoding='utf-8') as text:
                script = text.read().split('\n')
            for replica in script:
                if f'{self.ind}:  ' in replica:
                    replicas.append(replica[6:])
                elif f'{self.ind}:205' in replica:
                    replicas.append(replica[4:])
            return replicas
        return self.replicas

    def print_replicas(self, replica):
        if self.replicas[self.num_phrse] == '---':
            self.num_phrse = 0
            self.is_dialogue = False
            if self.ismain:
                self.game.switch_to_next_level = True
                print('завершаю уровень нпс')
            self.available_for_dialogue = False
            return

        if 'name' in replica:
            replica = replica.replace('name', settings.name)

        coords = self.position[0] - 100 - self.game.camera.offset.x, self.position[1] - 50 - self.game.camera.offset.y

        if replica.startswith('205'):
            color = 'yellow'
            replica = replica[3:]
            coords = self.game.player.position[0] - 100 - self.game.camera.offset.x, self.game.player.position[
                1] + 50 - self.game.camera.offset.y
        else:
            color = 'white'

        current_time = pygame.time.get_ticks()
        if current_time - self.last_letter_time > 50:
            if self.text_index < len(replica):
                self.current_text += replica[self.text_index]
                self.text_index += 1
                self.last_letter_time = current_time
                if current_time - self.sound_timer > 500:
                    self.typing_sound.stop()
                    self.typing_sound.play()
                    self.sound_timer = current_time
            else:
                self.typing_sound.stop()

        text = self.game.font.render(self.current_text, True, color)
        self.game.texts.append((text, coords))


class Camera:
    def __init__(self, width, height):
        self.offset = pygame.Vector2(0, 0)
        self.width = width
        self.height = height

    def update(self, target_position):
        self.offset.x = target_position.rect.x - self.width // 2
        self.offset.y = target_position.rect.y - self.height // 2

    def apply(self, entity, player_position):
        rel_pos = pygame.Vector2(entity.rect.center) - player_position
        new_pos = rel_pos + pygame.Vector2(self.width // 2, self.height // 2)
        return entity.image, new_pos


class AmmoDisplay(pygame.sprite.Sprite):
    def __init__(self, position, game):
        super().__init__(game.ui_sprites, game.all_sprites)
        self.position = position

        self.bullet_image = load_image('bullet.png')
        self.bullet_width, self.bullet_height = self.bullet_image.get_size()

        self.image = pygame.Surface(
            (self.bullet_width + 50, self.bullet_height), pygame.SRCALPHA
        )
        self.rect = self.image.get_rect(topleft=position)

        self.game = game

    def update(self):

        self.image = pygame.Surface(
            (self.bullet_width + 50, self.bullet_height), pygame.SRCALPHA
        )
        self.rect = self.image.get_rect(topleft=self.position)

        amo = self.game.player.amo
        ammo_text = f"{amo}"
        if amo > 10:
            color = 'white'
        elif 3 < amo <= 10:
            color = 'yellow'
        else:
            color = 'red'

        font = pygame.font.SysFont('verdana', 20)
        text_surface = font.render(ammo_text, True, color, None)
        self.image.blit(self.bullet_image, (0, 0))
        self.image.blit(text_surface, (self.bullet_width + 2, 2))


class HealthBar(pygame.sprite.Sprite):
    def __init__(self, position, size, max_health, color=(255, 0, 0), bg_color=(50, 50, 50), game=None):
        super().__init__(game.ui_sprites, game.all_sprites)
        self.position = position
        self.size = size
        self.max_health = max_health
        self.current_health = max_health
        self.color = color
        self.bg_color = bg_color
        self.image = pygame.Surface(size, pygame.SRCALPHA)
        self.rect = self.image.get_rect(bottomright=position)

        self.game = game

    def update(self):
        self.current_health = max(0, min(self.game.player.health, self.max_health))
        self.image.fill(self.bg_color)
        if self.current_health > 0:
            health_width = int((self.current_health / self.max_health) * self.size[0])
            pygame.draw.rect(self.image, self.color, (0, 0, health_width, self.size[1]))


class Particle(pygame.sprite.Sprite):
    def __init__(self, image, pos, direction, speed=1, max_distance=100, randomness=0.5, game=None):
        super().__init__(game.all_particles, game.all_sprites)

        fire = [load_image(image)]

        self.original_image = random.choice(fire)
        self.image = self.original_image.copy()

        self.start_pos = pos
        self.max_distance = max_distance

        self.rect = self.image.get_rect()
        self.direction = [speed * (direction[0] + random.uniform(-randomness, randomness)),
                          speed * (direction[1] + random.uniform(-randomness, randomness))]

        self.speed = speed

        self.rect.center = pos
        self.gravity = 0.05

        self.mask = pygame.mask.from_surface(self.image)

        self.game = game

    def update(self):
        self.direction[1] += self.gravity
        self.rect.x += self.speed * self.direction[0]
        self.rect.y += self.speed * self.direction[1]

        distance = euclidean_distance(self.start_pos, self.rect.center)
        alpha = max(0, 255 * (1 - distance / self.max_distance))
        self.image = self.original_image.copy()
        self.image.set_alpha(alpha)

        if distance >= self.max_distance:
            self.kill()
            return

        if not self.rect.colliderect((0, 0, self.game.width, self.game.height - 30)):
            self.kill()
            return

        for obstacle in self.game.all_obstacles:
            if pygame.sprite.collide_mask(self, obstacle):
                self.kill()
                return


def create_particles(position, image, direction, max_distance, speed, randomness, particle_count, game):
    for _ in range(particle_count):
        Particle(image, position, direction, speed, max_distance, randomness, game=game)
