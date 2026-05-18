# Meow-nster Shooter — Changes & Technical Breakdown

A full explanation of every change made, why it was made, and how the code works.

---

## 1. Fixed Asset Paths

**Before:**
```python
pygame.image.load(join('img/pink_cat.png'))
```
**After:**
```python
BASE_DIR = dirname(abspath(__file__))
pygame.image.load(join(BASE_DIR, 'images/pink_cat.png'))
```

**Why:** The original code used relative paths like `img/`. That means "look for the `img` folder wherever the terminal is currently pointing." If you ran the game from your Desktop instead of the CatShooter folder, it would crash immediately because it couldn't find the images.

`__file__` is a Python built-in that always knows the exact location of the script itself. `abspath` converts it to a full path, and `dirname` strips the filename to get just the folder. So `BASE_DIR` always equals "the folder this script lives in" — no matter where you launch it from.

**Algorithm:** Build an absolute path anchor once at startup, then prefix every asset load with it.

---

## 2. Fixed the Dead `speed` Attribute on `Meow`

**Before:**
```python
self.speed = 100  # set here
...
self.rect.centery -= 400 * dt  # hardcoded 400, ignoring speed
```
**After:**
```python
self.speed = 400
self.rect.centery -= self.speed * dt
```

**Why:** The original code set `self.speed = 100` but never used it. Movement was controlled by a magic number `400` buried in the update method. This is a bug — if you ever wanted to change bullet speed, you'd change `self.speed` and nothing would happen. We made `speed` actually drive the movement so the code does what it looks like it does.

---

## 3. Removed Duplicate Key Poll

**Before:**
```python
keys = pygame.key.get_pressed()       # first poll
self.direction.x = int(keys[...])
...
recent_keys = pygame.key.get_pressed()  # second poll, same thing
if recent_keys[pygame.K_SPACE]:
```
**After:**
```python
keys = pygame.key.get_pressed()  # one poll, used for everything
self.direction.x = int(keys[...])
...
if keys[pygame.K_SPACE]:
```

**Why:** `pygame.key.get_pressed()` takes a snapshot of every key on the keyboard at that exact millisecond. Calling it twice in the same frame is redundant — the keyboard state doesn't change between two lines of code. We reused the first snapshot for everything.

---

## 4. Player Boundary Clamping

**Added:**
```python
self.rect.clamp_ip(pygame.Rect(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT))
```

**Why:** Without this, the cat could walk off the edges of the screen and disappear. `clamp_ip` is a pygame rectangle method — it takes a boundary rectangle and forces your rect to stay inside it. The `_ip` means "in place" (modifies directly instead of returning a new rect).

**Algorithm:** After every movement update, snap the player's position back inside the screen bounds. One line runs after every move, so it's impossible to escape.

---

## 5. Game Over Screen

**Before:** When you died, `running = False` was set and the window just closed silently.

**After:** A semi-transparent dark overlay is drawn on top of the game, with "GAME OVER", your score, best score, and instructions.

```python
overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
overlay.fill((0, 0, 0, 160))  # black with 160/255 opacity
display_surface.blit(overlay, (0, 0))
```

**Why:** `pygame.SRCALPHA` creates a surface that supports transparency. The `160` in the color tuple is the alpha (opacity) value — 0 is invisible, 255 is solid. We blit (draw) it on top of the frozen game frame so you can still see the battlefield underneath.

**Algorithm:** Game state gets a `game_over` boolean flag. When it's `True`, the game loop skips updates and collision checks but still draws the last frame, then draws the overlay on top of it.

---

## 6. Restart Without Relaunching

**Added:**
```python
def reset_game():
    score = 0
    lives = 3
    game_over = False
    all_sprites.empty()
    meow_sprites.empty()
    monster_sprites.empty()
    yarn_sprites.empty()
    for _ in range(20):
        Yarn(...)
    return Cat(all_sprites)
```

**Why:** When you press R, we need to wipe everything and start fresh. `sprite_group.empty()` removes every sprite from every group instantly. Then we rebuild the stars and a new cat. The function returns the new cat so the main loop's `cat` variable points to the fresh one.

**Algorithm:** Clear all groups → re-spawn background stars → create new player → reset score and lives → flip `game_over` back to `False`. One function call resets the entire game state.

---

## 7. Difficulty Scaling

**Added:**
```python
def get_spawn_interval():
    elapsed = (pygame.time.get_ticks() - game_start_time) / 1000
    return max(150, int(500 - elapsed * 5))
```

**Why:** The original game spawned a monster every 500ms forever. It never got harder, so experienced players could just farm forever. This function calculates how long to wait before the next spawn based on how many seconds have passed.

