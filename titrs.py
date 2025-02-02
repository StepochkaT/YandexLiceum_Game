import pygame
from pygame.locals import *
from star import TwinklingStars
from math_funcs import load_image, load_sound

pygame.init()
screen = pygame.display.set_mode((1000, 750))
WIDTH, HEIGHT = 1000, 750
MAX_FPS = 60
screen_r = screen.get_rect()
font = pygame.font.SysFont("Arial", 40)
clock = pygame.time.Clock()
phon = load_image('background.jpg')


def fade():
    running = True
    fade_alpha = 0
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        fade_surface = pygame.Surface((WIDTH, HEIGHT))
        fade_surface.fill((0, 0, 0))
        fade_surface.set_alpha(fade_alpha)
        screen.blit(fade_surface, (0, 0))

        fade_alpha += 6
        if fade_alpha >= 55:
            fade_alpha = 255
            running = False
        pygame.display.flip()
        clock.tick(MAX_FPS)


def start_text():
    pygame.mixer.music.load(load_sound("menu_song.mp3"))
    pygame.mixer.music.play(-1)
    font2 = pygame.font.Font(None, 50)
    y = 0
    with open("Data/Texts/the_end_monologue.txt", encoding="utf8") as f:
        lines = f.readlines()

    total = 0
    stars = TwinklingStars(1000, 750)
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
                    if total > len(lines) - 1:
                        fade()
                        running = False
                        titr()

        screen.fill((0, 0, 0))
        stars.draw(screen)

        def display_text(screen, font2, lines, total, y):
            if total < len(lines):
                txt_surf = font2.render(lines[total].strip(), True, [255, 255, 255])
                alpha_img = pygame.Surface(txt_surf.get_size(), pygame.SRCALPHA)
                alpha_img.fill((255, 255, 255, y))
                txt_surf.blit(alpha_img, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                screen.blit(txt_surf, (10, screen.get_height() // 2))

                if y < 255:
                    y += 5

            return y

        y = display_text(screen, font2, lines, total, y)

        pygame.display.flip()
        clock_star.tick(60)
        f.close()


def titr():
    credit_list = ["ПОЗДРАВЛЯЕМ!", "ВЫ ПРОШЛИ ИГРУ", " ", "Продюсеры - Диана", "Исполнительный продюсер - Елизавета",
                   "Ассоушиэйт продюсер - Степан", "Сценарист - Елизавета", "Старший раскадровщик - Диана",
                   "Раскадровщик - Елизавета", "Локейшн менеджер - Степан", "Оператор-постановщик - Степан",
                   "Оператор камеры - Елизавета", "Супервайзер по спецэффектам - Степан", "Пиротехников - Степан",
                   "Звукорежисер - Диана", "Помощник звукорежисера - Степан", "Вертолёт ми-8 - ???!",
                   "Редактор диалогов - Елизавета", "Директор главного меню - Диана", "Художник - помощница Елизаветы"]

    texts = []
    for i, line in enumerate(credit_list):
        s = font.render(line, 1, (255, 255, 255))
        r = s.get_rect(centerx=screen_r.centerx, y=screen_r.bottom + i * 45)
        texts.append((r, s))

    logo = load_image("end_logo.png").convert_alpha()
    x = -100
    y = 700
    while True:
        screen.fill((0, 0, 0))
        screen.blit(phon, (0, 0))
        screen.blit(phon, (737, 0))
        screen.blit(phon, (0, 415))
        screen.blit(phon, (737, 415))
        for e in pygame.event.get():
            if e.type == QUIT or e.type == KEYDOWN and e.key == pygame.K_ESCAPE:
                return
        for r, s in texts:
            r.move_ip(0, -1)
            screen.blit(s, r)
        if not screen_r.collidelistall([r for (r, _) in texts]):
            screen.blit(logo, (x, y))
            y -= 1

        pygame.display.update()
        clock.tick(60)


if __name__ == '__main__':
    start_text()
