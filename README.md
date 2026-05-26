# 🧮♟️ Math Checkers

A Python desktop game that combines classic Checkers with Math Challenges. To capture an opponent's piece, you must correctly answer a math question — or lose your turn!

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python)
![Pygame](https://img.shields.io/badge/Pygame-2.x-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 🎮 Features

- ♟️ Full 8x8 Checkers with king promotion
- 🧠 Math challenges on every capture (add, subtract, multiply)
- 🤖 AI opponent with adjustable difficulty (Easy / Average / Hard)
- 🎵 Background music and sound effects
- 💾 Save and load game state
- ↩️ Undo moves
- 🏆 Winner detection with Game Over popup and final scores
- 🎨 Multiple board themes (Wood, Marble, Gradient, Dark)
- ⏱️ Optional timed mode for extra pressure

---

## 📸 Screenshot

> ![Screenshot](Screenshot%202026-05-26%20182857.png)

---

## 🚀 Getting Started

### Requirements
- Python 3.8 or higher
- See `requirements.txt` for all dependencies

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/math-checkers.git
   cd math-checkers
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the game**
   ```bash
   python main.py
   ```

---

## 🕹️ How to Play

1. Launch the game and click **Play**
2. Choose your **Math Type** (Integers, Fractions, Algebra)
3. Choose your **Difficulty** (Easy, Average, Hard)
4. Move your pieces diagonally on dark squares
5. When you attempt a **capture**, a math question appears
6. Answer correctly → capture succeeds and you gain points!
7. Answer wrong → your turn is forfeit
8. **Win** by eliminating all opponent pieces or leaving them with no valid moves

### Keyboard Shortcuts
| Key | Action |
|-----|--------|
| `U` | Undo last move |
| `S` | Save game |
| `ESC` | Deselect / cancel |

---

## 📁 Project Structure

```
math-checkers/
├── main.py          # Entry point — run this to start
├── game.py          # Game logic, turns, scoring, winner detection
├── ui.py            # Pygame UI, rendering, input handling
├── board.py         # Board state and move validation
├── piece.py         # Piece class (color, value, king)
├── ai.py            # AI opponent logic
├── mathgen.py       # Math question generator
├── savegame.py      # Save/load system
├── requirements.txt # Python dependencies
├── bg.png           # Background image
├── bg_music.mp3     # Background music
├── button.wav       # Button click sound
├── capture.wav      # Capture sound effect
└── move.wav         # Move sound effect
```

---

## 🧩 Built With

- [Python](https://www.python.org/)
- [Pygame](https://www.pygame.org/)

---

## 📄 License

This project is licensed under the MIT License — feel free to use, modify, and share it.

---

## 🙌 Contributing

Pull requests are welcome! Feel free to open an issue for bugs, suggestions, or new features.
