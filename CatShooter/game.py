"""
Meow-nster Shooter
==================
A 2D arcade-style top-down shooter built with Pygame.

The player controls a cat that fires projectiles ("meows") upward to destroy
falling monsters. The game features three difficulty levels, a combo multiplier
scoring system, random power-ups, screen-shake on damage, and persistent
high-score saving between sessions.

How to run:
    python game.py

Required dependencies (see requirements.txt):
    - pygame  : game framework for rendering, input, audio, and sprite management
    - numpy   : used to procedurally generate the hit-damage sound effect

Architecture overview:
    - All interactive objects (cat, enemies, bullets, etc.) are Pygame Sprites
      collected into named Sprite Groups for efficient batch updates and collision
      detection.
    - Game state (score, lives, difficulty, combo) is stored as module-level
      globals, kept simple for a single-file project of this scope.
    - The main game loop runs at a capped 60 FPS and is responsible for event
      handling, state updates, collision resolution, and rendering each frame.
    - Persistent data (high score only) is saved to save_data.json next to this
      file using Python's built-in json module.
"""

# ---------------------------------------------------------------------------
# Standard library & third-party imports
# ---------------------------------------------------------------------------
import pygame
from pygame.locals import *                      # Exposes QUIT, KEYDOWN, etc. as bare names
from os.path import join, dirname, abspath       # Cross-platform path helpers
from random import randint, uniform              # Used for enemy spawn positions and speeds
import json                                      # Serialize / deserialize save data
import os                                        # File existence checks
import numpy as np                               # Procedural audio generation for the hit sound

# Absolute path to the directory containing this file.  All asset paths are
# constructed relative to this so the game works regardless of where the user
# launches Python from.
BASE_DIR = dirname(abspath(__file__))


# ---------------------------------------------------------------------------
# Player sprite — the pink cat the user controls
# ---------------------------------------------------------------------------

