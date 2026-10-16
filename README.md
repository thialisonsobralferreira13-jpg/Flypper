# Flappy Bird em Python

Jogo feito do zero com Python, Tkinter e SQLite. Não precisa instalar pacotes extras. O recorde fica salvo no arquivo `flappy_bird.db`, criado na pasta do jogo, e continua disponível nas próximas partidas.

## Como jogar

No terminal, dentro desta pasta, execute:

```bash
python main.py
```

Pressione **Espaço**, **↑** ou clique para começar e fazer o pássaro voar. Passe entre os canos para marcar pontos. Ao perder, use as mesmas teclas ou clique para recomeçar; **R** também reinicia.

## Jogar no navegador

Há uma versão web em Python na pasta `web/`. Ela usa Pygame e Pygbag para executar Python no navegador. Consulte [web/README.md](web/README.md) para instalar e iniciar o servidor local ou gerar a versão para publicar.

Na versão desktop, o recorde fica em `flappy_bird.db` (SQLite). Na versão web, ele fica no armazenamento local do navegador; por isso, o recorde é mantido nesse navegador e dispositivo.
