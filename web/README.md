# Versão para navegador

O jogo continua escrito em Python (`main.py`). Pygbag empacota a versão Pygame para WebAssembly, permitindo executá-la no navegador. As imagens ficam em `web/assets/`: personagem e conectores RJ45. A versão desktop com Tkinter continua na raiz do projeto.

## Preparar

Instale Python 3.11 ou mais recente e, no terminal, instale o Pygbag:

```bash
python -m pip install pygbag
```

## Executar no navegador localmente

Na pasta raiz do projeto, execute:

```bash
python -m pygbag web
```

Depois abra [http://localhost:8000](http://localhost:8000). A primeira abertura pode demorar enquanto o navegador baixa o runtime.

## Gerar os arquivos para publicação

Na pasta raiz, execute:

```bash
python -m pygbag --build web
```

Os arquivos estáticos gerados ficam em `web/build/web/`. Publique o conteúdo dessa pasta em um host de sites estáticos, como GitHub Pages. Cada pessoa terá seu próprio recorde no armazenamento local do navegador.

Controles: **Espaço**, **↑**, **W**, toque ou clique para voar. **R** reinicia.
