"""Versão web do Flappy Bird. Executada em Python no navegador com Pygbag."""

import asyncio
import random
import sys

import pygame


WIDTH, HEIGHT = 480, 640
GROUND = 558
GRAVITY = 0.42
FLAP_POWER = -7.2
PIPE_SPEED = 3.2
PIPE_WIDTH = 72
PIPE_GAP = 172
PIPE_INTERVAL = 92
SKY = (112, 197, 206)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Flappy Bird")
clock = pygame.time.Clock()
font = pygame.font.SysFont("arial", 28, bold=True)
small_font = pygame.font.SysFont("arial", 15, bold=True)
tiny_font = pygame.font.SysFont("arial", 13)

if sys.platform == "emscripten":
    import platform as browser_platform


def load_best() -> int:
    if sys.platform == "emscripten":
        try:
            return int(browser_platform.window.localStorage.getItem("flypper_best") or 0)
        except (TypeError, ValueError):
            return 0
    try:
        with open("web_record.txt", encoding="utf-8") as record_file:
            return int(record_file.read().strip() or 0)
    except (OSError, ValueError):
        return 0


def save_best(value: int) -> None:
    if sys.platform == "emscripten":
        browser_platform.window.localStorage.setItem("flypper_best", str(value))
    else:
        with open("web_record.txt", "w", encoding="utf-8") as record_file:
            record_file.write(str(value))


def reset_game() -> dict:
    return {
        "bird_y": GROUND / 2,
        "bird_vy": 0.0,
        "pipes": [],
        "frame": 0,
        "score": 0,
        "state": "ready",
    }


