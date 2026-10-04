# Cifrador: orientações para o Claude Code

## O que é
App em Python (Gradio) que recebe áudio + letra e gera a cifra em PDF (tom, modulações, acordes sobre a letra,
logotipo, artista, álbum e diagramas de acordes de violão). Roda no Google Colab (gratuito, com GPU) a partir do repositório do GitHub; o Hugging Face Spaces com Gradio exige plano pago.

## Quem usa
O dono do projeto é músico (projeto "A Mensagem"), não é programador, trabalha por navegador e não pode instalar
programas no PC. Explique em português, com passos curtos, um de cada vez, e deixe comandos em blocos de código
para copiar e colar.

## Estrutura
- `app.py`: tela Gradio.
- `cifrador/harmonia.py`: tom, modulações e acordes (cromagrama + Viterbi).
- `cifrador/transcricao.py`: Whisper (stable-ts). Único módulo que precisa baixar modelo da internet.
- `cifrador/letra.py`: troca o texto transcrito pela letra certa e reencaixa os tempos.
- `cifrador/cifra.py`: monta o texto da cifra (acordes em cima da letra).
- `cifrador/pdf.py`: PDF com reportlab.
- `cifrador/pipeline.py`: junta tudo; `transcrever_fn` pode ser trocado nos testes.
- `tests/`: testes com áudio sintético e transcrição falsa.

## Como trabalhar
- Rode `python -m pytest -q` antes de abrir um pull request. Todo código novo precisa de teste.
- Sempre trabalhe em uma branch própria e abra um pull request; quem mescla é o dono, no GitHub.
- Nunca coloque senhas ou tokens no código. O token do Hugging Face fica só nos segredos do GitHub.
- A interface e as mensagens são em português do Brasil.
- Se o ambiente não conseguir baixar o modelo do Whisper, teste tudo com a transcrição falsa e avise o dono.

## Ideias de melhoria
- Whisper mais rápido na CPU (faster-whisper).
- Guardar um histórico de músicas e permitir regerar o PDF depois.
- Tablatura/dedilhado e acordes mais elaborados no desenho do violão.
- Comparar o resultado com cifras que o dono já tem, para calibrar a detecção.
