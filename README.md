# Meow-nster Shooter

A fast-paced 2D arcade shooter where you control a cat battling waves of monsters. Survive as long as you can, rack up points, and beat your high score.

## Features

- **Player Movement** — Arrow keys, with full screen-boundary clamping
- **Laser Shooting** — Spacebar with cooldown system
- **Lives System** — 3 heart icons; lose one per monster hit
- **Invincibility Frames** — 1.5s of flashing immunity after each hit
- **Screen Shake** — Camera jolts on damage for physical feedback
- **Difficulty Selector** — Easy, Normal, or Hard — choose on the start screen
- **Difficulty Scaling** — Monster spawn rate increases over time
- **Fast Red Enemies** — Appear after 30s, move faster, worth 3 pts each
- **Score System** — Earn points for each monster defeated
- **Kill Combo Multiplier** — Chain kills within 2s for up to 5x points
- **Rapid-Fire Power-Up** — Blue orb drops from monsters; cuts cooldown for 5s
- **Kill Counter** — Tracks total monsters destroyed this run
- **Persistent High Score** — Best score saved to disk, survives closing the game
- **Start Screen** — Title screen with difficulty picker before the action begins
- **Pause** — Freeze gameplay at any time
- **Sound Mute Toggle** — Silence all audio instantly
- **Game Over Screen** — Shows final score, best score, and restart option
- **Animated Explosions** — Paw explosion animation on monster kills
- **Sound & Music** — Background music, shoot, kill, and hit sound effects

## Controls

| Key | Action |
|---|---|
| Arrow Keys | Move cat |
| Space | Shoot |
| D | Cycle difficulty (on start screen) |
| P | Pause / Resume |
| M | Mute / Unmute audio |
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