class Cat(pygame.sprite.Sprite):
    """
    The player-controlled character.

    Responsibilities:
        - Read keyboard input each frame and move accordingly (arrow keys).
        - Fire a Meow projectile when SPACE is pressed, subject to a cooldown.
        - Flash / become temporarily invincible for 1.5 s after taking a hit,
          preventing multiple rapid hits from a single enemy pass.
    """

    def __init__(self, groups):
        super().__init__(groups)

        # Load the cat sprite image with transparency support (convert_alpha
        # preserves the PNG alpha channel so the background is see-through).
        self.image = pygame.image.load(join(BASE_DIR, 'images/pink_cat.png')).convert_alpha()
        self.rect = self.image.get_rect(bottomright = (WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2))

        # Movement — direction is a normalised 2D vector set each frame from
        # key state; multiplied by speed * dt to get frame-rate-independent movement.
        self.direction = pygame.Vector2()
        self.speed = 500  # pixels per second

        # Shooting cooldown — prevents holding SPACE from firing every single frame.
        self.can_shoot = True
        self.meow_shoot_time = 0
        self.cooldown_duration = 400      # milliseconds between shots (default)

        # Invincibility frames — after a hit the cat blinks and cannot be hurt again
        # for invincible_duration milliseconds, giving the player time to move away.
        self.invincible = False
        self.invincible_start = 0
        self.invincible_duration = 1500   # 1.5 seconds of post-hit protection
        self.original_image = self.image.copy()   # saved so we can restore after blink

        # Pixel-perfect collision mask built from the sprite's alpha channel.
        # Using a mask instead of rectangle overlap prevents "near misses" from
        # being counted as hits.
        self.mask = pygame.mask.from_surface(self.image)

    def meow_timer(self):
        """Re-enable shooting once the cooldown period has elapsed."""
        if not self.can_shoot:
            current_time = pygame.time.get_ticks()
            if current_time - self.meow_shoot_time >= self.cooldown_duration:
                self.can_shoot = True

    def hit(self):
        """Called by the collision system when the cat is struck by an enemy."""
        self.invincible = True
        self.invincible_start = pygame.time.get_ticks()

    def invincibility_timer(self):
        """
        Handle the post-hit invincibility blink effect.

        The cat's sprite alternates between visible and invisible every 100 ms
        to give a classic arcade 'flashing' visual cue.  After invincible_duration
        the cat returns to full visibility and can be hurt again.
        """
        if self.invincible:
            now = pygame.time.get_ticks()
            if now - self.invincible_start >= self.invincible_duration:
                # Invincibility window over — restore the sprite and re-enable damage.
                self.invincible = False
                self.image = self.original_image
            else:
                # Toggle visibility based on whether the current 100 ms slot is even/odd.
                visible = (now // 100) % 2 == 0
                self.image = self.original_image if visible else pygame.Surface(self.original_image.get_size(), pygame.SRCALPHA)

    def update(self, dt):
        """
        Called once per frame by the sprite group.

        dt (float): seconds elapsed since the last frame.  Multiplying velocity
        by dt makes movement speed independent of frame rate.
        """
        keys = pygame.key.get_pressed()

        # Build a direction vector from held arrow keys.
        # Subtracting LEFT from RIGHT gives -1, 0, or +1 for the X axis, same for Y.
        self.direction.x = int(keys[pygame.K_RIGHT]) - int(keys[pygame.K_LEFT])
        self.direction.y = int(keys[pygame.K_DOWN]) - int(keys[pygame.K_UP])

        # Normalise diagonal movement so holding two keys doesn't move faster than one.
        self.direction = self.direction.normalize() if self.direction else self.direction
        self.rect.center += self.direction * self.speed * dt

        # Keep the cat inside the window boundaries.
        self.rect.clamp_ip(pygame.Rect(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT))

        if keys[pygame.K_SPACE] and self.can_shoot:
            # Spawn a projectile at the cat's nose (midtop of the sprite rect).
            Meow(meow_surf, self.rect.midtop, (all_sprites, meow_sprites))
            self.can_shoot = False
            self.meow_shoot_time = pygame.time.get_ticks()
            meow_sound.play()

        self.meow_timer()
        self.invincibility_timer()
        
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
        lo, hi = DIFFICULTY_SETTINGS[difficulty]['speed_range']
        self.speed = randint(lo, hi)
        self.rotation_speed = randint(40, 80)
        self.rotation = 0

    def update(self, dt):
        self.rect.center += self.direction * self.speed * dt
        if pygame.time.get_ticks() - self.start_time >= self.lifetime:
            self.kill()
        self.rotation += self.rotation_speed * dt
        self.image = pygame.transform.rotozoom(self.original_surf, self.rotation, 1)
        self.rect = self.image.get_rect(center = self.rect.center)
    
class FastMonster(pygame.sprite.Sprite):
    def __init__(self, surf, pos, groups):
        super().__init__(groups)
        tinted = surf.copy()
        tinted.fill((255, 60, 60, 180), special_flags=pygame.BLEND_RGBA_MULT)
        self.original_surf = tinted
        self.image = tinted
        self.rect = self.image.get_rect(center=pos)
        self.start_time = pygame.time.get_ticks()
        self.lifetime = 4000
        self.direction = pygame.Vector2(uniform(-0.5, 0.5), 1)
        self.speed = randint(700, 900)
        self.rotation_speed = randint(100, 150)
        self.rotation = 0
        self.score_value = 3
        self.mask = pygame.mask.from_surface(self.image)

    def update(self, dt):
        self.rect.center += self.direction * self.speed * dt
        if pygame.time.get_ticks() - self.start_time >= self.lifetime:
            self.kill()
        self.rotation += self.rotation_speed * dt
        self.image = pygame.transform.rotozoom(self.original_surf, self.rotation, 1)
        self.rect = self.image.get_rect(center=self.rect.center)

class PowerUp(pygame.sprite.Sprite):
    def __init__(self, pos, groups):
        super().__init__(groups)
        self.image = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (80, 220, 255), (10, 10), 10)
        self.rect = self.image.get_rect(center=pos)
        self.speed = 150

    def update(self, dt):
        self.rect.y += int(self.speed * dt)
        if self.rect.top > WINDOW_HEIGHT:
            self.kill()

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

SAVE_FILE = join(BASE_DIR, 'save_data.json')

def load_high_score():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, 'r') as f:
            return json.load(f).get('high_score', 0)
    return 0

def save_high_score(value):
    with open(SAVE_FILE, 'w') as f:
        json.dump({'high_score': value}, f)

score = 0
high_score = load_high_score()
lives = 3
kills = 0
game_over = False
paused = False
on_start_screen = True
difficulty = 'Normal'
DIFFICULTY_SETTINGS = {
    'Easy':   {'spawn_base': 700, 'spawn_min': 300, 'speed_range': (250, 350)},
    'Normal': {'spawn_base': 500, 'spawn_min': 150, 'speed_range': (400, 500)},
    'Hard':   {'spawn_base': 300, 'spawn_min': 80,  'speed_range': (500, 700)},
}
muted = False
shake_timer = 0
combo = 0
combo_timer = 0
COMBO_WINDOW = 2000
rapid_fire_timer = 0
game_start_time = pygame.time.get_ticks()

