import pygame
from pygame.locals import *
from os.path import join
from random import randint, uniform

class Cat(pygame.sprite.Sprite):
    def __init__(self, groups):
        super().__init__(groups)
        self.image = pygame.image.load(join('CatShooter', 'images', 'pink_cat.png')).convert_alpha()
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
        
        recent_keys = pygame.key.get_pressed()
        if recent_keys[pygame.K_SPACE] and self.can_shoot:
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
        self.speed = 100
        
    def update(self, dt):
        self.rect.centery -= 400 * dt
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

# Add score variable
score = 0  # Initialize the score to zero

def update_score():
    global score
    score += 1  # Increment the score by 1
    
def display_score():
    text_surf = font.render(f'Score: {score}', True, (240, 240, 240))  # Display the score
    text_rect = text_surf.get_rect(midbottom = (WINDOW_WIDTH / 2, WINDOW_HEIGHT - 50))
    display_surface.blit(text_surf, text_rect)
    pygame.draw.rect(display_surface, (240, 240, 240), text_rect.inflate(20, 16).move(0, -8), 5, 10 )

def collisions():
    global running 
    collision_sprites = pygame.sprite.spritecollide(cat, monster_sprites, True, pygame.sprite.collide_mask)
    if collision_sprites:  # If a collision occurs with a monster
        running = False
        
    for meow in meow_sprites:
        collided_sprites = pygame.sprite.spritecollide(meow, monster_sprites, True)
        if collided_sprites:  # If a collision occurs with a monster
            meow.kill()
            update_score()  # Increase the score when a monster is hit
            AnimatedPaw(paw_frames, meow.rect.midtop, all_sprites)
            paw_sound.play()
            
# General setup
pygame.init()
WINDOW_WIDTH, WINDOW_HEIGHT = 1280, 720
display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Cat Shooter")
pygame.display.set_icon(pygame.image.load('CatShooter/images/cat_icon.png'))  # To change the window icon
running = True
clock = pygame.time.Clock()

# Import
yarn_surf = pygame.image.load(join('CatShooter', 'images', 'star.png')).convert_alpha()
monster_surf = pygame.image.load(join('CatShooter', 'images', 'enemy.png')).convert_alpha()
meow_surf = pygame.image.load(join('CatShooter', 'images', 'laser.png')).convert_alpha()
font = pygame.font.Font(join('CatShooter', 'images', 'CatFont-Bold.ttf'), 40)
paw_frames = [pygame.image.load(join('CatShooter', 'images', 'explosion', f'{i}.png')).convert_alpha() for i in range(21)]

meow_sound = pygame.mixer.Sound(join('CatShooter', 'audio', 'sword.mp3'))
meow_sound.set_volume(0.5) # volume
paw_sound = pygame.mixer.Sound(join('CatShooter', 'audio', 'kill.mp3'))
game_music = pygame.mixer.Sound(join('CatShooter', 'audio', 'music.mp3'))
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
pygame.time.set_timer(MONSTER_SPAWN_EVENT, 500)  # Every half second

# Game loop
while running:
    dt = clock.tick(60) / 1000  # Delta time in seconds
    
    # Event handling
    for event in pygame.event.get():
        if event.type == QUIT:
            running = False
        if event.type == MONSTER_SPAWN_EVENT:
            Monster(monster_surf, (randint(50, WINDOW_WIDTH - 50), -50), (all_sprites, monster_sprites))
    
    # Update
    all_sprites.update(dt)
    
    # Check collisions
    collisions()
    
    # Drawing
    display_surface.fill((30, 30, 30))  # Background color
    all_sprites.draw(display_surface)
    display_score()  # Draw the score on the screen
    pygame.display.update()

# Quit the game
pygame.quit()
