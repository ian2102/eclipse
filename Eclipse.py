import pygame
import random
import numpy as np
import os
import sys

pygame.init()

VERSION = "Main"

RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

volume = 0.5
FPS = 60

PLAYER_RADIUS = 20
ENEMY_RADIUS = 20
ENEMY_COLOR = BLACK
BACKGROUND_IMAGE = os.path.join("Assets","background.png")

TEXT_COLOR = WHITE
PLAYER_COLOR = WHITE

info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Eclipse " + VERSION)
pygame.mouse.set_visible(False)

FONT = pygame.font.Font(None, 40)

BACKGROUND = pygame.transform.scale(pygame.image.load(BACKGROUND_IMAGE), (WIDTH, HEIGHT))

player_image = pygame.Surface((PLAYER_RADIUS * 2, PLAYER_RADIUS * 2), pygame.SRCALPHA)
pygame.draw.circle(player_image, PLAYER_COLOR, (PLAYER_RADIUS, PLAYER_RADIUS), PLAYER_RADIUS)

circle_enemy = pygame.Surface((ENEMY_RADIUS * 2, ENEMY_RADIUS * 2), pygame.SRCALPHA)
pygame.draw.circle(circle_enemy, ENEMY_COLOR, (ENEMY_RADIUS, ENEMY_RADIUS), ENEMY_RADIUS)

square_enemy = pygame.Surface((ENEMY_RADIUS * 2, ENEMY_RADIUS * 2), pygame.SRCALPHA)
pygame.draw.rect(square_enemy, ENEMY_COLOR, (0, 0, ENEMY_RADIUS * 2, ENEMY_RADIUS * 2))

triangle_enemy = pygame.Surface((ENEMY_RADIUS * 2, ENEMY_RADIUS * 2), pygame.SRCALPHA)
pygame.draw.polygon(triangle_enemy, ENEMY_COLOR, [(0, ENEMY_RADIUS * 2), (ENEMY_RADIUS, 0), (ENEMY_RADIUS * 2, ENEMY_RADIUS * 2)])

menu_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
menu_surface.fill((200, 200, 200, 128))

volume_up_rect = pygame.draw.rect(menu_surface, (255, 255, 255), (WIDTH/2 - 50, HEIGHT/ 2 - 120, 120, 40))
volume_label = FONT.render("Volume +", True, (0, 0, 0))
menu_surface.blit(volume_label, (volume_up_rect.x + 10, volume_up_rect.y + 5))

volume_down_rect = pygame.draw.rect(menu_surface, (255, 255, 255), (WIDTH/2 - 50, HEIGHT/ 2 - 60, 120, 40))
volume_label = FONT.render("Volume -", True, (0, 0, 0))
menu_surface.blit(volume_label, (volume_down_rect.x + 10, volume_down_rect.y + 5))

resume_rect = pygame.draw.rect(menu_surface, (255, 255, 255), (WIDTH/2 - 50, HEIGHT/ 2, 120, 40))
resume_label = FONT.render("Resume", True, (0, 0, 0))
menu_surface.blit(resume_label, (resume_rect.x + 10, resume_rect.y + 5))

exit_rect = pygame.draw.rect(menu_surface, (255, 255, 255), (WIDTH/2 - 50, HEIGHT/ 2 + 60, 120, 40))
exit_label = FONT.render("Exit", True, (0, 0, 0))
menu_surface.blit(exit_label, (exit_rect.x + 10, exit_rect.y + 5))


pygame.mixer.music.load(os.path.join("Assets","bg_music.mp3"))


DIE_SOUND = pygame.mixer.Sound(os.path.join("Assets","die.mp3"))
BULLET_FIRE_SOUND = pygame.mixer.Sound(os.path.join("Assets","shoot.mp3"))
HIT_SOUND = pygame.mixer.Sound(os.path.join("Assets","crunch.mp3"))


HIT_SOUND.set_volume(volume)
BULLET_FIRE_SOUND.set_volume(volume)
DIE_SOUND.set_volume(volume)