def get_spawn_interval():
    s = DIFFICULTY_SETTINGS[difficulty]
    elapsed = (pygame.time.get_ticks() - game_start_time) / 1000
    return max(s['spawn_min'], int(s['spawn_base'] - elapsed * 5))

def update_score(base=1):
    global score, combo, combo_timer, kills
    kills += 1
    combo += 1
    combo_timer = pygame.time.get_ticks()
    multiplier = min(combo, 5)
    score += base * multiplier

def display_score():
    text_surf = font.render(f'Score: {score}', True, (240, 240, 240))
    text_rect = text_surf.get_rect(midbottom = (WINDOW_WIDTH / 2, WINDOW_HEIGHT - 50))
    display_surface.blit(text_surf, text_rect)
    pygame.draw.rect(display_surface, (240, 240, 240), text_rect.inflate(20, 16).move(0, -8), 5, 10)

def draw_heart(surface, x, y, size, filled):
    color = (220, 60, 80) if filled else (80, 40, 50)
    r = size // 4
    pygame.draw.circle(surface, color, (x + r, y + r), r)
    pygame.draw.circle(surface, color, (x + size - r, y + r), r)
    points = [(x, y + r), (x + size // 2, y + size), (x + size, y + r)]
    pygame.draw.polygon(surface, color, points)

def display_lives():
    size = 36
    gap = 10
    for i in range(3):
        draw_heart(display_surface, 20 + i * (size + gap), 20, size, i < lives)

def display_kills():
    kills_surf = font.render(f'Kills: {kills}', True, (160, 220, 160))
    display_surface.blit(kills_surf, kills_surf.get_rect(topright=(WINDOW_WIDTH - 20, 60)))

def display_combo():
    if combo >= 2:
        color = (255, 215, 0) if combo < 5 else (255, 80, 80)
        combo_surf = font.render(f'x{min(combo, 5)} COMBO!', True, color)
        display_surface.blit(combo_surf, combo_surf.get_rect(midtop=(WINDOW_WIDTH / 2, 20)))

def display_mute():
    if muted:
        mute_surf = font.render('MUTED', True, (180, 180, 180))
        display_surface.blit(mute_surf, mute_surf.get_rect(topright=(WINDOW_WIDTH - 20, 20)))

def draw_start_screen():
    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    display_surface.blit(overlay, (0, 0))
    title_surf = font.render('MEOW-NSTER SHOOTER', True, (255, 160, 80))
    display_surface.blit(title_surf, title_surf.get_rect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 - 100)))
    hs_surf = font.render(f'Best Score: {high_score}', True, (255, 215, 0))
    display_surface.blit(hs_surf, hs_surf.get_rect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 - 30)))
    diff_color = {'Easy': (80, 220, 80), 'Normal': (240, 240, 80), 'Hard': (255, 80, 80)}[difficulty]
    diff_surf = font.render(f'Difficulty: {difficulty}  (D to change)', True, diff_color)
    display_surface.blit(diff_surf, diff_surf.get_rect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 + 40)))
    hint_surf = font.render('Press SPACE to Play', True, (200, 200, 200))
    display_surface.blit(hint_surf, hint_surf.get_rect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 + 110)))
    mute_hint = font.render('M = Mute   P = Pause', True, (140, 140, 140))
    display_surface.blit(mute_hint, mute_hint.get_rect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 + 160)))

def draw_paused():
    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 120))
    display_surface.blit(overlay, (0, 0))
    pause_surf = font.render('PAUSED', True, (240, 240, 240))
    display_surface.blit(pause_surf, pause_surf.get_rect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2)))
    hint_surf = font.render('Press P to Resume', True, (180, 180, 180))
    display_surface.blit(hint_surf, hint_surf.get_rect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 + 60)))

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
    global score, lives, kills, game_over, game_start_time, combo, combo_timer, rapid_fire_timer
    score = 0
    lives = 3
    kills = 0
    game_over = False
    combo = 0
    combo_timer = 0
    rapid_fire_timer = 0
    game_start_time = pygame.time.get_ticks()
    all_sprites.empty()
    meow_sprites.empty()
    monster_sprites.empty()
    yarn_sprites.empty()
    powerup_sprites.empty()
    for _ in range(20):
        Yarn((all_sprites, yarn_sprites), yarn_surf)
    return Cat(all_sprites)

