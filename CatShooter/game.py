import pygame
from pygame.locals import *
from os.path import join, dirname, abspath
from random import randint, uniform

BASE_DIR = dirname(abspath(__file__))

class Cat(pygame.sprite.Sprite):
    def __init__(self, groups):
        super().__init__(groups)
        self.image = pygame.image.load(join(BASE_DIR, 'images/pink_cat.png')).convert_alpha()
        self.rect = self.image.get_rect(bottomright = (WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2))
        self.direction = pygame.Vector2()
        self.speed = 500  # pixels per second
        
        # Cool down
        self.can_shoot = True
        self.meow_shoot_time = 0
        self.cooldown_duration = 400
        
        # Mask
        self.mask = pygame.mask.from_surface(self.image)
        
    def meow_timer(self):
        if not self.can_shoot:
            current_time = pygame.time.get_ticks()
            if current_time - self.meow_shoot_time >= self.cooldown_duration:
                self.can_shoot = True
        
    def update(self, dt):
        keys = pygame.key.get_pressed()
        self.direction.x = int(keys[pygame.K_RIGHT]) - int(keys[pygame.K_LEFT])
        self.direction.y = int(keys[pygame.K_DOWN]) - int(keys[pygame.K_UP])
        self.direction = self.direction.normalize() if self.direction else self.direction
        self.rect.center += self.direction * self.speed * dt
        self.rect.clamp_ip(pygame.Rect(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT))

        if keys[pygame.K_SPACE] and self.can_shoot:
            Meow(meow_surf, self.rect.midtop, (all_sprites, meow_sprites))
            self.can_shoot = False
            self.meow_shoot_time = pygame.time.get_ticks()
            meow_sound.play()
            
        self.meow_timer()  # Call the meow timer function
        
class Yarn(pygame.sprite.Sprite):
    def __init__(self, groups, surf):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(center = (randint(0, WINDOW_WIDTH), randint(0, WINDOW_HEIGHT)))

class Meow(pygame.sprite.Sprite):
    def __init__(self, surf, pos, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(midbottom = pos)
        self.speed = 400

    def update(self, dt):
        self.rect.centery -= self.speed * dt
        if self.rect.bottom < 0:
            self.kill()
    
class Monster(pygame.sprite.Sprite):
    def __init__(self, surf, pos, groups):
        super().__init__(groups)
        self.original_surf = surf
        self.image = surf
        self.rect = self.image.get_rect(center = pos)
        self.start_time = pygame.time.get_ticks()
        self.lifetime = 3000
        self.direction = pygame.Vector2(uniform(-0.5, 0.5), 1)
        self.speed = randint(400, 500)
        self.rotation_speed = randint(40, 80)
        self.rotation = 0
        
    def update(self, dt):
        self.rect.center += self.direction * self.speed * dt
        if pygame.time.get_ticks() - self.start_time >= self.lifetime:
            self.kill()
        self.rotation += self.rotation_speed * dt
        self.image = pygame.transform.rotozoom(self.original_surf, self.rotation, 1)
        self.rect = self.image.get_rect(center = self.rect.center)
    
class AnimatedPaw(pygame.sprite.Sprite):
    def __init__(self, frames, pos, groups):
        super().__init__(groups)
        self.frames = frames
        self.frame_index = 0
        self.image = self.frames[self.frame_index]
        self.rect = self.image.get_rect(center = pos)
        
    def update(self, dt):
        self.frame_index += 20 * dt
        if self.frame_index < len(self.frames):
            self.image = self.frames[int(self.frame_index)]
        else:
            self.kill()  # Remove the paw animation once it's done

score = 0
high_score = 0
lives = 3
game_over = False
game_start_time = pygame.time.get_ticks()

def get_spawn_interval():
    elapsed = (pygame.time.get_ticks() - game_start_time) / 1000
    return max(150, int(500 - elapsed * 5))

def update_score():
    global score
    score += 1

def display_score():
    text_surf = font.render(f'Score: {score}', True, (240, 240, 240))
    text_rect = text_surf.get_rect(midbottom = (WINDOW_WIDTH / 2, WINDOW_HEIGHT - 50))
    display_surface.blit(text_surf, text_rect)
    pygame.draw.rect(display_surface, (240, 240, 240), text_rect.inflate(20, 16).move(0, -8), 5, 10)

def display_lives():
    lives_surf = font.render(f'Lives: {lives}', True, (255, 160, 160))
    lives_rect = lives_surf.get_rect(topleft=(20, 20))
    display_surface.blit(lives_surf, lives_rect)

def draw_game_over():
    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    display_surface.blit(overlay, (0, 0))

    title_surf = font.render('GAME OVER', True, (255, 80, 80))
    title_rect = title_surf.get_rect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 - 60))
    display_surface.blit(title_surf, title_rect)

    score_surf = font.render(f'Score: {score}', True, (240, 240, 240))
    score_rect = score_surf.get_rect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2))
    display_surface.blit(score_surf, score_rect)

    hs_surf = font.render(f'Best: {high_score}', True, (255, 215, 0))
    hs_rect = hs_surf.get_rect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 + 50))
    display_surface.blit(hs_surf, hs_rect)

    hint_surf = font.render('Press R to Restart or Q to Quit', True, (180, 180, 180))
    hint_rect = hint_surf.get_rect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 + 110))
    display_surface.blit(hint_surf, hint_rect)