pygame.mixer.music.set_volume(volume)


class GameObject:
    def __init__(self, x, y, radius, image):
        self.x = x
        self.y = y
        self.radius = radius
        self.image = image
        self.rect = self.image.get_rect(center=(self.x, self.y))


class Player(GameObject):
    def __init__(self, x, y):
        super().__init__(x, y, PLAYER_RADIUS, player_image)
        self.shooting = False
        self.ammo = 0
        self.last_shot_time = pygame.time.get_ticks()
        self.fire_rate = 1500
        self.health = 100
        self.max_health = 99
        self.bullet_size = 30
        self.bullet_penetration = 3
        self.reload_speed = 2
        self.hit = False
        self.last_hit = 0
        self.levels = 0
        self.regen_speed = 1

    def move(self):
        if self.shooting == False:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            self.x = mouse_x
            self.y = mouse_y
            self.rect.center = (self.x, self.y)

    def draw(self, surface):
        if self.hit == True:
            pygame.draw.circle(player_image, RED, (PLAYER_RADIUS, PLAYER_RADIUS), PLAYER_RADIUS)
        else:
            pygame.draw.circle(player_image, PLAYER_COLOR, (PLAYER_RADIUS, PLAYER_RADIUS), PLAYER_RADIUS)
        surface.blit(self.image, self.rect)
        ammo = pygame.font.Font(None, 50).render(str(self.ammo), True, BLACK)
        surface.blit(ammo, (self.x - 10, self.y - 15))

    def check_collision(self, object):
        distance = pygame.math.Vector2(self.x, self.y).distance_to(
            pygame.math.Vector2(object.x, object.y)
        )
        if distance <= (self.radius + object.radius):
            return True
        return False

    def reload(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_shot_time > self.fire_rate:
            self.ammo = 1
            return True
        return False


class Bullet(GameObject):
    def __init__(self, x, y, angle, bullet_size):
        self.bullet_size = bullet_size
        bullet_image = pygame.Surface((bullet_size * 2, bullet_size * 2), pygame.SRCALPHA)
        pygame.draw.circle(bullet_image, WHITE, (bullet_size, bullet_size), bullet_size)
        super().__init__(x, y, bullet_size, bullet_image)
        self.angle = angle
        self.speed = 7
        self.hits = 0

    def move(self):
        self.x += np.cos(self.angle) * self.speed
        self.y += np.sin(self.angle) * self.speed
        self.rect.center = (self.x, self.y)

    def draw(self, surface):
        surface.blit(self.image, self.rect)


class Enemy(GameObject):
    def __init__(self, difficulty):
        self.x = (
            random.randint(WIDTH, WIDTH * 2)
            if random.randint(0, 1) == 0
            else random.randint(-WIDTH, 0)
        )
        self.y = (
            random.randint(HEIGHT, HEIGHT * 2)
            if random.randint(0, 1) == 0
            else random.randint(-HEIGHT, 0)
        )
        self.speed = 1 * difficulty
        self.shape = random.choice(["circle", "square", "triangle"])
        if self.shape == "circle":
            self.image = circle_enemy
        elif self.shape == "square":
            self.image = square_enemy
        else:
            self.image = triangle_enemy
        super().__init__(self.x, self.y, ENEMY_RADIUS, self.image)
        self.time = pygame.time.get_ticks()

    def move(self, circle_x, circle_y):
        angle = np.arctan2(circle_y - self.y, circle_x - self.x)
        self.x += np.cos(angle) * self.speed
        self.y += np.sin(angle) * self.speed
        self.rect.center = (self.x, self.y)

    def draw(self, surface):
        surface.blit(self.image, self.rect)


def main():
    global fps
    global volume
    pygame.mixer.music.play(-1)
    player = Player(WIDTH / 2, HEIGHT / 2)
    bullets = []
    enemies = []
    kills = 0
    alive = True
    running = True
    angle = 0
    shoot = False
    clock = pygame.time.Clock()
    start_time = pygame.time.get_ticks()
    rating = 0
    last_spawn_time = 0
    x = 0
    show_menu = False
    while alive:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    if player.levels > 0:
                        player.max_health = player.max_health + 30
                        player.levels -= 1
                if event.key == pygame.K_2:
                    if player.levels > 0:
                        player.bullet_size = player.bullet_size + 10
                        player.levels -= 1
                if event.key == pygame.K_3:
                    if player.levels > 0:
                        player.bullet_penetration = player.bullet_penetration + 1
                        player.levels -= 1
                if event.key == pygame.K_4:
                    if player.levels > 0:
                        if player.fire_rate > 0:
                            player.fire_rate = player.fire_rate - 200
                            player.levels -= 1
                if event.key == pygame.K_5:
                    if player.levels > 0:
                        player.regen_speed += 1
                        player.levels -= 1
                if event.key == pygame.K_ESCAPE:
                    show_menu = True
            if event.type == pygame.MOUSEBUTTONDOWN:
                player.shooting = True
                pygame.mouse.set_visible(True)
                location = pygame.mouse.get_pos()
            if event.type == pygame.MOUSEBUTTONUP:
                if player.reload():
                    player.last_shot_time = pygame.time.get_ticks()
                    player.ammo = 0
                    shoot = True
                    BULLET_FIRE_SOUND.play()
                player.shooting = False
                pygame.mouse.set_visible(False)
                pygame.mouse.set_pos(location)

        pygame.mouse.set_visible(False)

        elapsed_ticks = pygame.time.get_ticks() - start_time
        elapsed_time = elapsed_ticks / 1000

        base = 2
        rating = base ** (np.log10(elapsed_time + 1)) + base ** (np.log10(kills + 1))

        if int(rating) > x:
            x += 1
            player.levels += 1

        player.reload()

        player.level = rating // 2

        if player.shooting:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            angle = np.arctan2(mouse_y - player.y, mouse_x - player.x)

            arrow_x = player.x + (70 * np.cos(angle))
            arrow_y = player.y + (70 * np.sin(angle))

        if shoot:
            bullet = Bullet(player.x, player.y, angle, player.bullet_size)
            bullets.append(bullet)
            shoot = False

        current_time = pygame.time.get_ticks()
        if current_time - last_spawn_time > 1000 - rating * 50:
            if player.health < player.max_health:
                if not player.hit:
                    player.health = player.health + 1 * player.regen_speed
            last_spawn_time = current_time
            enemies.append(Enemy(rating))

        player.move()

        for bullet in bullets:
            bullet.move()

        for e in enemies:
            if pygame.time.get_ticks() > e.time + 25000:
                enemies.remove(e)
            e.move(player.x, player.y)

        for enemy in enemies:
            if player.check_collision(enemy):
                if not player.hit:
                    player.hit = True
                    player.last_hit = pygame.time.get_ticks()
                    player.health = player.health - int(50 + rating)
                    DIE_SOUND.play()
                if player.health <= 0:
                    alive = False

        if current_time - player.last_hit > 2000:
            player.hit = False


        for bullet in bullets:
            for enemy in enemies:
                if bullet.rect.colliderect(enemy.rect):
                    if bullet.hits < player.bullet_penetration:
                        enemies.remove(enemy)
                        bullet.hits += 1
                        kills += 1
                        HIT_SOUND.play()

        clock.tick(FPS)

        screen.blit(BACKGROUND, (0, 0))

        if player.shooting:
            pygame.draw.line(screen, PLAYER_COLOR, (player.x, player.y), (arrow_x, arrow_y), 10)

        for b in bullets:
            b.draw(screen)
        for e in enemies:
            e.draw(screen)

        player.draw(screen)

        bar_width = 300
        bar_height = 20
        bar_x = WIDTH - 320
        bar_y = HEIGHT - 30
        pygame.draw.rect(screen, (255, 0, 0), (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(screen, (0, 255, 0), (bar_x, bar_y, bar_width * (player.health / player.max_health), bar_height))

        health_text = FONT.render(str(player.health), True, TEXT_COLOR)
        screen.blit(health_text, (bar_x - 65, bar_y - 5))

        max_health_text = FONT.render("[1] Max Health: " + str(player.max_health + 1), True, TEXT_COLOR)
        screen.blit(max_health_text, (10, HEIGHT - 160))

        bullet_speed_text = FONT.render("[2] Bullet Size: " + str(player.bullet_size), True, TEXT_COLOR)
        screen.blit(bullet_speed_text, (10, HEIGHT - 130))

        bullet_penetration_text = FONT.render("[3] Bullet Penetration: " + str(player.bullet_penetration), True, TEXT_COLOR)
        screen.blit(bullet_penetration_text, (10, HEIGHT - 100))

        reload_speed_text = FONT.render("[4] Reload Speed: " + str(player.fire_rate / 1000) + "s", True, TEXT_COLOR)
        screen.blit(reload_speed_text, (10, HEIGHT - 70))

        regen_speed_text = FONT.render("[5] Regen Speed: " + str(player.regen_speed), True, TEXT_COLOR)
        screen.blit(regen_speed_text, (10, HEIGHT - 40))

        time_text = FONT.render("Time: " + str(elapsed_time), True, TEXT_COLOR)
        screen.blit(time_text, (10, 40))

        kills_text = FONT.render("Kills: " + str(kills), True, TEXT_COLOR)
        screen.blit(kills_text, (10, 10))

        level_text = FONT.render("Levels: " + str(player.levels), True, TEXT_COLOR)
        screen.blit(level_text, (10, 70))

        frame_rate = clock.get_fps()
        fps_text = FONT.render("FPS: " + str(int(frame_rate)), True, TEXT_COLOR)
        screen.blit(fps_text, (WIDTH - 120, 10))

        font = pygame.font.Font(None, 80)

        text = font.render("Eclipse " + VERSION, True, TEXT_COLOR)
        text_rect = text.get_rect()
        text_rect.centerx = screen.get_rect().centerx
        text_rect.top = 10
        screen.blit(text, text_rect)

        while show_menu:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        show_menu = False
                        pygame.mouse.set_pos((player.x, player.y))
                if event.type == pygame.MOUSEBUTTONUP:
                    if volume_up_rect.collidepoint(event.pos):
                        volume += 0.05
                        HIT_SOUND.set_volume(volume)
                        BULLET_FIRE_SOUND.set_volume(volume)
                        DIE_SOUND.set_volume(volume)
                        pygame.mixer.music.set_volume(volume)
                    if volume_down_rect.collidepoint(event.pos):
                        volume -= 0.05
                        HIT_SOUND.set_volume(volume)
                        BULLET_FIRE_SOUND.set_volume(volume)
                        DIE_SOUND.set_volume(volume)
                        pygame.mixer.music.set_volume(volume)
                    elif resume_rect.collidepoint(event.pos):
                        show_menu = False
                        pygame.mouse.set_pos((player.x, player.y))
                    elif exit_rect.collidepoint(event.pos):
                        running = False
                        alive = False
                        sys.exit()

            pygame.mouse.set_visible(True)
            screen.blit(menu_surface, (0, 0))
            pygame.display.flip()

        pygame.display.flip()

    while not alive and running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    alive = True
                if event.key == pygame.K_ESCAPE:
                    running = False
                    alive = False
                    break

        text_strings = ["Game Over", "Press Enter to Restart", "Press Escape to Exit"]
        font_size = 100
        text_color = RED

        font = pygame.font.Font(None, font_size)

        for i, text_string in enumerate(text_strings):
            text = font.render(text_string, 1, text_color)
            text_rect = text.get_rect(center=(WIDTH // 2, (HEIGHT // 2) + (i * 100)))
            screen.blit(text, text_rect)

        pygame.display.flip()

    while running:
        main()


if __name__ == "__main__":
    main()
