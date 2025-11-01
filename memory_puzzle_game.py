
import tkinter as tk
from tkinter import messagebox
import random
import time

# Configuration
GRID_ROWS = 4
GRID_COLS = 4
CARD_BACK = "❓"
REVEAL_DELAY_MS = 800  # delay before hiding unmatched cards (milliseconds)

# Emoji pool (ensure at least GRID_ROWS*GRID_COLS/2 unique items)
EMOJI_POOL = [
    "🐶","🐱","🦊","🐼","🐵","🦁","🐸","🐷",
    "🍎","🍌","🍇","🍓","🍒","🍍","🥝","🍉",
    "⚽","🏀","🏈","🎾","🎲","🎯","🎮","🎸",
    "🌟","☀️","🌈","🍀","🔥","❄️","🌊","🌙"
]

class MemoryGame(tk.Tk):
    def __init__(self, rows=GRID_ROWS, cols=GRID_COLS):
        super().__init__()
        self.title("Memory Puzzle Game")
        self.resizable(False, False)

        self.rows = rows
        self.cols = cols
        if (rows * cols) % 2 != 0:
            raise ValueError("Grid must contain an even number of cards")

        self.num_pairs = (rows * cols) // 2
        self.emojis = self._prepare_deck()

        self.buttons = {}  # (r,c) -> button
        self.card_values = {}  # (r,c) -> emoji
        self.revealed = {}  # (r,c) -> bool
        self.matched = set()

        self.first_selection = None
        self.second_selection = None
        self.locked = False

        self.move_count = 0
        self.start_time = None
        self.timer_running = False
        self.best_score = None  # (moves, seconds)

        self._build_ui()
        self._place_cards()

    def _prepare_deck(self):
        pool = EMOJI_POOL.copy()
        random.shuffle(pool)
        needed = self.num_pairs
        if needed > len(pool):
            raise ValueError("Not enough unique emoji in pool for requested grid size")
        selected = pool[:needed]
        deck = selected * 2
        random.shuffle(deck)
        return deck

    def _build_ui(self):
        top_frame = tk.Frame(self)
        top_frame.grid(row=0, column=0, padx=8, pady=8, sticky="ew")

        self.moves_label = tk.Label(top_frame, text="Moves: 0", font=(None, 12))
        self.moves_label.pack(side="left", padx=(0, 10))

        self.timer_label = tk.Label(top_frame, text="Time: 00:00", font=(None, 12))
        self.timer_label.pack(side="left", padx=(0, 10))

        restart_btn = tk.Button(top_frame, text="Restart", command=self.restart)
        restart_btn.pack(side="right")

        # Card grid
        grid_frame = tk.Frame(self)
        grid_frame.grid(row=1, column=0, padx=8, pady=(0,8))

        for r in range(self.rows):
            for c in range(self.cols):
                b = tk.Button(grid_frame, text=CARD_BACK, width=6, height=3,
                              font=(None, 20), command=lambda r=r, c=c: self.on_card_click(r, c))
                b.grid(row=r, column=c, padx=5, pady=5)
                self.buttons[(r,c)] = b
                self.revealed[(r,c)] = False

    def _place_cards(self):
        idx = 0
        for r in range(self.rows):
            for c in range(self.cols):
                self.card_values[(r,c)] = self.emojis[idx]
                idx += 1

    def on_card_click(self, r, c):
        if self.locked:
            return
        if (r,c) in self.matched:
            return
        if self.revealed[(r,c)]:
            return

        if not self.timer_running:
            self.start_timer()

        self._reveal_card(r,c)

        if self.first_selection is None:
            self.first_selection = (r,c)
            return

        if self.second_selection is None and (r,c) != self.first_selection:
            self.second_selection = (r,c)
            self.move_count += 1
            self._update_move_label()
            self._check_for_match()

    def _reveal_card(self, r, c):
        val = self.card_values[(r,c)]
        btn = self.buttons[(r,c)]
        btn.config(text=val, state="disabled")
        self.revealed[(r,c)] = True

    def _hide_card(self, r, c):
        btn = self.buttons[(r,c)]
        btn.config(text=CARD_BACK, state="normal")
        self.revealed[(r,c)] = False

    def _check_for_match(self):
        a = self.first_selection
        b = self.second_selection
        if not a or not b:
            return

        va = self.card_values[a]
        vb = self.card_values[b]

        if va == vb:
            # matched
            self.matched.add(a)
            self.matched.add(b)
            self.first_selection = None
            self.second_selection = None
            if len(self.matched) == self.rows * self.cols:
                self._on_game_won()
        else:
            # not matched: temporarily lock input and hide after delay
            self.locked = True
            self.after(REVEAL_DELAY_MS, self._unreveal_pair)

    def _unreveal_pair(self):
        a = self.first_selection
        b = self.second_selection
        if a:
            self._hide_card(*a)
        if b:
            self._hide_card(*b)
        self.first_selection = None
        self.second_selection = None
        self.locked = False

    def _update_move_label(self):
        self.moves_label.config(text=f"Moves: {self.move_count}")

    def start_timer(self):
        self.start_time = time.time()
        self.timer_running = True
        self._tick()

    def _tick(self):
        if not self.timer_running:
            return
        elapsed = int(time.time() - self.start_time)
        mins = elapsed // 60
        secs = elapsed % 60
        self.timer_label.config(text=f"Time: {mins:02d}:{secs:02d}")
        # schedule next update
        self.after(500, self._tick)

    def stop_timer(self):
        self.timer_running = False

    def _on_game_won(self):
        self.stop_timer()
        elapsed = int(time.time() - self.start_time) if self.start_time else 0
        msg = f"You won!\nMoves: {self.move_count}\nTime: {elapsed//60:02d}:{elapsed%60:02d}"
        # update best score
        new_score = (self.move_count, elapsed)
        if self.best_score is None or new_score < self.best_score:
            self.best_score = new_score
            msg += "\nNew best score!"
        messagebox.showinfo("Congratulations", msg)

    def restart(self):
        # reset state and reshuffle
        self.stop_timer()
        self.move_count = 0
        self._update_move_label()
        self.timer_label.config(text="Time: 00:00")
        self.start_time = None
        self.timer_running = False
        self.first_selection = None
        self.second_selection = None
        self.locked = False
        self.matched.clear()

        # shuffle deck and reassign
        random.shuffle(self.emojis)
        idx = 0
        for r in range(self.rows):
            for c in range(self.cols):
                self.card_values[(r,c)] = self.emojis[idx]
                idx += 1
                self._hide_card(r,c)

    def run(self):
        self.mainloop()


if __name__ == "__main__":
    try:
        app = MemoryGame()
        app.run()
    except Exception as e:
        print("Error:", e)