def collisions():
    global game_over, lives, high_score, shake_timer, rapid_fire_timer
    if not cat.invincible:
        collision_sprites = pygame.sprite.spritecollide(cat, monster_sprites, True, pygame.sprite.collide_mask)
        if collision_sprites:
            cat.hit()
            shake_timer = 300
            hit_sound.play()
            lives -= 1
            if lives <= 0:
                game_over = True
                if score > high_score:
                    high_score = score
                    save_high_score(high_score)

    for meow in meow_sprites:
        collided_sprites = pygame.sprite.spritecollide(meow, monster_sprites, True)
        if collided_sprites:
            meow.kill()
            base = sum(getattr(m, 'score_value', 1) for m in collided_sprites)
            update_score(base)
            AnimatedPaw(paw_frames, meow.rect.midtop, all_sprites)
            paw_sound.play()
            if randint(1, 5) == 1:
                PowerUp(meow.rect.midtop, (all_sprites, powerup_sprites))

    picked = pygame.sprite.spritecollide(cat, powerup_sprites, True)
    if picked:
        cat.cooldown_duration = 100
        rapid_fire_timer = pygame.time.get_ticks()
            
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

def make_hit_sound():
    sample_rate = 44100
    duration = 0.15
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    wave = (np.sin(2 * np.pi * 180 * t) * 0.4 * np.exp(-t * 20)).astype(np.float32)
    stereo = np.column_stack([wave, wave])
    sound = pygame.sndarray.make_sound((stereo * 32767).astype(np.int16))
    return sound

hit_sound = make_hit_sound()
game_music.set_volume(0.4)
game_music.play(-1)  # Play the game music indefinitely

# Sprite Groups
all_sprites = pygame.sprite.Group()
yarn_sprites = pygame.sprite.Group()
meow_sprites = pygame.sprite.Group()
monster_sprites = pygame.sprite.Group()
powerup_sprites = pygame.sprite.Group()

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
        if event.type == KEYDOWN and event.key == pygame.K_m:
            muted = not muted
            pygame.mixer.pause() if muted else pygame.mixer.unpause()
        if on_start_screen:
            if event.type == KEYDOWN and event.key == pygame.K_SPACE:
                on_start_screen = False
                game_start_time = pygame.time.get_ticks()
            if event.type == KEYDOWN and event.key == pygame.K_d:
                diff_list = list(DIFFICULTY_SETTINGS.keys())
                difficulty = diff_list[(diff_list.index(difficulty) + 1) % len(diff_list)]
        if event.type == KEYDOWN and event.key == pygame.K_p and not game_over and not on_start_screen:
            paused = not paused
        if not game_over and not paused and not on_start_screen:
            if event.type == MONSTER_SPAWN_EVENT:
                elapsed = (pygame.time.get_ticks() - game_start_time) / 1000
                pos = (randint(50, WINDOW_WIDTH - 50), -50)
                if elapsed > 30 and randint(1, 4) == 1:
                    FastMonster(monster_surf, pos, (all_sprites, monster_sprites))
                else:
                    Monster(monster_surf, pos, (all_sprites, monster_sprites))
                pygame.time.set_timer(MONSTER_SPAWN_EVENT, get_spawn_interval())
        else:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_r]:
                cat = reset_game()
            if keys[pygame.K_q]:
                running = False

    if combo > 0 and pygame.time.get_ticks() - combo_timer > COMBO_WINDOW:
        combo = 0

    if rapid_fire_timer > 0 and pygame.time.get_ticks() - rapid_fire_timer > 5000:
        cat.cooldown_duration = 400
        rapid_fire_timer = 0

    if not game_over and not paused and not on_start_screen:
        all_sprites.update(dt)
        collisions()

    if shake_timer > 0:
        shake_timer = max(0, shake_timer - dt * 1000)
        shake_x = randint(-8, 8)
        shake_y = randint(-8, 8)
    else:
        shake_x = shake_y = 0

    display_surface.fill((30, 30, 30))
    game_surf = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
    game_surf.fill((30, 30, 30))
    for sprite in all_sprites:
        game_surf.blit(sprite.image, sprite.rect)
    display_surface.blit(game_surf, (shake_x, shake_y))
    display_score()
    display_lives()
    display_kills()
    display_combo()
    display_mute()

    if on_start_screen:
        draw_start_screen()
    elif paused:
        draw_paused()
    elif game_over:
        draw_game_over()

    pygame.display.update()

pygame.quit()