def draw_text(text: str, y: int, color: tuple, selected_font=font) -> None:
    image = selected_font.render(text, True, color)
    screen.blit(image, image.get_rect(center=(WIDTH // 2, y)))


def draw_bird(y: float, velocity: float) -> None:
    x = 118
    pygame.draw.ellipse(screen, (215, 154, 34), (x - 18, y - 13, 36, 28))
    pygame.draw.ellipse(screen, (255, 216, 61), (x - 16, y - 13, 32, 26))
    pygame.draw.ellipse(screen, (245, 184, 50), (x - 11, y + 1, 17, 10))
    pygame.draw.ellipse(screen, (255, 255, 255), (x + 3, y - 9, 10, 10))
    pygame.draw.circle(screen, (37, 37, 37), (x + 9, int(y - 4)), 2)
    pygame.draw.polygon(screen, (244, 123, 53), [(x + 14, y - 1), (x + 28, y + 3), (x + 14, y + 7)])
    wing_y = y + 2 + max(-5, min(6, velocity))
    pygame.draw.ellipse(screen, (255, 240, 160), (x - 12, wing_y, 14, 8))


def draw_pipe(pipe: dict) -> None:
    x, top = int(pipe["x"]), int(pipe["top"])
    bottom = top + PIPE_GAP
    green, dark, light = (88, 184, 67), (57, 140, 53), (141, 224, 90)
    pygame.draw.rect(screen, green, (x + 5, 0, PIPE_WIDTH - 10, top - 13))
    pygame.draw.rect(screen, dark, (x + 5, 0, PIPE_WIDTH - 10, top - 13), 3)
    pygame.draw.rect(screen, green, (x, top - 19, PIPE_WIDTH, 19))
    pygame.draw.rect(screen, dark, (x, top - 19, PIPE_WIDTH, 19), 3)
    pygame.draw.rect(screen, light, (x + 12, 0, 8, max(0, top - 21)))
    pygame.draw.rect(screen, green, (x + 5, bottom + 19, PIPE_WIDTH - 10, GROUND - bottom - 19))
    pygame.draw.rect(screen, dark, (x + 5, bottom + 19, PIPE_WIDTH - 10, GROUND - bottom - 19), 3)
    pygame.draw.rect(screen, green, (x, bottom, PIPE_WIDTH, 19))
    pygame.draw.rect(screen, dark, (x, bottom, PIPE_WIDTH, 19), 3)
    pygame.draw.rect(screen, light, (x + 12, bottom + 21, 8, max(0, GROUND - bottom - 21)))


def draw_scene(game: dict, best: int) -> None:
    screen.fill(SKY)
    for x, y in ((52, 105), (320, 80), (400, 205)):
        pygame.draw.ellipse(screen, (217, 243, 238), (x, y, 48, 22))
        pygame.draw.ellipse(screen, (217, 243, 238), (x + 14, y - 11, 28, 27))
    for pipe in game["pipes"]:
        draw_pipe(pipe)
    pygame.draw.rect(screen, (139, 208, 74), (0, GROUND, WIDTH, 13))
    pygame.draw.rect(screen, (222, 216, 149), (0, GROUND + 13, WIDTH, HEIGHT - GROUND - 13))
    offset = (game["frame"] * 3) % 34 if game["state"] == "playing" else 0
    for x in range(-20, WIDTH + 30, 34):
        pygame.draw.line(screen, (196, 185, 108), (x - offset, GROUND + 31), (x + 17 - offset, GROUND + 31), 3)
    draw_bird(game["bird_y"], game["bird_vy"])
    score_image = font.render(str(game["score"]), True, (255, 255, 255))
    screen.blit(score_image, score_image.get_rect(center=(WIDTH // 2, 43)))
    best_image = small_font.render(f"RECORDE {best}", True, (255, 248, 223))
    screen.blit(best_image, (WIDTH - best_image.get_width() - 16, 18))

    if game["state"] in ("ready", "over"):
        pygame.draw.rect(screen, (255, 248, 223), (38, 230, WIDTH - 76, 135), border_radius=8)
        pygame.draw.rect(screen, (189, 141, 58), (38, 230, WIDTH - 76, 135), 3, border_radius=8)
        if game["state"] == "ready":
            draw_text("FLAPPY BIRD", 265, (88, 69, 42))
            draw_text("ESPAÇO, ↑, toque ou clique para voar", 307, (89, 76, 53), small_font)
            draw_text("Desvie dos canos e marque pontos!", 338, (119, 105, 79), tiny_font)
        else:
            draw_text("FIM DE JOGO", 263, (88, 69, 42))
            draw_text(f"Pontuação: {game['score']}    Recorde: {best}", 307, (89, 76, 53), small_font)
            draw_text("Clique ou pressione ESPAÇO para recomeçar", 338, (119, 105, 79), tiny_font)
    pygame.display.flip()


def flap(game: dict) -> dict:
    if game["state"] == "over":
        game = reset_game()
    if game["state"] == "ready":
        game["state"] = "playing"
    if game["state"] == "playing":
        game["bird_vy"] = FLAP_POWER
    return game


def update_game(game: dict, best: int) -> int:
    if game["state"] != "playing":
        return best
    game["frame"] += 1
    if game["frame"] % PIPE_INTERVAL == 0:
        top = random.randint(62, GROUND - PIPE_GAP - 62)
        game["pipes"].append({"x": WIDTH + 8, "top": top, "scored": False})
    game["bird_vy"] += GRAVITY
    game["bird_y"] += game["bird_vy"]
    for pipe in game["pipes"]:
        pipe["x"] -= PIPE_SPEED
        if not pipe["scored"] and pipe["x"] + PIPE_WIDTH < 118:
            pipe["scored"] = True
            game["score"] += 1
            if game["score"] > best:
                best = game["score"]
                save_best(best)
    game["pipes"] = [pipe for pipe in game["pipes"] if pipe["x"] + PIPE_WIDTH > -5]
    radius = 15
    if game["bird_y"] - radius < 0 or game["bird_y"] + radius > GROUND:
        game["state"] = "over"
    for pipe in game["pipes"]:
        overlaps_x = 118 + radius > pipe["x"] and 118 - radius < pipe["x"] + PIPE_WIDTH
        outside_gap = game["bird_y"] - radius < pipe["top"] or game["bird_y"] + radius > pipe["top"] + PIPE_GAP
        if overlaps_x and outside_gap:
            game["state"] = "over"
            break
    return best


async def main() -> None:
    best = load_best()
    game = reset_game()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                if event.type == pygame.MOUSEBUTTONDOWN or event.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
                    game = flap(game)
                elif event.key == pygame.K_r:
                    game = reset_game()
        best = update_game(game, best)
        draw_scene(game, best)
        clock.tick(60)
        await asyncio.sleep(0)


asyncio.run(main())