**Algorithm:**
- `elapsed` = seconds since game started
- `500 - elapsed * 5` = starts at 500ms, shrinks by 5ms every second
- `max(150, ...)` = never goes below 150ms (a hard floor so it doesn't become impossible)
- After each spawn, we call `pygame.time.set_timer(MONSTER_SPAWN_EVENT, get_spawn_interval())` to reset the timer to the new shorter interval

So at 0s → 500ms gap. At 30s → 350ms gap. At 70s → 150ms gap (maximum difficulty).

---

## 8. Lives System

**Added:** `lives = 3` global, decremented on hit, game over only when `lives <= 0`.

**Before:** One touch = instant death.

**After:**
```python
if collision_sprites:
    lives -= 1
    if lives <= 0:
        game_over = True
```

**Why:** Instant death with no feedback loop is punishing and not fun. Three lives gives the player a chance to recover from a mistake. The lives counter in the top-left is the HUD (heads-up display) — drawn every frame so it always reflects the current value.

---

## 9. High Score Tracking

```python
high_score = 0
...
if lives <= 0:
    game_over = True
    if score > high_score:
        high_score = score
```

**Why:** High score only gets updated at the moment you die (when the game is actually over). It persists in memory across restarts because it's a regular variable — not reset by `reset_game()`. So no matter how many times you restart, it holds your best run.

**Algorithm:** On death, compare current score to stored high score. If better, overwrite. Display it in gold on the game over screen.

---

## The Big Picture — How the Game Loop Works

Every frame the loop does exactly 4 things in order:

```
1. EVENTS     → did the player press a key? did a monster spawn timer fire?
2. UPDATE     → move everything (player, bullets, monsters, animations)
3. COLLISIONS → did anything hit anything?
4. DRAW       → paint the current state to the screen
```

The `game_over` flag acts as a gate — when it's `True`, steps 2 and 3 are skipped so the game freezes in place, and step 4 draws the overlay on top. When the player presses R, `reset_game()` rebuilds everything and the gate opens again.

That's the entire engine. Clean, linear, and predictable.

---

## 10. Persistent High Score

**Before:** `high_score = 0` — resets every time the game is closed.

**After:**
```python
SAVE_FILE = join(BASE_DIR, 'save_data.json')

def load_high_score():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, 'r') as f:
            return json.load(f).get('high_score', 0)
    return 0

def save_high_score(value):
    with open(SAVE_FILE, 'w') as f:
        json.dump({'high_score': value}, f)
```

**Why:** The high score was stored in a plain Python variable — gone the moment you quit. Now we write it to `save_data.json` next to the game file. JSON is human-readable, so you could even edit it manually. `os.path.exists` guards against the first run when no file exists yet.

**Algorithm:** Load once at startup → update only on death if beaten → write to disk immediately so a crash can't erase it.

---

## 11. Sound Mute Toggle

**Added:**
```python
if event.type == KEYDOWN and event.key == pygame.K_m:
    muted = not muted
    pygame.mixer.pause() if muted else pygame.mixer.unpause()
```

**Why:** `pygame.mixer.pause()` suspends every playing channel simultaneously — music, effects, everything. `unpause()` resumes them all from where they stopped. A single boolean toggle is the cleanest way to track state because the mixer itself is stateful; we just flip it on or off.

---

## 12. Pause Functionality

**Added:** `paused` boolean that gates both updates and the monster spawn event.

**Why:** When paused, we need to stop sprite movement AND stop new monsters from spawning. The spawn timer keeps firing even when sprites don't update, so we check `paused` in both the event handler and the update block. The overlay is drawn on top of the frozen last frame — same pattern as the game over screen.

**Algorithm:** `P` key flips `paused`. Update and spawn are both gated by `not paused`. Draw overlay on top when paused.

---

## 13. Invincibility Frames After Hit

**Added to `Cat`:**
```python
def hit(self):
    self.invincible = True
    self.invincible_start = pygame.time.get_ticks()

def invincibility_timer(self):
    if self.invincible:
        now = pygame.time.get_ticks()
        if now - self.invincible_start >= self.invincible_duration:
            self.invincible = False
            self.image = self.original_image
        else:
            visible = (now // 100) % 2 == 0
            self.image = self.original_image if visible else pygame.Surface(...)
```

**Why:** Without iframes, a group of three monsters touching the cat drains all 3 lives in one frame. The `(now // 100) % 2` trick creates a 10Hz strobe — the sprite alternates between visible and invisible every 100ms for 1.5 seconds, giving the player a clear visual signal that they're protected.

**Algorithm:** On hit → set `invincible = True` and record timestamp. Each frame, check elapsed time. Strobe the image at 10Hz. After 1.5s, restore original image and clear the flag. Collision check skipped entirely while `invincible` is `True`.

---

## 14. Screen Shake on Hit

**Added:**
```python
shake_timer = 300  # ms, set on hit

if shake_timer > 0:
    shake_timer = max(0, shake_timer - dt * 1000)
    shake_x = randint(-8, 8)
    shake_y = randint(-8, 8)
```

**Why:** Instead of drawing sprites directly to `display_surface`, we draw everything to a `game_surf` intermediate surface, then blit that surface to `display_surface` at `(shake_x, shake_y)`. Random offsets every frame within ±8px creates a jitter effect. Decrementing by `dt * 1000` converts milliseconds-per-frame to a real time decay.

---

## 15. Kill Combo Multiplier

**Added:**
```python
def update_score(base=1):
    combo += 1
    combo_timer = pygame.time.get_ticks()
    multiplier = min(combo, 5)
    score += base * multiplier
```

**Why:** Chaining kills within 2 seconds ramps the multiplier from 1x up to 5x. `min(combo, 5)` caps it so the game doesn't become trivially broken at long chains. The 2-second window is long enough to reward burst play but short enough that you can't just slowly farm it.

**Algorithm:** Each kill increments `combo` and resets `combo_timer`. Every frame, if `time.get_ticks() - combo_timer > 2000`, reset `combo` to 0.

---

## 16. Rapid-Fire Power-Up

**Added:**
```python
class PowerUp(pygame.sprite.Sprite):
    # Blue circle that falls from monster kill position
    ...

if randint(1, 5) == 1:
    PowerUp(meow.rect.midtop, (all_sprites, powerup_sprites))

picked = pygame.sprite.spritecollide(cat, powerup_sprites, True)
if picked:
    cat.cooldown_duration = 100
    rapid_fire_timer = pygame.time.get_ticks()
```

**Why:** A 20% drop chance (1-in-5) keeps power-ups rare but frequent enough to feel impactful. Picking one slashes the shoot cooldown from 400ms to 100ms for 5 seconds. After 5s the cooldown resets. `pygame.sprite.spritecollide(..., True)` with the third arg `True` kills the powerup on contact — no extra `.kill()` needed.

---

## 17. Fast Red Enemy Type

**Added:** `FastMonster` class — same as `Monster` but tinted red and moving 70–80% faster, with a `score_value = 3` attribute.

**Why:** Without enemy variety the game gets monotonous. `surf.copy()` duplicates the surface so we can tint one copy without affecting the original. `pygame.BLEND_RGBA_MULT` multiplies each pixel's RGBA by the overlay color — a red tint makes it visually distinct without loading a second image.

**Algorithm:** After 30 seconds of gameplay, each spawn event has a 25% chance to spawn a `FastMonster` instead. The `score_value` attribute is read at kill time via `getattr(m, 'score_value', 1)`, so normal monsters default to 1 and fast monsters give 3.

---

## 18. Start Screen

**Added:** `on_start_screen` boolean that holds the game in a title overlay until `SPACE` is pressed.

**Why:** Without a start screen the game launches straight into gameplay — jarring and skips the difficulty selector. The start screen draws over the idle game world (sprites exist but don't update), shows the best score from disk, and explains controls.

---

## 19. Kill Counter HUD

**Added:** `kills` global incremented in `update_score`, displayed top-right.

**Why:** Score and kills tell you different things — score reflects combo efficiency, kills is raw output. Showing both lets players track their accuracy without needing to do math.

---

## 20. Hit Sound (Synthesized)

**Added:**
```python
import numpy as np

def make_hit_sound():
    t = np.linspace(0, 0.15, int(44100 * 0.15), endpoint=False)
    wave = (np.sin(2 * np.pi * 180 * t) * 0.4 * np.exp(-t * 20)).astype(np.float32)
    stereo = np.column_stack([wave, wave])
    return pygame.sndarray.make_sound((stereo * 32767).astype(np.int16))
```

**Why:** There's no hit sound file in the audio folder. Rather than add a new asset, we synthesize one at startup using numpy. `np.exp(-t * 20)` is an exponential decay envelope — it makes the sound fade out naturally in ~150ms. `180 Hz` is a low, "thump" frequency. The result is converted to 16-bit stereo PCM that pygame can play directly.

---

## 21. Difficulty Selector

**Added:**
```python
DIFFICULTY_SETTINGS = {
    'Easy':   {'spawn_base': 700, 'spawn_min': 300, 'speed_range': (250, 350)},
    'Normal': {'spawn_base': 500, 'spawn_min': 150, 'speed_range': (400, 500)},
    'Hard':   {'spawn_base': 300, 'spawn_min': 80,  'speed_range': (500, 700)},
}
```

**Why:** A single dictionary drives both spawn timing and monster speed. `get_spawn_interval()` reads `spawn_base` and `spawn_min`; `Monster.__init__` reads `speed_range`. Press D on the start screen to cycle. This data-driven approach means adding a new difficulty is one dictionary entry.

---

## 22. Heart Icons for Lives

**Added:**
```python
def draw_heart(surface, x, y, size, filled):
    r = size // 4
    pygame.draw.circle(surface, color, (x + r, y + r), r)
    pygame.draw.circle(surface, color, (x + size - r, y + r), r)
    pygame.draw.polygon(surface, color, [(x, y+r), (x+size//2, y+size), (x+size, y+r)])
```

**Why:** A heart is two overlapping circles (the bumps) plus a downward triangle (the point). Drawing it with primitives means no extra image asset. Filled hearts are bright red; lost ones are dark — immediately readable at a glance. `i < lives` maps array index to filled/empty.

---

## The Full State Machine

The game now has four states:

```
START_SCREEN → PLAYING → GAME_OVER
                 ↕
               PAUSED
```

- `on_start_screen = True` → show title, D cycles difficulty, SPACE starts
- `paused = True` → freeze updates, show overlay, P resumes
- `game_over = True` → freeze updates, show score summary, R restarts
- All three `False` → normal gameplay
