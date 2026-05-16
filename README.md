# Meow-nster Shooter

A fast-paced 2D arcade shooter where you control a cat battling waves of monsters. Survive as long as you can, rack up points, and beat your high score.

## Features

- **Player Movement** — Arrow keys, with full screen-boundary clamping
- **Laser Shooting** — Spacebar with cooldown system
- **Lives System** — Start with 3 lives; lose one per monster hit
- **Difficulty Scaling** — Monster spawn rate increases over time
- **Score System** — Earn points for each monster defeated
- **Session High Score** — Tracks your best score across restarts
- **Game Over Screen** — Shows final score, best score, and restart option
- **Animated Explosions** — Paw explosion animation on monster kills
- **Sound & Music** — Background music and sound effects

## Controls

| Key | Action |
|---|---|
| Arrow Keys | Move cat |
| Space | Shoot |
| R | Restart (on game over screen) |
| Q | Quit (on game over screen) |

## Installation

### Prerequisites

- Python 3.8+
- pygame

```bash
pip install -r requirements.txt
```

### Run

```bash
cd CatShooter
python game.py
```
