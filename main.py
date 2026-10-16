

import random
import sqlite3
import tkinter as tk
from pathlib import Path


WIDTH, HEIGHT = 480, 640
GROUND_HEIGHT = 82
PLAY_HEIGHT = HEIGHT - GROUND_HEIGHT
FPS_MS = 16
GRAVITY = 0.42
FLAP_POWER = -7.2
PIPE_SPEED = 3.2
PIPE_WIDTH = 72
PIPE_GAP = 172
PIPE_INTERVAL = 92
DATABASE_PATH = Path(__file__).with_name("flappy_bird.db")


class FlappyBird:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        root.title("Flappy Bird — Python")
        root.resizable(False, False)
        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, highlightthickness=0)
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self.flap)
        root.bind("<space>", self.flap)
        root.bind("<Up>", self.flap)
        root.bind("<r>", self.restart)
        root.bind("<R>", self.restart)
        self.bird_photo = tk.PhotoImage(file=Path(__file__).with_name("assets") / "player.png")
        scale = max(1, (self.bird_photo.width() + 95) // 96)
        self.bird_sprite = self.bird_photo.subsample(scale, scale)
        cable_path = Path(__file__).with_name("assets")
        cable_scale = 7
        cable_top = tk.PhotoImage(file=cable_path / "rj45.png")
        cable_bottom = tk.PhotoImage(file=cable_path / "rj45_bottom.png")
        self.cable_top_sprite = cable_top.subsample(cable_scale, cable_scale)
        self.cable_bottom_sprite = cable_bottom.subsample(cable_scale, cable_scale)
        self.cable_sprite_height = self.cable_top_sprite.height()
        self.best = self.load_best_score()
        self.reset()
        self.draw()

    @staticmethod
    def load_best_score() -> int:
        """Cria o banco, caso necessário, e lê o recorde salvo."""
        with sqlite3.connect(DATABASE_PATH) as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS record (id INTEGER PRIMARY KEY CHECK (id = 1), score INTEGER NOT NULL)"
            )
            row = connection.execute("SELECT score FROM record WHERE id = 1").fetchone()
            return int(row[0]) if row else 0

    def save_best_score(self) -> None:
        with sqlite3.connect(DATABASE_PATH) as connection:
            connection.execute(
                "INSERT INTO record (id, score) VALUES (1, ?) "
                "ON CONFLICT(id) DO UPDATE SET score = excluded.score",
                (self.best,),
            )

    def reset(self) -> None:
        self.bird_x = 118
        self.bird_y = PLAY_HEIGHT / 2
        self.bird_vy = 0.0
        self.pipes: list[dict[str, float | bool]] = []
        self.frame = 0
        self.score = 0
        self.state = "ready"

    def flap(self, _event: tk.Event | None = None) -> None:
        if self.state == "over":
            self.restart()
        if self.state == "ready":
            self.state = "playing"
        if self.state == "playing":
            self.bird_vy = FLAP_POWER

    def restart(self, _event: tk.Event | None = None) -> None:
        self.reset()
        self.tick()

    def add_pipe(self) -> None:
        top = random.randint(62, PLAY_HEIGHT - PIPE_GAP - 62)
        self.pipes.append({"x": WIDTH + 8, "top": top, "scored": False})

    def update(self) -> None:
        if self.state != "playing":
            return
        self.frame += 1
        if self.frame % PIPE_INTERVAL == 0:
            self.add_pipe()
        self.bird_vy += GRAVITY
        self.bird_y += self.bird_vy

        for pipe in self.pipes:
            pipe["x"] = float(pipe["x"]) - PIPE_SPEED
            if not pipe["scored"] and float(pipe["x"]) + PIPE_WIDTH < self.bird_x:
                pipe["scored"] = True
                self.score += 1
                if self.score > self.best:
                    self.best = self.score
                    self.save_best_score()
        self.pipes = [p for p in self.pipes if float(p["x"]) + PIPE_WIDTH > -5]

        half_height = 25
        half_width = 22
        if self.bird_y - half_height < 0 or self.bird_y + half_height > PLAY_HEIGHT:
            self.state = "over"
            return
        for pipe in self.pipes:
            x = float(pipe["x"])
            top = float(pipe["top"])
            overlaps_x = self.bird_x + half_width > x and self.bird_x - half_width < x + PIPE_WIDTH
            outside_gap = self.bird_y - half_height < top or self.bird_y + half_height > top + PIPE_GAP
            if overlaps_x and outside_gap:
                self.state = "over"
                return

    def draw_background(self) -> None:
        c = self.canvas
        c.create_rectangle(0, 0, WIDTH, PLAY_HEIGHT, fill="#70c5ce", outline="")
        # Nuvens simples dão profundidade sem imagens ou recursos externos.
        for x, y in ((52, 105), (320, 80), (400, 205)):
            c.create_oval(x, y, x + 48, y + 22, fill="#d9f3ee", outline="")
            c.create_oval(x + 14, y - 11, x + 42, y + 16, fill="#d9f3ee", outline="")
        c.create_rectangle(0, PLAY_HEIGHT, WIDTH, HEIGHT, fill="#ded895", outline="")
        c.create_rectangle(0, PLAY_HEIGHT, WIDTH, PLAY_HEIGHT + 13, fill="#8bd04a", outline="")
        for x in range(-20, WIDTH + 30, 34):
            offset = (self.frame * 3) % 34 if self.state == "playing" else 0
            xx = x - offset
            c.create_line(xx, PLAY_HEIGHT + 18, xx + 17, PLAY_HEIGHT + 18, fill="#c4b96c", width=3)

    def draw_pipe(self, x: float, top: float) -> None:
        c = self.canvas
        bottom = top + PIPE_GAP
        cable, edge, shine = "#1474e9", "#0754ad", "#65adff"
        cable_x = x + PIPE_WIDTH / 2
        connector_height = self.cable_sprite_height
        # O cabo se prolonga por trás do conector fotográfico para parecer contínuo.
        c.create_rectangle(cable_x - 9, 0, cable_x + 9, top - connector_height + 8, fill=cable, outline=edge, width=2)
        c.create_line(cable_x - 3, 0, cable_x - 3, top - connector_height + 8, fill=shine, width=2)
        c.create_image(cable_x, top - connector_height / 2, image=self.cable_top_sprite)
        c.create_rectangle(cable_x - 9, bottom + connector_height - 8, cable_x + 9, PLAY_HEIGHT, fill=cable, outline=edge, width=2)
        c.create_line(cable_x - 3, bottom + connector_height - 8, cable_x - 3, PLAY_HEIGHT, fill=shine, width=2)
        c.create_image(cable_x, bottom + connector_height / 2, image=self.cable_bottom_sprite)

    def draw_bird(self) -> None:
        c = self.canvas
        x, y = self.bird_x, self.bird_y
        c.create_image(x, y, image=self.bird_sprite)

    def draw(self) -> None:
        self.canvas.delete("all")
        self.draw_background()
        for pipe in self.pipes:
            self.draw_pipe(float(pipe["x"]), float(pipe["top"]))
        self.draw_bird()
        self.canvas.create_text(WIDTH / 2, 43, text=str(self.score), font=("Arial", 32, "bold"), fill="white")
        self.canvas.create_text(WIDTH - 72, 25, text=f"RECORDE {self.best}", font=("Arial", 10, "bold"), fill="#fff8df")
        if self.state == "ready":
            self.draw_card("FLAPPY BIRD", "Pressione ESPAÇO, ↑ ou clique para voar", "Desvie dos canos e marque pontos!")
        elif self.state == "over":
            self.draw_card("FIM DE JOGO", f"Pontuação: {self.score}    Recorde: {self.best}", "Clique ou pressione ESPAÇO para jogar de novo")

    def draw_card(self, title: str, line1: str, line2: str) -> None:
        c = self.canvas
        c.create_rectangle(38, 230, WIDTH - 38, 365, fill="#fff8df", outline="#bd8d3a", width=3)
        c.create_text(WIDTH / 2, 263, text=title, font=("Arial", 25, "bold"), fill="#58452a")
        c.create_text(WIDTH / 2, 307, text=line1, font=("Arial", 12, "bold"), fill="#594c35")
        c.create_text(WIDTH / 2, 338, text=line2, font=("Arial", 11), fill="#77694f")

    def tick(self) -> None:
        self.update()
        self.draw()
        self.root.after(FPS_MS, self.tick)


def main() -> None:
    root = tk.Tk()
    FlappyBird(root).tick()
    root.mainloop()


if __name__ == "__main__":
    main()
