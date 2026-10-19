"""Versão web do Flappy Bird. Executada em Python no navegador com Pygbag."""

import asyncio
import math
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

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Flypper — Flappy Bird")
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
title_font = pygame.font.SysFont("arial", 27, bold=True)

# O céu em gradiente é preparado uma vez para não redesenhar 640 faixas a cada quadro.
background = pygame.Surface((WIDTH, HEIGHT))
for y in range(HEIGHT):
    blend = min(1.0, y / HEIGHT)
    color = tuple(round(top + (bottom - top) * blend) for top, bottom in zip((91, 185, 207), (207, 233, 218)))
    pygame.draw.line(background, color, (0, y), (WIDTH, y))

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
    angle = max(-25, min(25, -velocity * 3))
    sprite = pygame.transform.rotate(bird_image, angle)
    screen.blit(sprite, sprite.get_rect(center=(118, int(y))))


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
    screen.blit(background, (0, 0))
    # Colinas distantes e sol criam profundidade sem esconder os obstáculos.
    pygame.draw.circle(screen, (255, 235, 167), (386, 142), 35)
    pygame.draw.ellipse(screen, (153, 211, 190), (-105, 300, 390, 190))
    pygame.draw.ellipse(screen, (125, 197, 177), (170, 320, 430, 175))
    cloud_shift = int(game["frame"] * 0.35) % (WIDTH + 100) if game["state"] == "playing" else 0
    for base_x, y in ((52, 105), (320, 80), (400, 205)):
        x = (base_x - cloud_shift) % (WIDTH + 100) - 50
        pygame.draw.ellipse(screen, (255, 255, 246), (x, y, 56, 23))
        pygame.draw.ellipse(screen, (255, 255, 246), (x + 13, y - 13, 32, 31))
        pygame.draw.ellipse(screen, (255, 255, 246), (x + 31, y - 7, 29, 25))
    for pipe in game["pipes"]:
        draw_pipe(pipe)
    pygame.draw.rect(screen, (110, 190, 60), (0, GROUND, WIDTH, 15))
    pygame.draw.line(screen, (184, 232, 113), (0, GROUND + 2), (WIDTH, GROUND + 2), 3)
    pygame.draw.rect(screen, (226, 216, 151), (0, GROUND + 15, WIDTH, HEIGHT - GROUND - 15))
    offset = (game["frame"] * 3) % 34 if game["state"] == "playing" else 0
    for x in range(-20, WIDTH + 30, 34):
        pygame.draw.line(screen, (196, 185, 108), (x - offset, GROUND + 31), (x + 17 - offset, GROUND + 31), 3)
    bird_y = game["bird_y"]
    if game["state"] == "ready":
        bird_y += 5 * math.sin(pygame.time.get_ticks() / 180)
    draw_bird(bird_y, game["bird_vy"])
    # Placar com contorno e sombra para manter o contraste em qualquer fundo.
    pygame.draw.rect(screen, (27, 91, 112), (WIDTH // 2 - 34, 15, 68, 55), border_radius=16)
    pygame.draw.rect(screen, (255, 250, 225), (WIDTH // 2 - 37, 11, 74, 55), border_radius=16)
    score_image = title_font.render(str(game["score"]), True, (50, 72, 69))
    screen.blit(score_image, score_image.get_rect(center=(WIDTH // 2, 38)))
    best_label = small_font.render(f"RECORDE  {best}", True, (65, 76, 62))
    best_box = pygame.Rect(WIDTH - best_label.get_width() - 34, 19, best_label.get_width() + 22, 29)
    pygame.draw.rect(screen, (255, 250, 225), best_box, border_radius=14)
    screen.blit(best_label, (best_box.x + 11, best_box.y + 6))

    if game["state"] in ("ready", "over"):
        pygame.draw.rect(screen, (36, 93, 106), (43, 236, WIDTH - 76, 135), border_radius=20)
        pygame.draw.rect(screen, (255, 249, 224), (38, 230, WIDTH - 76, 135), border_radius=20)
        pygame.draw.rect(screen, (255, 255, 255), (43, 235, WIDTH - 86, 125), 2, border_radius=17)
        if game["state"] == "ready":
            draw_text("FLAPPY BIRD", 263, (48, 85, 75), title_font)
            draw_text("TOQUE OU CLIQUE PARA VOAR", 307, (89, 76, 53), small_font)
            draw_text("Espaço ou ↑ também funcionam", 338, (119, 105, 79), tiny_font)
        else:
            draw_text("FIM DE JOGO", 263, (48, 85, 75), title_font)
            draw_text(f"PONTOS  {game['score']}     RECORDE  {best}", 307, (89, 76, 53), small_font)
            draw_text("Toque, clique ou pressione R para voltar", 338, (119, 105, 79), tiny_font)
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
