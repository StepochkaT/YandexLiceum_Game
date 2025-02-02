import pygame
from test import ImageButton
from star import TwinklingStars
import time

pygame.init()
WIDTH, HEIGT = 1000, 750
MAX_FPS = 40

screen = pygame.display.set_mode((WIDTH, HEIGT))
pygame.display.set_caption('Menu play')
phon = pygame.image.load('фон.jpg')  # 736*414
cursor = pygame.image.load('курсор.jpg')
pygame.mouse.set_visible(False)  # скрытие стандартного курсора
clock = pygame.time.Clock()
clock2 = pygame.time.Clock()
pygame.mixer.music.load("menu_song.mp3")
pygame.mixer.music.play(-1)


def main_menu():
    start_button = ImageButton(WIDTH / 2 - (252 / 2), 250, 252, 74, 'Новая игра', 'кнопка1.jpg', 'кнопка2.jpg',
                               'клик2.mp3')
    audio_button = ImageButton(WIDTH / 2 - (252 / 2), 400, 252, 74, 'Аудио', 'кнопка1.jpg', 'кнопка2.jpg',
                               'клик2.mp3')
    exit_button = ImageButton(WIDTH / 2 - (252 / 2), 550, 252, 74, 'Выход', 'кнопка1.jpg', 'кнопка2.jpg', 'клик2.mp3')
    logos = ['сераая__лого.png', 'синяя__лого.png', 'светлая__лого.png']
    ind_logo = 0
    running = True
    while running:
        screen.fill((0, 0, 0))
        screen.blit(phon, (0, 0))
        screen.blit(phon, (737, 0))
        screen.blit(phon, (0, 415))
        screen.blit(phon, (737, 415))
        logo = pygame.image.load(logos[ind_logo]).convert_alpha()
        logo = pygame.transform.scale(logo, (500, 250))
        screen.blit(logo, (WIDTH // 3.5, 0))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                if logo.get_rect().collidepoint(x, y):
                    ind_logo += 1
                    if ind_logo == 3:
                        ind_logo = 0



            elif event.type == pygame.USEREVENT and event.button == start_button:
                print('Переход по кнопке "Новая игра"')
                fade()
                new_game()
            elif event.type == pygame.USEREVENT and event.button == audio_button:
                print('Переход по кнопке "Аудио"')
                fade()
                audio()
            elif event.type == pygame.USEREVENT and event.button == exit_button:
                print('Переход по кнопке "Выход"')
                running = False
            for btn in [start_button, audio_button, exit_button]:
                btn.handle_event(event)

        for btn in [start_button, audio_button, exit_button]:
            btn.check_hover(pygame.mouse.get_pos())
            btn.draw(screen)

        x, y = pygame.mouse.get_pos()
        screen.blit(cursor, (x, y))
        pygame.display.flip()


def new_game():
    back_button = ImageButton(0, 0, 150, 50, 'Назад', 'кнопка1.jpg', 'кнопка2.jpg', 'клик2.mp3')
    ready = ImageButton(WIDTH / 2 - (252 / 2), 400, 252, 74, 'Начать!', 'кнопка1.jpg', 'кнопка2.jpg', 'клик2.mp3')
    name = ''
    need_input = False
    running = True
    while running:
        screen.fill((0, 0, 0))
        screen.fill((0, 0, 0))
        screen.blit(phon, (0, 0))
        screen.blit(phon, (737, 0))
        screen.blit(phon, (0, 415))
        screen.blit(phon, (737, 415))
        font = pygame.font.Font(None, 60)
        text_surface = font.render('Нажмите на TAB, чтобы ввести имя:', True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(WIDTH / 2, 150))
        screen.blit(text_surface, text_rect)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
            elif event.type == pygame.USEREVENT and event.button == back_button:
                fade()
                running = False
            elif event.type == pygame.USEREVENT and event.button == ready:
                fade()
                if len(name) == 0:
                    name = 'Безымянный'
                start_text()
            if need_input and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    need_input = False
                    name = ''
                elif event.key == pygame.K_BACKSPACE:
                    name = name[:-1]
                else:
                    if len(name) < 20:
                        name += event.unicode
            for btn in [back_button, ready]:
                btn.handle_event(event)
        for btn in [back_button, ready]:
            btn.check_hover(pygame.mouse.get_pos())
            btn.draw(screen)

        key = pygame.key.get_pressed()
        if key[pygame.K_TAB]:
            need_input = True

        x, y = pygame.mouse.get_pos()
        screen.blit(cursor, (x, y))

        f = pygame.font.Font(None, 80)
        text = f.render(name, True, (255, 255, 255))
        place = text.get_rect(center=(WIDTH / 2, 300))
        screen.blit(text, place)
        pygame.display.flip()
        pygame.display.update()


def start_text():
    font = pygame.font.Font(None, 50)
    y = 0
    with open("vved.txt", encoding="utf8") as f:
        lines = f.readlines()

    total = 0
    stars = TwinklingStars(WIDTH, HEIGT)
    clock_star = pygame.time.Clock()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                fade()
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    total += 1
                    y = 0
                    if total > len(lines):
                        fade()
                        running = False
                        # вызов игры

        screen.fill((0, 0, 0))
        stars.draw(screen)  # рисуем звезды

        def display_text(screen, font, lines, total, y):
            if total < len(lines):
                txt_surf = font.render(lines[total].strip(), True, [255, 255, 255])
                alpha_img = pygame.Surface(txt_surf.get_size(), pygame.SRCALPHA)
                alpha_img.fill((255, 255, 255, y))
                txt_surf.blit(alpha_img, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                screen.blit(txt_surf, (100, screen.get_height() // 2))

                if y < 255:
                    y += 1

            return y

        y = display_text(screen, font, lines, total, y)  # показываем текст

        pygame.display.flip()
        clock_star.tick(60)
        f.close()


def audio():
    song_yes = pygame.image.load('sound_yes.png').convert_alpha()
    song_yes = pygame.transform.scale(song_yes, (80, 80))
    song_no = pygame.image.load('sound_no.png').convert_alpha()
    song_no = pygame.transform.scale(song_no, (80, 80))
    current_song = song_yes
    sprite_up = AnimatedSprite('sound_plus.png', frame_count=4, frame_duration=0.3)
    sprite_down = AnimatedSprite('sound_min.png', frame_count=4, frame_duration=0.3)
    current_sprite = None
    running = True
    flPause = False
    vol = 1
    while running:
        screen.fill((0, 0, 0))
        screen.blit(phon, (0, 0))
        screen.blit(phon, (737, 0))
        screen.blit(phon, (0, 415))
        screen.blit(phon, (737, 415))
        text(60, 'Настройки музыки:', 100)
        text(45, 'Нажмите на ПРОБЕЛ, чтобы выключить фоновую музыку', 200)
        text(45, 'Нажмите на СТРЕЛОЧКУ ВНИЗ,', 350)
        text(45, 'чтобы убавить громкость фоновой музыки', 380)
        text(45, 'Нажмите на СТРЕЛОЧКУ ВВЕРХ,', 530)
        text(45, 'чтобы прибавить громкость фоновой музыке,', 560)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    flPause = not flPause
                    if flPause:
                        pygame.mixer.music.pause()
                    else:
                        pygame.mixer.music.unpause()
                    current_song = song_no if current_song == song_yes else song_yes
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_DOWN:
                    vol -= 0.2
                    if vol < 0.2:
                        vol = 0
                    pygame.mixer.music.set_volume(vol)
                    current_sprite = sprite_down
                if event.key == pygame.K_UP:
                    vol += 0.2
                    if vol > 0.8:
                        vol = 1
                    pygame.mixer.music.set_volume(vol)
                    current_sprite = sprite_up
        screen.blit(current_song, (450, 230))
        if current_sprite:
            current_sprite.update()  # Обновляем анимацию
            if current_sprite == sprite_down:
                screen.blit(current_sprite.image, (450, 410))
            else:
                screen.blit(current_sprite.image, (450, 590))
        pygame.display.flip()


def fade():
    running = True
    fade_alpha = 0
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        fade_surface = pygame.Surface((WIDTH, HEIGT))
        fade_surface.fill((0, 0, 0))
        fade_surface.set_alpha(fade_alpha)  # заполнение прозрачности на черную для перехода
        screen.blit(fade_surface, (0, 0))

        fade_alpha += 6
        if fade_alpha >= 55:
            fade_alpha = 255
            running = False
        pygame.display.flip()
        clock.tick(MAX_FPS)  # теперь затемнение плавное


def text(sixe, text, y):
    font = pygame.font.Font(None, sixe)
    text_surface = font.render(text, True, (255, 255, 255))
    text_rect = text_surface.get_rect(center=(WIDTH / 2, y))
    screen.blit(text_surface, text_rect)


class ImageSprite(pygame.sprite.Sprite):
    def __init__(self, image_path):
        super().__init__()
        self.image = pygame.image.load(image_path)
        self.rect = self.image.get_rect()


class AnimatedSprite(pygame.sprite.Sprite):
    def __init__(self, image_path, frame_count, frame_duration):
        super().__init__()
        self.original_image = pygame.image.load(image_path)
        self.frame_count = frame_count
        self.frame_duration = frame_duration
        self.current_frame = 0
        self.last_update = time.time()
        self.update_image()

    def update_image(self):
        # Извлекаем текущий кадр
        frame_width = self.original_image.get_width() // self.frame_count
        frame_rect = pygame.Rect(self.current_frame * frame_width, 0, frame_width, self.original_image.get_height())
        self.image = self.original_image.subsurface(frame_rect)
        self.image = pygame.transform.scale(self.image, (100, 100))
        self.rect = self.image.get_rect()

    def update(self):
        # Обновление текущего кадра
        now = time.time()
        if now - self.last_update > self.frame_duration:
            self.current_frame = (self.current_frame + 1) % self.frame_count
            self.last_update = now
            self.update_image()  # Обновляем изображение


if __name__ == '__main__':
    main_menu()
