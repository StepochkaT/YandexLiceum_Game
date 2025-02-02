import pygame
import random


class TwinklingStars:
    def __init__(self, window_width, window_height, max_stars=200):
        self.window_width = window_width
        self.window_height = window_height
        self.max_stars = max_stars
        self.stars = self.generate_stars()
        self.clock = pygame.time.Clock()

    def generate_stars(self):
        stars = []
        for _ in range(self.max_stars):
            star_radius = random.randint(1, 3)
            star_color = (255, 255, 237)
            star_position = (random.randint(0, self.window_width), random.randint(0, self.window_height))
            star_expand = True
            star_expand_speed = random.uniform(0.1, 0.5)
            stars.append((star_radius, star_color, star_position, star_expand, star_expand_speed))
        return stars

    def update_stars(self):
        for i in range(self.max_stars):
            star_radius, star_color, star_position, star_expand, star_expand_speed = self.stars[i]

            if star_expand:
                star_radius += star_expand_speed
                if star_radius >= 5:
                    star_expand = False
            else:
                star_radius -= star_expand_speed
                if star_radius <= 1:
                    star_expand = True

            star_position = (
                star_position[0] + random.randint(-1, 1),
                star_position[1] + random.randint(-1, 1)
            )

            self.stars[i] = (star_radius, star_color, star_position, star_expand, star_expand_speed)

    def draw_stars(self, screen):
        for star in self.stars:
            star_radius, star_color, star_position, _, _ = star
            pygame.draw.circle(screen, star_color, star_position, int(star_radius))

    def draw(self, screen):
        self.update_stars()
        self.draw_stars(screen)


def display_text(screen, font, lines, total, y):
    if total < len(lines):
        txt_surf = font.render(lines[total].strip(), True, [255, 255, 255])
        alpha_img = pygame.Surface(txt_surf.get_size(), pygame.SRCALPHA)
        alpha_img.fill((255, 255, 255, y))
        txt_surf.blit(alpha_img, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        screen.blit(txt_surf, (50, screen.get_height() // 2))

        if y < 255:
            y += 1

    return y


if __name__ == "__main__":
    pygame.init()
    WINDOW_WIDTH = 800
    WINDOW_HEIGHT = 600
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Мерцающие звезды")

    font = pygame.font.Font(None, 50)
    y = 0
    with open("vved.txt", encoding="utf8") as f:
        lines = f.readlines()

    total = 0
    stars = TwinklingStars(WINDOW_WIDTH, WINDOW_HEIGHT)
    clock = pygame.time.Clock()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    total += 1
                    y = 0

        screen.fill((0, 0, 0))
        stars.draw(screen)
        y = display_text(screen, font, lines, total, y)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
