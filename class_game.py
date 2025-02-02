import random
from itertools import combinations

from math_funcs import obstacle_intersect_by_line, euclidean_distance, load_sound, seconds_to_mm_ss
from entity_classes import Object, Enemy, Archer, Player, NPS, Camera, AmmoDisplay, HealthBar

import pygame

import titrs

pygame.init()


class Game:
    def __init__(self, levels, width, height):

        self.width, self.height = width, height
        self.screen = pygame.display.set_mode((self.width, self.height))
        self.clock = pygame.time.Clock()
        self.running = True
        self.game_over = False
        self.switch_to_next_level = False
        self.level_complete = False
        self.level_complete_time = None
        self.music_path = None

        self.player = None
        self.camera = None
        self.all_sprites = pygame.sprite.Group()
        self.all_enemies = pygame.sprite.Group()
        self.all_arrows = pygame.sprite.Group()
        self.all_particles = pygame.sprite.Group()
        self.all_obstacles = pygame.sprite.Group()
        self.all_npc = pygame.sprite.Group()
        self.ui_sprites = pygame.sprite.Group()
        self.all_players = pygame.sprite.Group()

        self.font = pygame.font.Font(None, 20)
        self.mixer = pygame.mixer

        self.static_graph = {}
        self.graph_points = []

        self.levels = levels
        self.current_level_index = 0

        self.left_enemies = []

        self.texts = []
        self.text_queue = []

        self.shot_sound = self.mixer.Sound(load_sound('shot.mp3'))
        self.shot_sound.set_volume(0.4)
        self.walk_sound = self.mixer.Sound(load_sound('walk.mp3'))
        self.walk_sound.set_volume(0.9)
        self.rikoshet_sound = self.mixer.Sound(load_sound('rikoshet.mp3'))
        self.rikoshet_sound.set_volume(0.4)
        self.knife_sound = self.mixer.Sound(load_sound('knife.mp3'))
        self.knife_sound.set_volume(0.9)
        self.hit_sound = self.mixer.Sound(load_sound('hit.mp3'))
        self.knife_sound.set_volume(0.9)
        self.dead_sound = self.mixer.Sound(load_sound('dead.mp3'))
        self.knife_sound.set_volume(0.9)

        self.deaths = 0
        self.shots_made = 0
        self.pass_time = None

    def load_level(self, level_data):
        pygame.mixer.music.stop()
        self.left_enemies = []

        for sprite in self.all_sprites:
            for group in sprite.groups():
                group.remove(sprite)

        level_type = level_data['type']

        if level_type == 'battle':
            self.music_path = f'battle{random.randrange(1, 5)}.mp3'
            self.camera = None
            if 'archers' in level_data:
                for archer in level_data['archers']:
                    Archer(archer['position'], fire_rate=500, game=self)
            if 'enemies' in level_data:
                Enemy(level_data['enemies'][0]['position'], speed=1.4, game=self)
                for enemy in level_data['enemies'][1:]:
                    self.left_enemies.append(enemy)

            self.player = Player(
                position=level_data["player"]["position"],
                size=(20, 20),
                speed=1.5,
                amo=level_data["player"]["amo"],
                typ=level_type,
                game=self
            )

            HealthBar(position=(0.97 * self.width, 0.97 * self.height), size=(200, 20), max_health=1000, game=self)
            AmmoDisplay((0.57 * self.width, 0.935 * self.height), game=self)

        else:
            self.music_path = 'chill.mp3'
            self.camera = Camera(self.width, self.height)

            if 'npc' in level_data:
                for npc in level_data['npc']:
                    NPS(position=npc['position'], size=npc['size'], ind=npc['id'], ismain=npc['is_main'],
                        game=self)

            self.player = Player(
                position=level_data["player"]["position"],
                size=(20, 20),
                speed=1.5,
                amo=0,
                typ=level_type,
                game=self
            )

        if 'obstacles' in level_data:
            for obstacle in level_data['obstacles']:
                if 'angle' in obstacle:
                    angle = obstacle['angle']
                else:
                    angle = 0
                Object(obstacle['points'], obstacle['texture'], self, angle, self.all_obstacles)

        if level_type == 'battle':
            self.graph_points = []
            for obstacle in self.all_obstacles:
                for point in obstacle.points:
                    if 0 < point[0] < self.width and 0 < point[1] < self.height:
                        self.graph_points.append(point)

            self.static_graph = {point: [] for point in self.graph_points}

            for point1, point2 in combinations(self.graph_points, 2):

                if all([type(obstacle_intersect_by_line(point1[0], point1[1], point2[0], point2[1],
                                                        obstacle.points, self.graph_points)) != list for obstacle in
                        self.all_obstacles]):
                    distance = euclidean_distance(point1, point2)
                    self.static_graph[point1].append((point2, distance))
                    self.static_graph[point2].append((point1, distance))

        pygame.mixer.music.load(load_sound(self.music_path))
        pygame.mixer.music.set_volume(0.5)
        pygame.mixer.music.play(-1)

    def spawn_new_enemies(self):
        if self.left_enemies:
            enemy = self.left_enemies.pop()
            Enemy(enemy['position'], speed=1.4, game=self)

    def show_text(self, text, duration, font_size=40):
        font = pygame.font.SysFont(None, font_size)
        lines = text.split("\n")
        y_offset = self.height // 2 - (len(lines) * font_size) // 2

        for line in lines:
            text_surface = font.render(line, True, (255, 255, 255))
            text_rect = text_surface.get_rect(center=(self.width // 2, y_offset))
            self.screen.blit(text_surface, text_rect)
            y_offset += font_size + 5

        pygame.display.flip()
        pygame.time.delay(duration)

    def add_shaky_text(self, text, coords, color='white', font_size=20, duration=2000,
                       shake_intensity=2, shake_frequency=100):

        font = pygame.font.Font(None, font_size)
        expiration_time = pygame.time.get_ticks() + duration
        self.text_queue.append({
            'type': 'shaky',
            'text': text,
            'coords': coords,
            'color': color,
            'font': font,
            'expiration_time': expiration_time,
            'shake_intensity': shake_intensity,
            'shake_frequency': shake_frequency,
            'last_shake_update': 0,
            'shakes': [self.random_offset(shake_intensity) for _ in text]
        })

    def draw_texts(self):
        current_time = pygame.time.get_ticks()
        for text_data in self.text_queue[:]:
            if current_time < text_data['expiration_time']:
                if text_data['type'] == 'shaky':
                    self._draw_shaky_text(
                        text_data['text'],
                        text_data['coords'],
                        text_data['font'],
                        text_data['color'],
                        text_data['shake_intensity'],
                        text_data['shake_frequency'],
                        text_data
                    )
            else:
                self.text_queue.remove(text_data)

    def _draw_shaky_text(self, text, coords, font, color, shake_intensity, shake_frequency, text_data):
        current_time = pygame.time.get_ticks()

        if current_time - text_data['last_shake_update'] > shake_frequency:
            text_data['shakes'] = [self.random_offset(shake_intensity) for _ in text]
            text_data['last_shake_update'] = current_time

        x, y = coords
        for i, char in enumerate(text):
            offset_x, offset_y = text_data['shakes'][i]
            char_surface = font.render(char, True, color)
            self.screen.blit(char_surface, (x + offset_x, y + offset_y))
            x += char_surface.get_width()

    @staticmethod
    def random_offset(intensity):
        return random.randint(-intensity, intensity), random.randint(-intensity, intensity)

    def show_game_over_message(self):
        font = pygame.font.SysFont(None, 35)
        text_surface = font.render('Вы умерли. Нажмите пробел', True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(self.width // 2, self.height // 2))
        self.screen.blit(text_surface, text_rect)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if self.game_over and event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                self.load_level(self.levels[self.current_level_index])
                self.game_over = False

    def update(self):
        if len(self.all_players) == 0 and not self.level_complete:
            pygame.mixer.music.set_volume(0.2)
            self.game_over = True
            self.show_game_over_message()
            return

        if len(self.all_enemies) == 0 and len(self.left_enemies) == 0 and not self.switch_to_next_level and \
                self.levels[self.current_level_index]['type'] == 'battle' and not self.level_complete:
            self.switch_to_next_level = True
            self.player.play_animation(self.player.falling_frames, 300, False)
            pygame.mixer.music.set_volume(0.2)

        if self.switch_to_next_level and self.player.animation_frames != self.player.falling_frames:
            self.switch_to_next_level = False
            if self.current_level_index + 1 >= len(self.levels):
                pygame.mixer.music.stop()
                self.running = False
                titrs.start_text()
                return

            if self.levels[self.current_level_index + 1]['type'] == 'battle':
                self.add_shaky_text("Убей всех врагов", (self.width / 2 - 75, self.height / 2), color='red',
                                    font_size=40,
                                    shake_intensity=2, duration=5000, shake_frequency=25)
            else:
                self.show_text(
                    f'Уровень пройден\nВремя прохождения:{seconds_to_mm_ss((pygame.time.get_ticks() - self.pass_time) / 1000)}'
                    f'\nСмертей: {self.deaths}\nВыстрелов сделано: {self.shots_made}',
                    3000, 40)

            self.current_level_index += 1
            self.deaths = 0
            self.shots_made = 0
            self.pass_time = pygame.time.get_ticks()
            self.level_complete = True
            self.level_complete_time = pygame.time.get_ticks()
            self.switch_to_next_level = False

        if self.level_complete:
            if pygame.time.get_ticks() - self.level_complete_time > 2000:
                self.level_complete = False
                self.load_level(self.levels[self.current_level_index])

        self.all_sprites.update()

    def draw(self):
        if not self.running:
            return
        if self.game_over or self.level_complete:
            self.draw_texts()
            pygame.display.flip()
            return
        if self.camera:
            self.camera.update(self.player)
            for sprite in self.all_sprites:
                if sprite == self.player:
                    image, _ = self.camera.apply(sprite, self.player.position)
                    rect = image.get_rect(center=(self.width // 2, self.height // 2))
                    self.screen.blit(image, rect.topleft)
                else:
                    image, new_pos = self.camera.apply(sprite, self.player.position)
                    rect = image.get_rect(center=new_pos)
                    self.screen.blit(image, rect.topleft)
        else:
            self.all_sprites.draw(self.screen)

        for text, coords in self.texts:
            self.screen.blit(text, coords)
        self.texts = []

        pygame.display.flip()

    def run(self):
        self.load_level(self.levels[self.current_level_index])
        while self.running:
            if self.levels[self.current_level_index]['type'] == 'battle':
                self.screen.fill((25, 25, 25))
            else:
                self.screen.fill((0, 0, 0))
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)
        pygame.quit()
