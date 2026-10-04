---
title: Cifrador
emoji: 🎸
colorFrom: blue
colorTo: indigo
sdk: gradio
sdk_version: 6.29.1
python_version: "3.11"
app_file: app.py
pinned: false
---

# Cifrador

Envie o áudio de uma música, cole a letra e baixe a **cifra em PDF**, com o tom, as modulações e os
acordes encaixados em cima da letra, o logotipo, o artista, o álbum e os desenhos dos acordes de violão.

## Como funciona

1. **Harmonia** (`cifrador/harmonia.py`): detecta o tom por trecho (e as modulações) e os acordes
   (maiores, menores, com sétima e, no nível 3, sus, nonas, diminutos).
2. **Transcrição** (`cifrador/transcricao.py`): o Whisper ouve a música e marca o tempo de cada palavra.
3. **Letra** (`cifrador/letra.py`): troca o texto transcrito (que erra palavras) pela letra certa que você colou,
   verso por verso, respeitando repetições do refrão.
4. **Cifra** (`cifrador/cifra.py`): coloca cada acorde na palavra onde ele troca.
5. **PDF** (`cifrador/pdf.py`): gera o PDF com logotipo e diagramas de acordes.

## Rodar no computador

```
pip install -r requirements.txt gradio
python app.py
```

## Testes

```
pip install pytest
python -m pytest -q
```

Os testes usam um áudio sintético e uma transcrição falsa, então não precisam baixar o Whisper.

## Logotipo padrão

Coloque o arquivo do logotipo em `assets/logo.png`. Ele é usado quando nenhum logotipo é enviado na tela.

## Rodar no Google Colab (gratuito, com placa de vídeo)

Abra um caderno novo em colab.research.google.com, ligue a GPU (Ambiente de execução > Alterar tipo > T4 GPU)
e rode duas caixas.

Caixa 1 (instalar e baixar o projeto; troque SEU_USUARIO pelo seu usuário do GitHub):

```
!pip install -q stable-ts reportlab gradio
!git clone https://github.com/SEU_USUARIO/cifrador.git
```

Caixa 2 (abrir o app; escolha usuário e senha para proteger o link):

```
import os
%cd /content/cifrador
!git pull
os.environ['APP_SHARE'] = '1'
os.environ['APP_USUARIO'] = 'josimarth'
os.environ['APP_SENHA'] = 'TROQUE-ESTA-SENHA'
!python app.py
```

A caixa 2 mostra um endereço terminado em `gradio.live`. Abra, entre com o usuário e a senha e use.
O link vale enquanto a caixa estiver rodando. Para uma nova sessão, rode as duas caixas de novo.

## Publicar no Hugging Face Spaces (opcional, exige plano pago)

Spaces com Gradio exigem plano pago no Hugging Face. Se um dia quiser usar: crie o Space, crie um token de escrita,
e no GitHub (Settings > Secrets and variables > Actions) crie o segredo `HF_TOKEN` e as variáveis `HF_USER` e
`HF_SPACE`. A cada mesclagem na `main`, o GitHub Actions envia o projeto para o Space.

## Limites conhecidos

- No Colab com GPU o app usa o Whisper `medium` (rápido). Sem GPU usa o `small` (alguns minutos por música).
  Dá para forçar outro com a variável `WHISPER_MODEL`.
- Os arquivos do Colab somem ao fechar a sessão: o logotipo padrão deve ficar em `assets/logo.png` no repositório.
- Acordes são sugestões automáticas: confira de ouvido.
