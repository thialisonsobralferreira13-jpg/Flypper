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
bird_image = pygame.image.load("assets/player.png").convert_alpha()
bird_image = pygame.transform.smoothscale(bird_image, (96, 64))
cable_top_image = pygame.image.load("assets/rj45.png").convert_alpha()
cable_bottom_image = pygame.image.load("assets/rj45_bottom.png").convert_alpha()
cable_top_image = pygame.transform.smoothscale(cable_top_image, (78, 67))
cable_bottom_image = pygame.transform.smoothscale(cable_bottom_image, (78, 67))
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
    screen.blit(bird_image, bird_image.get_rect(center=(118, int(y))))


def draw_pipe(pipe: dict) -> None:
    x, top = int(pipe["x"]), int(pipe["top"])
    bottom = top + PIPE_GAP
    cable, edge, shine = (20, 116, 233), (7, 84, 173), (101, 173, 255)
    cable_x = x + PIPE_WIDTH // 2
    connector_height = cable_top_image.get_height()
    pygame.draw.rect(screen, cable, (cable_x - 9, 0, 18, top - connector_height + 8))
    pygame.draw.line(screen, shine, (cable_x - 3, 0), (cable_x - 3, top - connector_height + 8), 2)
    screen.blit(cable_top_image, cable_top_image.get_rect(midbottom=(cable_x, top + 1)))
    lower_rect = cable_bottom_image.get_rect(midtop=(cable_x, bottom - 1))
    pygame.draw.rect(screen, cable, (cable_x - 9, bottom + connector_height - 8, 18, GROUND - bottom - connector_height + 8))
    pygame.draw.line(screen, shine, (cable_x - 3, bottom + connector_height - 8), (cable_x - 3, GROUND), 2)
    screen.blit(cable_bottom_image, lower_rect)


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
    half_height = 25
    half_width = 22
    if game["bird_y"] - half_height < 0 or game["bird_y"] + half_height > GROUND:
        game["state"] = "over"
    for pipe in game["pipes"]:
        overlaps_x = 118 + half_width > pipe["x"] and 118 - half_width < pipe["x"] + PIPE_WIDTH
        outside_gap = game["bird_y"] - half_height < pipe["top"] or game["bird_y"] + half_height > pipe["top"] + PIPE_GAP
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