def reset_game():
    global score, lives, game_over, game_start_time
    score = 0
    lives = 3
    game_over = False
    game_start_time = pygame.time.get_ticks()
    all_sprites.empty()
    meow_sprites.empty()
    monster_sprites.empty()
    yarn_sprites.empty()
    for _ in range(20):
        Yarn((all_sprites, yarn_sprites), yarn_surf)
    return Cat(all_sprites)

def collisions():
    global game_over, lives, high_score
    collision_sprites = pygame.sprite.spritecollide(cat, monster_sprites, True, pygame.sprite.collide_mask)
    if collision_sprites:
        lives -= 1
        if lives <= 0:
            game_over = True
            if score > high_score:
                high_score = score

    for meow in meow_sprites:
        collided_sprites = pygame.sprite.spritecollide(meow, monster_sprites, True)
        if collided_sprites:
            meow.kill()
            update_score()
            AnimatedPaw(paw_frames, meow.rect.midtop, all_sprites)
            paw_sound.play()
            
# General setup
pygame.init()
WINDOW_WIDTH, WINDOW_HEIGHT = 1280, 720
display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Meow-nster Shooter")
pygame.display.set_icon(pygame.image.load(join(BASE_DIR, 'images/cat_icon.png')))
running = True
clock = pygame.time.Clock()

# Import
yarn_surf = pygame.image.load(join(BASE_DIR, 'images/star.png')).convert_alpha()
monster_surf = pygame.image.load(join(BASE_DIR, 'images/enemy.png')).convert_alpha()
meow_surf = pygame.image.load(join(BASE_DIR, 'images/laser.png')).convert_alpha()
font = pygame.font.Font(join(BASE_DIR, 'images/CatFont-Bold.ttf'), 40)
paw_frames = [pygame.image.load(join(BASE_DIR, 'images/explosion', f'{i}.png')).convert_alpha() for i in range(21)]

meow_sound = pygame.mixer.Sound(join(BASE_DIR, 'audio/sword.mp3'))
meow_sound.set_volume(0.5)
paw_sound = pygame.mixer.Sound(join(BASE_DIR, 'audio/kill.mp3'))
game_music = pygame.mixer.Sound(join(BASE_DIR, 'audio/music.mp3'))
game_music.set_volume(0.4)
game_music.play(-1)  # Play the game music indefinitely

# Sprite Groups
all_sprites = pygame.sprite.Group()
yarn_sprites = pygame.sprite.Group()
meow_sprites = pygame.sprite.Group()
monster_sprites = pygame.sprite.Group()

# Player
cat = Cat(all_sprites)

# Yarn setup
for _ in range(20):
    Yarn((all_sprites, yarn_sprites), yarn_surf)

# Monster spawn event
MONSTER_SPAWN_EVENT = pygame.USEREVENT + 1
pygame.time.set_timer(MONSTER_SPAWN_EVENT, 500)

# Game loop
while running:
    dt = clock.tick(60) / 1000

    for event in pygame.event.get():
        if event.type == QUIT:
            running = False
        if not game_over:
            if event.type == MONSTER_SPAWN_EVENT:
                Monster(monster_surf, (randint(50, WINDOW_WIDTH - 50), -50), (all_sprites, monster_sprites))
                pygame.time.set_timer(MONSTER_SPAWN_EVENT, get_spawn_interval())
        else:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_r]:
                cat = reset_game()
            if keys[pygame.K_q]:
                running = False

    if not game_over:
        all_sprites.update(dt)
        collisions()

    display_surface.fill((30, 30, 30))
    all_sprites.draw(display_surface)
    display_score()
    display_lives()

    if game_over:
        draw_game_over()

    pygame.display.update()

pygame.quit()
